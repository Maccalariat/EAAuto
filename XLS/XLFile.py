__author__ = 'M020240'
"""
Testbed for EA automation
"""
import xlrd


class SpreadSheet:

    def __init__(self, spreadsheet_name, log_widget):
        self.log_widget = log_widget
        self.__filename = spreadsheet_name
        self.log_widget('xlrd filename ' + spreadsheet_name)
        self.__book = xlrd.open_workbook(self.__filename)

    def closeSpreadSheet(self):
        del self.__book

    def dumpRows(self, sheetNumber, rowCount):
        self.__sheet = self.__book.sheet_by_index(sheetNumber)
        self.log_widget(' , '.join([str(i) for i in self.__sheet.row(0)]))
        self.log_widget(' , '.join([str (1) for i in self.__sheet.row(1)]))

    def row(self, sheetNumber, row):
        """

        :type row: object
        """
        return self.__sheet.row(row)