import os
import sys
import logging
import traceback
from pathvalidate import sanitize_filename

APP_NAME = "QuestVRAutoinstaller"
APP_VERSION = "0.1"
AUTHOR = "Paul Millar"

HOMEDRIVE = ""

if os.name == "nt":
    HOMEDRIVE = os.getenv("HOMEDRIVE", "C:")

# Have to add the Home Drive otherwise Deluge kicks up an error
APP_BASE_PATH = HOMEDRIVE + os.path.join(os.getenv("HOMEPATH"), APP_NAME)

APP_DOWNLOADS_PATH = os.path.join(APP_BASE_PATH, "Games")

APP_DATA_PATH = os.path.join(APP_BASE_PATH, "Data")
APP_LOG_PATH = os.path.join(APP_DATA_PATH, "log.txt")

QUEST_ROOT = "/sdcard"

QUEST_DATA_DIRECTORY = f"{QUEST_ROOT}/Android/data"
QUEST_OBB_DIRECTORY = f"{QUEST_ROOT}/Android/obb"

# where the apk will temp be pushed to and installed from
QUEST_APK_TEMP_DIRECTORY = QUEST_ROOT + "/Download"


_Log = logging.getLogger(__name__)


def initalize_logger():
    logging.basicConfig(
        format="%(asctime)s %(message)s", handlers=[logging.StreamHandler()]
    )
    file_handler = logging.FileHandler(APP_LOG_PATH)
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    sys.excepthook = log_handler
    _Log.addHandler(file_handler)


def log_handler(exc_type: type, exc_value: Exception, exc_traceback: traceback) -> None:
    """file log handler

    Args:
        exc_type (type): the type of exception
        exc_value (Exception): the exception instance
        exc_traceback (traceback): the traceback
    """
    tb_frames = traceback.extract_tb(exc_traceback)
    trunc_frames = tb_frames[-2:]
    formatted_trunc_frames = traceback.format_list(trunc_frames)
    formatted_error = "".join(formatted_trunc_frames)
    _Log.error(formatted_error)


def create_data_paths() -> None:
    """creates the base path for games and app data such as log.txt and settings"""
    for path in (APP_BASE_PATH, APP_DOWNLOADS_PATH, APP_DATA_PATH):
        create_path(path)


def create_path(path: str):
    try:
        os.makedirs(path)
    except OSError:
        _Log.info(f"{path} already exists")


def create_game_directory(path: str) -> None:
    """

    Args:
        path (str): the name of the torrent

    Returns:
        str: the pathname created will be None if error
    """
    try:
        os.makedirs(path)
    except OSError as error:
        _Log.error(f"Could not create path {path}. Reason: {error.__str__()}")
    finally:
        return


def create_path_from_name(name: str) -> str:
    """creates a full path to the game directory to be created and downloaded to
    also sanatizes the name

    Args:
        name (str): the name of the torrent

    Returns:
        str: returns the full path name
    """
    name = sanitize_filename(name)
    name = name.replace(" ", "_")
    pathname = os.path.join(APP_DOWNLOADS_PATH, name)
    return pathname
