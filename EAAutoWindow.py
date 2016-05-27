from tkinter import Frame, Menu, SUNKEN, NORMAL, BOTH, DISABLED, Text
import sys
import pickle

from tkinter.filedialog import askopenfilename, askdirectory

from tkinter.scrolledtext import ScrolledText

from EAP import EADatabase
from XLS import ApplicationInventory, ECDMSpreadsheet
from EAAuto_xml import ErwinXMI
from Utilities import BiGUID

__author__ = 'M020240'


class EAAutoWindow:
    eaDB = None
    fileName = None

    def __init__(self, master):

        self.master = master
        # declare instance variables
        self.log = None  # the logging widget
        self.eaDB = None
        self.spreadsheet = None
        self.application_inventory_map_excel = {}
        self.application_inventory_map_eap = {}
        self.ea_ecdm_element_map = {}
        self.ea_ecdm_relationship_map = {}
        self.erwin_package_map = {}
        self.erwin_class_map = {}
        self.erwin_relationship_map = {}
        self.erwin_generalization_map = {}
        self.log_widget = None
        self.ecdm_Sparx_to_ERWIN_GUID = {}
        self.ecdm_ERWIN_to_Sparx_GUID = {}
        # end instance variables

        self.initUI(master)
        self.log_message('open for business')
        self.log_message("Don't forget to open and close the database yourself!")

    def exit_action(self):
        self.master.destroy()

    def reconcile_applications(self):
        """
        compare the application inventory spreadsheet to the EA database
        for now, produce a report of differences
        :return:

        """
        if self.eaDB is None:
            self.log_message("you need to open a database")
            return
        self.eaDB.find_package('Application Inventory')
        self.application_inventory_map_eap = self.eaDB.build_application_map()

        ai_file_name = self.open_excel_ai()
        self.log_message("AI excel file = " + ai_file_name)
        if ai_file_name is None:
            self.log_message("no eap file selected")
            return

        self.log_message("AI File = " + ai_file_name)
        spreadsheet = ApplicationInventory.ApplicationInventory(
            ai_file_name, self.log_message)
        self.application_inventory_map_excel = spreadsheet.build_application_map()
        spreadsheet.close_spreadsheet()
        self.log_message("Closing AI Spreadsheet")
        del spreadsheet

        self.compare_ai_to_sparx()

    def update_AHC(self):
        """
        read a spreadsheet with input from Application Health Check and Cloud affinity
        push into tagged values for the applications
        :return:

        """
        # first open the database
        eap_file_name = self.open_eap()

        if eap_file_name is None:
            self.log_message("no eap file selected")
            return
        self.log_message("EAP Filename = " + eap_file_name)

        self.eaDB = EADatabase.EAdatabase(eap_file_name, self.log_message)
        self.eaDB.find_package('Application Inventory')

        ai_file_name = self.open_excel_ai()
        self.log_message("AI excel file = " + ai_file_name)
        if ai_file_name is None:
            self.log_message("no excel file selected")
            return

        self.log_message("AI File = " + ai_file_name)
        spreadsheet = ApplicationInventory.ApplicationInventory(
            ai_file_name, self.log_message)
        self.application_inventory_map_excel = spreadsheet.build_application_map()
        spreadsheet.close_spreadsheet()
        self.log_message("Closing AI Spreadsheet")
        del spreadsheet

        self.compare_ahc_to_sparx()

        self.eaDB.stop_db()

    def extract_ECDM_guids(self):
        """
        parse the ECDM canonical directory dumping all elements and relationships (between ERWIN elements)
        to get the baseline Sparx GUIDS.
        This is pushed out in an Excel file (as a convencience) with two tabs:
        tab 1 is the element list
        tab 2 is the Relationship list
        :return:
        """
        self.log_message("starting ECDM guid dump")

        # if self.eaDB is None:
        #    self.log_message("no eap file selected")
        #    return

        erwin_mapper = ErwinXMI.ErwinXMI(self.log_message)
        options = {'defaultextension': '.xml',
                   'filetypes': (('xml', '.xml'), ('xmi', 'xmi')),
                   'initialdir': 'C:\\HOME\\var\\projects\\python\\EAAUTO',
                   'initialfile': 'erwin_export.EAAuto_xml',
                   'parent': self.master,
                   'title': 'Open ERWIN xmi export'}
        filename = askopenfilename(**options)

        self.eaDB.find_package('ECDM Canonical')
        (self.ea_ecdm_element_map, self.ea_ecdm_relationship_map) =  self.eaDB.build_ecdm_maps()

        directory = askdirectory(parent = self.master,
                                 initialdir='C:\\HOME\\var\\projects\\python\\EAAUTO',
                                 title = 'Sparx pickle of ECDM')
        pickle.dump(self.ea_ecdm_element_map, open(directory + '/ea_ecdm_element_map.p', "wb"))
        pickle.dump(self.ea_ecdm_relationship_map, open(directory + '/ea_ecdm_relationship_map.p', "wb"))
        exporter = ECDMSpreadsheet.ECDMSpreadsheet("c:/HOME/var/projects/Python/EAAuto/ecdmmap.xls", self.log_message)
        exporter.write_ecdm_map(self.ea_ecdm_element_map, self.ea_ecdm_relationship_map, self.log_message)

        if filename:
            (self.erwin_package_map, self.erwin_class_map, self.erwin_relationship_map, self.erwin_generalization_map) =\
                erwin_mapper.build_erwin_map(filename)

        else:
            self.log_message("error getting the ERWIN xmi export")
            return
        guid_mapper = BiGUID.BiGUID()
        reverse_ea_ecdm_element_map = {v: k for k, v in self.ea_ecdm_element_map.items()}
        # erwin GUID is left-hand, Sparx GUID is right-hand
        """
        ea_ecdm_element_map is GUID: (name, type)
        erwin_class_map is name: GUID
        """
        for erwin_name, erwin_guid in self.erwin_class_map.items():
            if erwin_name in reverse_ea_ecdm_element_map:
                guid_mapper.add(self.erwin_class_map[erwin_name], reverse_ea_ecdm_element_map[erwin_name])
            else:
                self.log_message("missing erwin element in sparx" + erwin_name)


        exporter.close_spreadsheet()

    def reconcile_ecdm(self):
        """
        compare the ecdm from xmi and sparx(mapped in extract_ECDM_guids)
         to come up with a 'diff' report
        :return:
        """
        if not (len(self.ea_ecdm_element_map) and len(self.ea_ecdm_relationship_map) and len(self.erwin_generalization_map) and
            len(self.erwin_relationship_map) and len(self.erwin_class_map) and len(self.erwin_package_map)):
            self.log_message("don't have all the maps to do a reconciliation")
            return

        # the order of add/change/delete is important.
        # relationships must come after entities

    def open_eap(self):
        # define options for opening the EAP file
        filename = None
        options = {'defaultextension': '.eap',
                   'filetypes': (('eap', '.eap'),),
                   'initialdir': 'C:\\HOME\\var\\projects\\python\EAAuto',
                   'initialfile': 'myfile.eap',
                   'parent': self.master,
                   'title': 'Open Sparx database'}
        filename = askopenfilename(**options)
        if filename:
            self.eaDB = EADatabase.EAdatabase(filename, self.log_message)
        else:
            self.log_message("Problem with opening the Sparx Database")

    def close_eap(self):
        self.eaDB.stop_db()

    def open_excel_ai(self):
        filename = None
        options = {'defaultextension': '.xlsx',
                   'filetypes': (('xls', '.xls'), ('xlsx', '.xlsx')),
                   'initialdir': 'C:\\HOME\\var\\projects\\python',
                   'initialfile': 'myfile.xlsx',
                   'parent': self.master,
                   'title': 'Open excel Application Inventory file'}
        filename = askopenfilename(**options)
        return filename

    def log_message(self, log_message):
        numlines = self.log_widget.index('end - 1 line').split('.')[0]
        self.log_widget.config(state=NORMAL)
        if numlines == 24:
            self.log_widget.delete(1.0, 2.0)
        if self.log_widget.index('end-1c') != '1.0':
            self.log_widget.insert('end', '\n')
        self.log_widget.insert('end', log_message)
        self.log_widget.config(state=DISABLED)

    def initUI(self, master):
        frame = Frame(master, bd=2, relief=SUNKEN)
        # frame.pack(fill=BOTH, expand=1)

        self.log = Text(frame)
        self.log.config(state=DISABLED)

        self.master.title("EAP Automation tool")
        menubar = Menu(self.master)
        self.master.config(menu=menubar)

        fileMenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=fileMenu)
        fileMenu.add_command(label="Open EAP", command=self.open_eap)
        fileMenu.add_command(label="Close EAP", command=self.close_eap)
        fileMenu.add_command(label="Exit", command=sys.exit)

        processmenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Process", menu=processmenu)
        processmenu.add_command(label="reconcile Applications",
                                command=self.reconcile_applications)
        processmenu.add_command(label="reconcile ERWIN", command=self.reconcile_ecdm)
        processmenu.add_command(label="update AHC",
                                command=self.update_AHC)

        extract_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Extract", menu=extract_menu)
        extract_menu.add_command(label="Sparx ECDM GUIDs",
                                 command=self.extract_ECDM_guids)

        # the log widget
        self.log_widget = ScrolledText(master, bg='light cyan')
        self.log_widget.config(state=DISABLED)
        self.log_widget.pack(padx=10, pady=10, fill=BOTH, expand=True)

    def compare_ahc_to_sparx(self):
        """
        with the provided EA Database and Spreadsheet run through the application inventory secion
        of the database and updtate the Application Healthcheck tag and cloud tags.
        If the tags do not exist, then create them
        """
        self.log_message("nothing happening here, moving along")
        return

    def compare_ai_to_sparx(self):
        """
        wth the provided EA database and Spreadsheet, run through the
        Application Inventory section of the EA Database and display a 'diff' report
        TODO: this diff is currently just a dump to the log window. Provide better formatting and also excel output
        :type self: object
        """

        self.log_message("processing AI against Sparx")

        if not self.application_inventory_map_excel:
            self.log_message("the excel table is empty - nothing to reconcile")
            return

        if not self.application_inventory_map_eap:
            self.log_message("the Sparx table is empty - nothing to reconcile")
            return

        self.set_excel = set(self.application_inventory_map_excel.keys())
        self.set_eap = set(self.application_inventory_map_eap.keys())
        self.set_intersect = self.set_excel.intersection(self.set_eap)

        self.log_message("comparing Excel to Sparx")
        self.log_message("========================")
        # now iterate through the excel file and compare to the Sparx database
        for excel_key in self.set_excel:
            if excel_key not in self.set_eap:
                excel_app_record = self.application_inventory_map_excel[
                    excel_key]
                if excel_app_record[2] == 'Production':
                    self.log_message("    ID= " + excel_key + " not in EA")

        self.log_message("comparing Sparx to Excel")
        self.log_message("========================")
        # now iterate through the excel file and compare to the Sparx database
        for sparx_key in self.set_eap:
            if sparx_key not in self.set_excel:
                self.log_message("   ID= " + sparx_key + " not in AI")

        self.log_message("completed processing")
        self.log_message("====================")

