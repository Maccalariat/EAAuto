from lxml import etree
from collections import namedtuple


class ErwinXMI:
    def __init__(self, log_message):

        self.log_message = log_message
        self.erwin_package_map = {}
        self.erwin_class_map = {}
        self.erwin_relationship_map = {}
        self.erwin_generalization_map = {}

        self.Connector = namedtuple('Connector', ['GUID', 'name',
                                                  'end_1_id', 'end_1_name', 'end_1_mult', 'end_1_type',
                                                  'end_1_type_idref',
                                                  'end_2_id', 'end_2_name', 'end_2_mult', 'end_2_type',
                                                  'end_2_type_idref'])
        self.Generalization = namedtuple("Generalization", ['GUID', 'xmi_id', 'name',
                                                            'child_type', 'child_idref',
                                                            'parent_type', 'parent_idref'])

        self.xpath_package = "/XMI/XMI.content/UML:Model/UML:Namespace.ownedElement/UML:Package"
        self.xpath_class = "/XMI/XMI.content/UML:Model/UML:Namespace.ownedElement/UML:Class"
        self.xpath_model = \
            "/XMI/XMI.content/Model_Management.Model/Foundation.Core.Namespace.ownedElement/Model_Management.Package"
        self.xpath_relationship = "/XMI/XMI.content/UML:Model/UML:Namespace.ownedElement/UML:Association"
        self.xpath_generalization = "/XMI/XMI.content/UML:Model/UML:Namespace.ownedElement/UML:Generalization"
        self.xpath_diagram = "/XMI/XMI.content/UML:Diagram"

    def build_erwin_map(self, filename):
        """build dictionaries of ERWIN elements, packages and relationships:
            key = ERWIN GUID
            value = name
            """
        doc = etree.parse(filename)
        # collect and process all packages
        rpath = doc.xpath(self.xpath_package, namespaces={'UML': "omg.org/UML1.3"})
        for elem in rpath:
            self.erwin_package_map[elem.attrib['name']] = elem.attrib['xmi.uuid']

        # collect and process all class - aka Entities
        rpath = doc.xpath(self.xpath_class, namespaces={'UML': "omg.org/UML1.3"})
        for elem in rpath:
            self.erwin_class_map[elem.attrib['name']] = elem.attrib['xmi.uuid']

        # collect and process all relationships
        rpath = doc.xpath(self.xpath_relationship, namespaces={'UML': "omg.org/UML1.3"})
        # a rather rash assumption is made that all associations have two ends with the same structure and a unique name
        for elem in rpath:
            r = self.Connector(GUID=elem.attrib['xmi.uuid'],
                               name=elem.attrib['name'],
                               end_1_id=(elem[0][0]).attrib['xmi.id'],
                               end_1_name=(elem[0][0]).attrib['name'],
                               end_1_mult=(elem[0][0][0]).text,
                               end_1_type=(elem[0][0][1][0]).tag,
                               end_1_type_idref=(elem[0][0][1][0]).attrib['xmi.idref'],
                               end_2_id=(elem[0][1]).attrib['xmi.id'],
                               end_2_name=(elem[0][1]).attrib['name'],
                               end_2_mult=(elem[0][1][0]).text,
                               end_2_type=(elem[0][1][1][0]).tag,
                               end_2_type_idref=(elem[0][1][1][0]).attrib['xmi.idref'])
            self.erwin_relationship_map[elem.attrib['xmi.uuid']] = r

        # collect Generalization relationships
        rpath = doc.xpath(self.xpath_generalization, namespaces={'UML': "omg.org/UML1.3"})
        for elem in rpath:
            g = self.Generalization(GUID=elem.attrib['xmi.uuid'],
                                    xmi_id=elem.attrib['xmi.id'],
                                    name=elem.attrib['name'],
                                    child_type=(elem[0][0]).tag,
                                    child_idref=(elem[0][0]).attrib['xmi.idref'],
                                    parent_type=(elem[1][0]).tag,
                                    parent_idref=(elem[1][0]).attrib['xmi.idref'])
            self.erwin_generalization_map[elem.attrib['xmi.uuid']] = g

        self.log_message("finished erwin xmi mapping")
        return self.erwin_package_map, self.erwin_class_map, self.erwin_relationship_map, self.erwin_generalization_map
