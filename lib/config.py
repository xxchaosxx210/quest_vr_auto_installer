"""
config.py

contains functions and enviroment variables for apps IO data
also contains logger

"""


import json
import os
import sys
import logging
import asyncio
import traceback
import argparse
from types import TracebackType
from typing import List

from pathvalidate import sanitize_filename

from api.schemas import Game, LogErrorRequest
from api.client import post_error
import lib.tasks


# App Meta data
APP_NAME = "QuestCave"
APP_VERSION = "1.0.4"
AUTHOR = "Paul Millar"


HOMEDRIVE = ""

# check if windows OS and assign the main drive
if os.name == "nt":
    HOMEDRIVE = os.getenv("HOMEDRIVE", "C:")
else:
    raise OSError("OS not yet supported")

# Have to add the Home Drive otherwise Deluge kicks up an error
HOMEPATH = os.getenv("HOMEPATH")
if HOMEPATH is None:
    raise EnvironmentError("Unable to find enviroment Home Path")
APP_BASE_PATH = HOMEDRIVE + os.path.join(HOMEPATH, APP_NAME)
# The path to save the torrent files to
APP_DOWNLOADS_PATH: str = os.path.join(APP_BASE_PATH, "Games")
# Path to save log data, local magnet json file and the APP settings
APP_DATA_PATH = os.path.join(APP_BASE_PATH, "Data")
APP_LOG_PATH = os.path.join(APP_DATA_PATH, "log.txt")
APP_SETTINGS_PATH = os.path.join(APP_DATA_PATH, "settings.json")


# local json file for storing local magnet database incase no response from the API
QUEST_MAGNETS_PATH = os.path.join(APP_DATA_PATH, "questmagnets.json")


# Quest Installation paths

QUEST_ROOT = "/sdcard"

QUEST_DATA_DIRECTORY = f"{QUEST_ROOT}/Android/data"
QUEST_OBB_DIRECTORY = f"{QUEST_ROOT}/Android/obb"

# where the apk will temp be pushed to and installed from
QUEST_APK_TEMP_DIRECTORY = QUEST_ROOT + "/Download"

# avoid the circular import
from lib.settings import Settings


_Log = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """parse the arguments from the terminal

    Returns:
        argparse.Namespace:
    """
    parser = argparse.ArgumentParser(description="QuestCave Parser")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    parser.add_argument("-s", "--skip", action="store_true", help="Skip the loading")
    args = parser.parse_args()
    return args


def initalize_logger():
    """
    sets up the logger and log handler
    """
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
        handlers=[logging.StreamHandler()],
        level=logging.INFO,
    )
    file_handler = logging.FileHandler(APP_LOG_PATH)
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    sys.excepthook = unhandled_exception_handler
    _Log.addHandler(file_handler)


def unhandled_exception_handler(
    exc_type: type, exc_value: Exception, exc_traceback: TracebackType
) -> None:
    """file log handler. This only catches exceptions from the same thread

    Args:
        exc_type (type): the type of exception
        exc_value (Exception): the exception instance
        exc_traceback (traceback): the traceback
    """
    traceback_string = "".join(
        traceback.format_exception(exc_type, exc_value, exc_traceback)
    )
    _Log.error(traceback_string)
    # post the unhandled exception to the database
    settings = Settings.load()
    error_request = LogErrorRequest(
        type=str(exc_type),
        uuid=settings.uuid,
        exception="".join(exc_value.args),
        traceback=traceback_string,
    )
    try:
        lib.tasks.check_task_and_create(post_error, error_request=error_request)
    except lib.tasks.TaskIsRunning:
        pass


def async_log_handler(loop: asyncio.ProactorEventLoop, context: dict) -> None:
    """handles exceptions from coroutines and writes to log.txt

    Args:
        loop (asyncio.ProactorEventLoop): the event loop the exception came from
        context (dict): contains message: str and exception: BaseException
    """
    exception: Exception = context.get("exception", None)
    if not exception:
        _Log.error(context.get("message", ""))
        return
    if Settings is None:
        from settings import Settings

        print(f"Settings is None. Exception context: {context}")
        return
    settings = Settings.load()

    tb_list: List[str] = traceback.format_tb(exception.__traceback__)
    tb_str = "".join(tb_list)
    error_request = LogErrorRequest(
        type=exception.__class__.__name__,
        uuid=settings.uuid,
        exception=exception.__str__(),
        traceback=tb_str,
    )
    try:
        lib.tasks.check_task_and_create(post_error, error_request=error_request)
    except lib.tasks.TaskIsRunning:
        pass
    except Exception as err:
        _Log.error(err.__str__())
    _Log.error(tb_str)


def save_local_quest_magnets(path: str, qm_list: List[Game]) -> bool:
    """converts and saves the QuestMagnets to json

    Args:
        path (str): json file to save to
        qm_list (List[QuestMagnet]): the questmagnets to be saved

    Returns:
        bool: true if successful
    """
    try:
        with open(path, "w") as fp:
            json.dump(list(map(lambda qm: qm.dict(), qm_list)), fp)
    except Exception as err:
        _Log.error(err.__str__())
        return False
    else:
        return True


def load_local_quest_magnets(path: str) -> List[Game]:
    """loads QuestMagnets from json file

    Args:
        path (str): the path of the json file to load

    Returns:
        List[QuestMagnet]:
    """
    if not os.path.exists(path):
        _Log.error(f"{path} does not exist")
        return []
    with open(path, "r") as fp:
        return list(map(lambda item: Game(**item), json.load(fp)))


def remove_file(path: str = QUEST_MAGNETS_PATH) -> bool:
    """removes a file

    Args:
        path (str, optional): the path to the file. Defaults to QUEST_MAGNETS_PATH.

    Returns:
        bool: true if successful, false if not
    """
    try:
        os.remove(path)
    except (FileNotFoundError, PermissionError, IsADirectoryError):
        pass
    except OSError as err:
        _Log.error(err.__str__())
    else:
        return True
    return False


def create_data_paths(
    base_path: str = APP_BASE_PATH,
    download_path: str = APP_DOWNLOADS_PATH,
    data_path: str = APP_DATA_PATH,
) -> None:
    """creates the base path for games and app data such as log.txt and settings"""
    for path in (base_path, download_path, data_path):
        try:
            os.makedirs(path)
        except OSError:
            _Log.info(f"{path} already exists")


def create_path_from_name(download_path: str, name: str) -> str:
    """creates a full path to the game directory to be created and downloaded to
    also sanatizes the name

    Args:
        name (str): the name of the torrent

    Returns:
        str: returns the full path name
    """
    filename = sanitize_filename(name)
    if type(filename) != str:
        raise TypeError("Filename from sanitize_filename is not str type")
    filename = filename.replace(" ", "_")
    pathname = os.path.join(download_path, filename)
    return pathname
