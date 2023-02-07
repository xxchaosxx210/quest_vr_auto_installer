import os

DAEMON_PORT = 58846

DELUGE_PATH = os.path.join(os.getenv("PROGRAMFILES"), "Deluge")
DELUGE_DAEMON_PATH = os.path.join(DELUGE_PATH, "deluged.exe")
DELUGE_DATA_PATH = os.path.join(os.getenv("APPDATA"), "deluge")
DELUGED_LOG_PATH = os.path.join(DELUGE_DATA_PATH, "deluged.log")
AUTH_FILE_PATH = os.path.join(DELUGE_DATA_PATH, "auth")
