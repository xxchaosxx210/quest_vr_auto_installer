import os
import socket
import ctypes
import logging
import platform
import datetime
import base64
from typing import List, Generator
from dataclasses import dataclass

from deluge.handler import MagnetData


_Log = logging.getLogger(__name__)


@dataclass
class ApkPath:
    root: str
    path: str
    data_dirs: List[str]
    file_paths: List[str]


def is_connected_to_internet() -> bool:
    """wrapper for the OS specific internet connection check

    Returns:
        bool: returns true if connection availible or false if internet state is turned off
    """
    os_name = platform.system()
    if os_name == "Windows":
        return _win32_is_connected_to_internet()
    else:
        return _unix_is_connected_to_internet()


def _win32_is_connected_to_internet() -> bool:
    try:
        connection = ctypes.windll.wininet.InternetGetConnectedState(0, 0)
        return connection != 0
    except Exception as err:
        _Log.error(err.__str__())
    return False


def _unix_is_connected_to_internet() -> bool:
    connected = False
    try:
        host = socket.gethostbyname("www.google.com")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, 80))
    except (socket.gaierror, socket.error, OSError) as err:
        _Log.error(err.__str__())
    else:
        connected = True
    finally:
        if "sock" in locals():
            sock.close()
        return connected


def apk_exists(magnetdata: MagnetData) -> str | None:
    """appends the default download game path and the torrent path from the meta data
    and checks if the path exists and then scans for an apk package in that directory

    Args:
        MagnetData: from deluge.handler

    Raises:
        AttributeError:

    Returns:
        str: if found then the first Apk filename will be returned. returns None if no found
    """
    if not magnetdata.name:
        raise AttributeError(
            "No Magnet Name found for this game torrent. Unable to continue"
        )
    full_path = os.path.join(magnetdata.download_path, magnetdata.name)
    if not os.path.exists(full_path):
        return None
    # search for the apk in this path
    for entry in os.scandir(full_path):
        if entry.is_file() and entry.name.endswith(".apk"):
            return entry.path
    return None


def get_folder_size(folder_path: str) -> int:
    """Return the total size of a folder in bytes.

    Args:
        folder_path (str): The path to the folder.

    Returns:
        int: The size of the folder in bytes.
    """
    size = 0
    with os.scandir(folder_path) as it:
        for entry in it:
            if entry.is_file():
                size += entry.stat().st_size
            elif entry.is_dir():
                size += get_folder_size(entry.path)
    return size


def format_size(size: float) -> str:
    """formats the size of bytes into a formatted string representation

    Args:
        size (int): the byte size

    Returns:
        str: the formatted string
    """
    for unit in ["", "K", "M", "G"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}Bytes"
        size /= 1024.0
    return f"{size:.1f} TBytes"


def find_install_dirs(root_dir: str) -> Generator[ApkPath, None, None]:
    """
    Generator function that scans the root_dir looking for APK files and data subfolders.

    Args:
        root_dir (str): The root folder to search in.

    Yields:
        Generator[ApkPath, None, None]: An APK directory if found, as an ApkPath object with the path to the APK file
            and a list of paths to data directories.
    """
    # Use a set to keep track of seen APK files, to avoid duplicates.
    apk_files = set()

    # Walk through the directory tree.
    for root, dirs, files in os.walk(root_dir):
        # Check each file in the current directory.
        for file in files:
            # If the file ends in .apk, it's an APK file.
            if file.endswith(".apk"):
                apk_path = os.path.join(root, file)
                # If we haven't seen this APK file before, process it.
                if apk_path not in apk_files:
                    # Create lists to store paths to data directories and files.
                    data_dirs: List[str] = []
                    file_paths: List[str] = []
                    apk_dir = os.path.dirname(apk_path)
                    # Loop through all subdirectories of the APK directory.
                    for sub_dir in os.listdir(apk_dir):
                        sub_path = os.path.join(apk_dir, sub_dir)
                        # If the subdirectory is a data directory (not the APK file itself), store its path.
                        if os.path.isdir(sub_path) and sub_path != apk_path:
                            data_dirs.append(sub_path)
                    # Add the APK file to the set of seen files.
                    apk_files.add(apk_path)
                    # Create an ApkPath object with the APK file path and list of data directory paths.
                    apk_file = ApkPath(root, apk_path, data_dirs, file_paths)
                    # Yield the ApkPath object to the caller.
                    yield apk_file


def format_timestamp_to_str(timestamp: float, include_hms: bool = False) -> str:
    """formats the timestamp into a readabele string

    Args:
        timestamp (int): the datetime timestamp

    Returns:
        str: DD:MM:YYYY HH:MM
    """
    dt = datetime.datetime.fromtimestamp(timestamp)
    if not include_hms:
        fmt_time = dt.strftime("%d-%m-%Y")
    else:
        fmt_time = dt.strftime("%d-%m-%Y %H:%M")
    return fmt_time


def format_str_to_timestamp(tstamp_str: str, include_hms: bool = False):
    if include_hms:
        format = "%d-%m-%Y %H:%M"
    else:
        format = "%d-%m-%Y"
    dt = datetime.datetime.strptime(tstamp_str, format)
    timestamp = dt.timestamp()
    return timestamp


def get_changed_properties(original: dict, new: dict) -> dict:
    """compare the original dict with a new dict and check if any fields have changed

    Args:
        original (dict): original dict to compare with
        new (dict): the new dict

    Returns:
        dict: returns a dict with fields that have changed from the original
    """
    changed = {}
    for key in original:
        if key in new and original[key] != new[key]:
            changed[key] = new[key]
    return changed


def encode_str2b64(data: str) -> str:
    """encode the string to base64 string

    Args:
        data (str): the string to encode

    Returns:
        str: the encoded string
    """
    # encode the decrpyted string back to bytes
    byte_string = data.encode("utf-8")
    # encode the encoded bytes back to base64 bytes
    byte_b64string = base64.b64encode(byte_string)
    # decode the base64 bytes back to a base64 readable str again
    return byte_b64string.decode("utf-8")
