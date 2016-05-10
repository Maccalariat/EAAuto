import xlrd
from collections import namedtuple

__author__ = 'M020240'
"""
This class represents an export of the ECDM elements and relationships

Attributes:

"""


class ECDMSpreadsheet:

    def __init__(self, spreadsheet_name, log_widget):
        """
        :param spreadsheet_name: the input spreadsheet
        :param log_widget: A function reference to the logging widget
        :return: no return
        """
        self.log_widget = log_widget
        self.filename = spreadsheet_name

        self.element = namedtuple('element', ['Name', 'GUID'])
        self.workbook = xlrd.open_workbook(self.filename)
        self.worksheet = self.workbook.sheet_by_index(0)



    def close_spreadsheet(self):
        """
        Close the spreadsheet file.
        We rely on the garbage collection of COM through XLFile to close the excel instance
        :return:
        """
        del self.workbook

    def write_entity_map(self):

        entity_map = {}

        rows = [ self.worksheet.row_values(idx, 0, 10) for idx in range(self.worksheet.nrows)]
        entity_map= { row[0]: (row[0], row[1], row[8]) for row in rows }

        return

    def write_relationship_map(self):
        return