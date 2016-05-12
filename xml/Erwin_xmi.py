from lxml import etree
from tkinter.filedialog import askopenfilename

class ERWIN_xmi:

    def __init__(self, log_message):

        self.log_message = log_message
        self.erwin_package_map = {}
        self.erwin_element_map = {}
        self.erwin_relationship_map = {}
        self.filename = None
        self.xpath_class = "/XMI/XMI.content/Model_Management.Model/Foundation.Core.Namespace.ownedElement/Model_Management.Package/Foundation.Core.Namespace.ownedElement/Foundation.Core.Class"
        self.xpath_model = "/XMI/XMI.content/Model_Management.Model/Foundation.Core.Namespace.ownedElement/Model_Management.Package"
        self.xpath_relationship = ""
        self.xpath_diagram = ""

        options = {'defaultextension': '.xml',
                   'filetypes': (('xml', '.sml'), ('xmi', 'xmi')),
                   'initialdir': 'C:\\HOME\\var\\projects\\python\\EAAUTO',
                   'initialfile': 'erwin_export.xml',
                   'parent': self.master,
                   'title': 'Open ERWIN xmi export'}
        filename = askopenfilename(**options)
        if filename:
            self.build_erwin_map()
        else:
            self.log_message("error getting the ERWIN xmi export")
            return


    def build_erwin_map(self):
        """build dictionaries of ERWIN elements, packages and relationships:
            key = ERWIN GUID
            value = name
            """
        self.log_message("starting erwin xmi mapping")
        doc = etree.parse(self.filename)
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
