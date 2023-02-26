"""
Deluge Client is packaged with QuestVRAutoInstaller

this file sets the paths for the Deluge daemon and required files to be loaded and run

"""

import os
import platform

DAEMON_PORT = 58846

# *Nix and MacOS not yet implemented
if platform.system() != "Windows":
    raise OSError("Linux and OSX version for torrenting not yet implemented")

# DELUGE_PATH = os.path.join(os.getenv("PROGRAMFILES"), "Deluge")
DELUGE_PATH = os.path.join("deluge", "bin", "version-211", "win64")
DELUGE_DAEMON_PATH = os.path.join(DELUGE_PATH, "deluged.exe")
# Deluge Settings path which contains the authentication users and deluged error logs
APPDATA_PATH = os.getenv("APPDATA")
if not APPDATA_PATH:
    raise EnvironmentError("Unable to locate APPDATA enviroment for deluge path")
DELUGE_DATA_PATH = os.path.join(APPDATA_PATH, "deluge")
DELUGED_LOG_PATH = os.path.join(DELUGE_DATA_PATH, "deluged.log")
AUTH_FILE_PATH = os.path.join(DELUGE_DATA_PATH, "auth")
