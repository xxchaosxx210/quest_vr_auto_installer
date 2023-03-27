import os
import platform
import logging

from . import adb_interface

__OS = platform.system()
MODULE_PATH = os.path.dirname(__file__)
if __OS == "Windows":
    BIN_PATH = os.path.join(MODULE_PATH, "win64")
    adb_interface.ADB_DEFAULT_PATH = os.path.join(BIN_PATH, "adb.exe")
else:
    raise OSError(f"This library is not yet implemented for {__OS}")
