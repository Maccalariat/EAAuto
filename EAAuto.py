from tkinter import Tk
from EAAutoWindow import EAAutoWindow

"""
this programme needs the following python modules:
psutil
xlrd
comtypes
"""


def runner():
    root = Tk()
    root.title("EA Automation Tool")
    EAAutoWindow(root)
    root.mainloop()

if __name__ == '__main__':
    runner()
