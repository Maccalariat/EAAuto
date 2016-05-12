import comtypes.client
import os
import psutil
import signal
from xml.dom import minidom
import re
import win32com.client


class EAdatabase:
    """
    A wrapper class for the Sparx EA Database interface.
    In Python we need to do this through lower-level com interfacing.
    This class has all the method calls of the EA object
    """

    # class variables
    ea_current_instance_pid = []  # pid list of current int
    ea_new_instance_pid = []  # pid list of instances created by this class
    ea_application = None
    ea_repository = None
    exp = None

    def __init__(self, file_name, log_function):
        """
        Constructor
        :type file_name: object
        :param file_name: the name of the EAP file
        :param log_function: the logging function
        """
        self.logWidget = log_function
        self.logWidget("in EADB")
        self.exp = re.compile('\(\w*-\w*\)\Z')
        self.ecdm_element_map = {}
        self.ecdm_relationship_map = {}
        self.start_db(file_name, log_function)

    def start_db(self, database_name, log_function):
        self.get_pid_list()

        # self.ea_application = comtypes.client.CreateObject("EA.App")
        self.ea_application = win32com.client.Dispatch("EA.App")

        self.get_pid_list()
        self.ea_repository = self.ea_application.Repository
        self.ea_repository.OpenFile(database_name)
        self.ea_application.Visible = 0
        log_function("opened Database", )

    def stop_db(self):
        print("stopping database")
        self.ea_repository.CloseFile()
        self.ea_application = None
        del self.ea_application

        # kill the new instance(s) - there should be onlyl one!
        for pid in self.ea_new_instance_pid:
            self.logWidget("killing " + str(pid))
            os.kill(pid, signal.SIGTERM)
        self.logWidget("database stopped")

    def get_pid_list(self):
        self.ea_new_instance_pid.clear()
        for proc in psutil.process_iter():
            pinfo = proc.as_dict(attrs=['pid', 'name'])
            # print (pinfo)
            if pinfo['name'] == "EA.exe":
                print("EA PID -> ", proc._pid)
                if self.ea_current_instance_pid.__contains__(proc._pid):
                    next
                else:
                    self.ea_current_instance_pid.append(proc._pid)
                    self.ea_new_instance_pid.append(proc._pid)

    def get_ecdm_relationships(self, map_element):
        element = self.ea_repository.getElementByGUID(map_element)
        try:
            connector_set = element.Connectors
            for connector in connector_set:
                # we are only interested in connections internal to ECDM (both client and supplier are in the ecdm_map
             client = self.ea_repository.getElementByID(connector.ClientID)
             supplier = self.ea_repository.getElementByID(connector.SupplierID)
             if client.ElementGUID in self.ecdm_element_map and supplier.ElementGUID in self.ecdm_element_map:
                 self.ecdm_relationship_map[connector.ConnectorGUID] = (connector.name, connector.ClientID,
                                                                       connector.SupplierID, client.ElementGUID,
                                                                       supplier.ElementGUID)
        except:
            pass


    def strip_name(self, name):
        """
        remove the final '(aiid)' postfix from a supplied name
        Note that this must be at the end of the string
        :param name:
        :return: strippedName
        """
        strippedName = name.replace(r'\([\s\S]\)$', '')
        return strippedName

    def strip_aiid(self, name):
        """
        extract the final '(aiid)' from the the supplied name
        :param name:
        :return: aiid
        """
        aiid = self.exp.search(name)
        if aiid:
            id = aiid.group(0).replace('(', '')
            id = id.replace(')', '')
            return id
        else:
            return ''

    def dump_element(self, theElement):
        # self.log_widget.log_trigger.emit('    element' + theElement.Name)
        for element in theElement.Elements:
            self.dump_element(element)

    def dump_package(self, theModel):
        self.logWidget.log_trigger.emit('package = ' + theModel.Name)
        for element in theModel.Elements:
            self.dump_element(element)

        for pkg in theModel.Packages:
            self.dump_package(pkg)

    def dump_contents(self):

        self.find_package('Application Inventory')
        # for currentModel in self.__eaRep.Models:
        #    self.dump_package(currentModel)

    def find_package(self, package_name):
        # querystring = "SELECT name, ea_guid from t_object WHERE t_object.object_Type = \'Package\' AND name=\'Application Inventory\'"
        querystring = r"SELECT name, ea_guid FROM t_object WHERE t_object.object_Type = 'Package' AND name = '%s'" % package_name

        result = self.ea_repository.SQLQuery(querystring)
        # self.logWidget("query result: " + result)
        doc = minidom.parseString(result)
        item = doc.getElementsByTagName("ea_guid")[0]
        self.logWidget("child data" + item.firstChild.data)
        package = self.ea_repository.GetpackageByGuid(item.firstChild.data)
        self.logWidget("package = " + package.Name)
        return package

    def build_ecdm_maps(self):
        """
        parse the database building two maps:
            * ECDM elements (packages and elements)
            * Relationships between ECDM elements (packages and elements)
        This is specific to a function regarding maintenance of ECDM

        :returns tuple (ecdm_element_map, ecdm_relationship_map)
        """
        self.logWidget("in build_ecdm_map")
        self.ecdm_element_map = {}
        self.ecdm_relationship_map = {}
        ecdm_root = self.find_package('ECDM Canonical')

        # local functions to do the recursion
        def dump_element(item):
            """
            A recursive routine to parse the database tree from a given package
            this calls dump_element to dump any elements in the current package
            :param item: the item to be dumped - may be package or element
            """

            if item.ObjectType == 5: # model
                self.ecdm_element_map[item.packageGUID] = (item.Name, 5)
            elif item.ObjectType == 3: # element
                self.ecdm_element_map[item.ElementGUID] = (item.Name, 3)
            elif item.ObjectType == 8: # diagram
                self.ecdm_element_map[item.DiagramGUID] = (item.Name, 8)
            elif item.ObjectType == 4:  # entity
                self.ecdm_element_map[item.ElementGUID] = (item.Name, 4)
            else:
                self.ecdm_element_map[item.ElementGUID] = (item.Name, 0)

            # We are not sure what the element is, so not all elements have each type of contents
            try:
                for element in item.Elements:
                    dump_element(element)
            except:
                pass
            try:
                for diagram in item.Diagrams:
                    dump_element(diagram)
            except:
                pass
            try:
                for package in item.Packages:
                    dump_element(package)
            except:
                pass


        def dump_relationships():
            """
            Process the ecdm_element_map.
            Check each element's relationships and create an entry in the ecdm_relationship_map only if
            the relationship is between elements in the ecdm_element_map
            :return:
            """
            for element in self.ecdm_element_map:
                self.get_ecdm_relationships(element)

        # drive the recursion
        dump_element(ecdm_root)
        dump_relationships()
        print("finished ecdm map generation")

        return self.ecdm_element_map, self.ecdm_relationship_map

    def build_application_map(self):
        """
        parse the database building  a map of applications.
        This is specific to a function regarding Application Inventory applications

        """
        self.logWidget("in build_application_map")
        applicationMap = {}
        # find the package for the Application Inventory
        aip = self.find_package('Application Inventory')

        def dump_element(element):
            """
            A recursive routine to dump out elements
            Note that a structure of EA is that an element cannot have a package under it
            :param element: the EA database element
            """
            # self.logger.append(" build_application_map element" + element.Name)
            # self.log_widget.log_trigger.emit("    element " + element.Name)
            strippedName = self.strip_name(element.Name)
            aiid = self.strip_aiid(element.Name)
            applicationMap[aiid] = (strippedName, element.Notes, aiid)

        def dump_package(AIPackage):
            """
            A recursive routine to parse the database tree from a given package
            this calls dump_element to dump any elements in the current package
            :param AIPackage: The EA Database package
            """
            for element in AIPackage.Elements:
                dump_element(element)

            for pkg in AIPackage.Packages:
                dump_package(pkg)

        dump_package(aip)
        """
        pattern using a map
        for key in myRDP:
            name = myNames.get(key, None)
            if name:
                print key, name
        """
        return applicationMap
