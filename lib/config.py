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
from pydantic import BaseModel

from lib.schemas import QuestMagnet


# App Meta data
APP_NAME = "QuestVRAutoinstaller"
APP_VERSION = "0.1"
AUTHOR = "Paul Millar"


HOMEDRIVE = ""

# check if windows OS and assign the main drive
if os.name == "nt":
    HOMEDRIVE = os.getenv("HOMEDRIVE", "C:")
else:
    raise OSError("OS not yet supported")

# Have to add the Home Drive otherwise Deluge kicks up an error
APP_BASE_PATH = HOMEDRIVE + os.path.join(os.getenv("HOMEPATH"), APP_NAME)
# The path to save the torrent files to
APP_DOWNLOADS_PATH = os.path.join(APP_BASE_PATH, "Games")
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


_Log = logging.getLogger(__name__)


class DebugSettings:
    enabled: bool = False
    device_names = ["QUEST1FAKE", "QUEST2FAKE"]
    package_names = [
        "com.oculus.TestGame",
        "com.rockstar.GTAV",
        "com.ubisoft.SplinterCellConviction",
        "com.golfcompany.MiniGolfAwesome",
    ]


class Settings(BaseModel):
    download_path: str = APP_DOWNLOADS_PATH
    remove_files_after_install: bool = False
    close_dialog_after_install: bool = False
    download_only: bool = False

    def set_download_path(self, path: str) -> None:
        try:
            os.makedirs(path)
        except OSError:
            pass
        finally:
            self.download_path = path

    @staticmethod
    def load(path: str = APP_SETTINGS_PATH) -> "Settings":
        """load the settings.json and return a class instance of Settings

        Args:
            path (str, optional): _description_. Defaults to APP_SETTINGS_PATH.

        Returns:
            Settings:
        """
        try:
            with open(path, "r") as fp:
                data = json.load(fp)
            settings = Settings(**data)
            return settings
        except FileNotFoundError:
            settings = Settings()
            return settings

    def save(self, path: str = APP_SETTINGS_PATH) -> None:
        """save the settings to path

        Args:
            path (str, optional): _description_. Defaults to APP_SETTINGS_PATH.
        """
        with open(path, "w") as fp:
            text = self.json()
            fp.write(text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="QuestVRAutoInstaller Parser")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    return args


def initalize_logger():
    """
    sets up the logger and log handler
    """
    logging.basicConfig(
        format="%(asctime)s %(message)s",
        handlers=[logging.StreamHandler()],
        level=logging.INFO,
    )
    file_handler = logging.FileHandler(APP_LOG_PATH)
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    sys.excepthook = log_handler
    _Log.addHandler(file_handler)


def log_handler(
    exc_type: type, exc_value: Exception, exc_traceback: TracebackType
) -> None:
    """file log handler. This only catches exceptions from the same thread

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


def async_log_handler(loop: asyncio.ProactorEventLoop, context: dict) -> None:
    """handles exceptions from coroutines and writes to log.txt

    Args:
        loop (asyncio.ProactorEventLoop): the event loop the exception came from
        context (dict): contains message: str and exception: BaseException
    """
    exception = context.get("exception", None)
    if not exception:
        _Log.error(context.get("message", ""))
        return
    _Log.error("".join(traceback.format_exception(exception)))


def save_local_quest_magnets(path: str, qm_list: List[QuestMagnet]) -> bool:
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


def load_local_quest_magnets(path: str) -> List[QuestMagnet]:
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
        return list(map(lambda item: QuestMagnet(**item), json.load(fp)))


def create_data_paths(
    base_path: str = APP_BASE_PATH,
    download_path: str = APP_DOWNLOADS_PATH,
    data_path: str = APP_DATA_PATH,
) -> None:
    """creates the base path for games and app data such as log.txt and settings"""
    for path in (base_path, download_path, data_path):
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


def create_path_from_name(download_path: str, name: str) -> str:
    """creates a full path to the game directory to be created and downloaded to
    also sanatizes the name

    Args:
        name (str): the name of the torrent

    Returns:
        str: returns the full path name
    """
    name = sanitize_filename(name)
    name = name.replace(" ", "_")
    pathname = os.path.join(download_path, name)
    return pathname
