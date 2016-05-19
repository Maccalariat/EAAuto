from lxml import etree


class ErwinXMI:
    def __init__(self, log_message):

        self.log_message = log_message
        self.erwin_package_map = {}
        self.erwin_element_map = {}
        self.erwin_relationship_map = {}

        self.xpath_class = "/XMI/XMI.content/Model_Management.Model/Foundation.Core.Namespace.ownedElement/Foundation.Core.Class"
        self.xpath_model = "/XMI/XMI.content/Model_Management.Model/Foundation.Core.Namespace.ownedElement/Model_Management.Package"
        self.xpath_relationship = "/XMI/XMI.content/Model_Management.Model/Foundation.Core.Namespace.ownedElement/Foundation.Core.Association"
        self.xpath_generalization = "/XMI/XMI.content/Model_Management.Model/Foundation.Core.Namespace.ownedElement/Foundation.Core.Generalization"
        self.xpath_diagram = ""

    def build_erwin_map(self, filename):
        """build dictionaries of ERWIN elements, packages and relationships:
            key = ERWIN GUID
            value = name
            """
        self.log_message("starting erwin xmi mapping")
        doc = etree.parse(filename)
        r = doc.getroot()
        # collect and process all Model - aka packages
        rpath = doc.xpath(self.xpath_model)
        for elem in rpath:
            e = doc.xpath('./@name')
            self.erwin_package_map[elem.attrib['name']] = elem.attrib['xmi.uuid']

        # collect and process all class - aka Entities
        rpath = doc.xpath(self.xpath_class)
        for elem in rpath:
            self.erwin_element_map[elem.attrib['name']] = elem.attrib['xmi.uuid']

        self.log_message("finished erwin xmi mapping")
        return self.erwin_package_map, self.erwin_element_map
