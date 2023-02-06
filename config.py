import os
import logging
from pathvalidate import sanitize_filename

APP_NAME = "QuestVRAutoinstaller"
APP_VERSION = "0.1"
AUTHOR = "Paul Millar"

HOMEDRIVE = os.environ.get("HOMEDRIVE", "C:")

# Have to add the Home Drive otherwise Deluge kicks up an error
DATA_PATH = HOMEDRIVE + os.path.join(os.environ["HOMEPATH"], APP_NAME)
GAME_DOWNLOAD_PATH = os.path.join(DATA_PATH, "Games")

QUEST_ROOT = "/sdcard"

QUEST_DATA_DIRECTORY = f"{QUEST_ROOT}/Android/data"
QUEST_OBB_DIRECTORY = f"{QUEST_ROOT}/Android/obb"

# where the apk will temp be pushed to and installed from
QUEST_APK_TEMP_DIRECTORY = QUEST_ROOT + "/Download"

_Log = logging.getLogger()


def create_data_paths():
    for path in (DATA_PATH, GAME_DOWNLOAD_PATH):
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
    pathname = os.path.join(GAME_DOWNLOAD_PATH, name)
    return pathname
