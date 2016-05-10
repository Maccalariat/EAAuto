import xlrd
from collections import namedtuple

__author__ = 'M020240'
"""
This class represents an Application Inventory excel extract

Attributes:

"""


class ApplicationInventory:

    def __init__(self, spreadsheet_name, logWidget ):
        """
        :param spreadsheet_name: the input spreadsheet
        :param logWidget: A function reference to the logging widget
        :return: no return
        """
        self.logWidget = logWidget
        self.filename = spreadsheet_name

        self.application = namedtuple('application', ['AIID', 'Name', 'Status'])
        self.workbook = xlrd.open_workbook(self.filename)
        self.worksheet = self.workbook.sheet_by_index(0)



    def close_spreadsheet(self):
        """
        Close the spreadsheet file.
        We rely on the garbage collection of COM through XLFile to close the excel instance
        :return:
        """
        del self.workbook

    def build_application_map(self):
        application_map = {}

        rows = [ self.worksheet.row_values(idx, 0, 10) for idx in range(self.worksheet.nrows)]
        application_map= { row[0]: (row[0], row[1], row[8]) for row in rows }

        return application_map