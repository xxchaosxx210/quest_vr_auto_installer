import os
import socket
import ctypes
import logging
from typing import Tuple, List

from deluge.handler import MagnetData


_Log = logging.getLogger(__name__)


def is_connected_to_internet() -> bool:
    """wrapper for the OS specific internet connection check

    Returns:
        bool: returns true if connection availible or false if internet state is turned off
    """
    if os.name == "nt":
        return win32_is_connected_to_internet()
    else:
        return unix_is_connected_to_internet()


def win32_is_connected_to_internet() -> bool:
    try:
        connection = ctypes.windll.wininet.InternetGetConnectedState(0, 0)
        return connection != 0
    except Exception as err:
        _Log.error(err.__str__())
    return False


def unix_is_connected_to_internet() -> bool:
    try:
        host = socket.gethostbyname("www.google.com")
        with socket.create_connection((host, 80), 2) as s:
            s.close()
        return True
    except (socket.gaierror, socket.error, OSError) as err:
        _Log.error(err.__str__())
    return False


def apk_exists(magnetdata: MagnetData) -> str:
    """appends the default download game path and the torrent path from the meta data
    and checks if the path exists and then scans for an apk package in that directory

    Args:
        MagnetData: from deluge.handler

    Returns:
        str: if found then the first Apk filename will be returned. returns None if no found
    """
    full_path = os.path.join(magnetdata.download_path, magnetdata.meta_data.name)
    if not os.path.exists(full_path):
        return None
    # search for the apk in this path
    for entry in os.scandir(full_path):
        if entry.is_file() and entry.name.endswith(".apk"):
            return entry.path
    return None


async def find_apk_directory_async(root_dir: str) -> Tuple[str, List[str], str]:
    if not os.path.exists(root_dir):
        return None, [], None

    async def scan_dir(dir_path: str) -> Tuple[str, List[str], str]:
        for dir_entry in os.scandir(dir_path):
            if dir_entry.is_file() and dir_entry.name.endswith(".apk"):
                apk_file_path = os.path.abspath(dir_entry.path)
                apk_dir = os.path.dirname(apk_file_path)
                data_paths = [
                    d.name for d in os.scandir(apk_dir) if not d.name.endswith(".apk")
                ]
                return apk_dir, data_paths, dir_entry.name
            elif dir_entry.is_dir():
                apk_dir, subdirs, apk_file_name = await scan_dir(dir_entry.path)
                if apk_dir is not None:
                    return apk_dir, subdirs, apk_file_name

        return None, [], ""

    return await scan_dir(root_dir)


def find_apk_directory(root_dir: str) -> Tuple[str, List[str], str]:
    """
    Args:
        root_dir (str): The root directory to search for APK files.

    Returns:
        Tuple[str, List[str]]: A tuple containing the absolute path to the directory containing the APK file,
                                the name of the APK file, and a list of subdirectories in the APK directory.
    """
    if not os.path.exists(root_dir):
        return None, [], None
    for dir_entry in os.scandir(root_dir):
        if dir_entry.is_file() and dir_entry.name.endswith(".apk"):
            apk_dir = os.path.abspath(dir_entry.path)
            apk_dir = os.path.dirname(apk_dir)
            sub_paths = [d.name for d in os.scandir(apk_dir) if d.is_dir()]
            return apk_dir, sub_paths, dir_entry.name
    return None, [], None
