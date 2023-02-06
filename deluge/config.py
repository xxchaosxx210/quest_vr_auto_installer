import os

DAEMON_PORT = 58846

DELUGE_PATH = os.path.join(os.environ["PROGRAMFILES"], "Deluge")
DELUGE_DAEMON_PATH = os.path.join(DELUGE_PATH, "deluged.exe")
DELUGE_DATA_PATH = os.path.join(os.environ.get("APPDATA", None), "deluge")
DELUGED_LOG_PATH = os.path.join(DELUGE_DATA_PATH, "deluged.log")
AUTH_FILE_PATH = os.path.join(DELUGE_DATA_PATH, "auth")
