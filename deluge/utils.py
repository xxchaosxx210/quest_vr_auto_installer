import re
import math
import base64
import asyncio
import logging
import subprocess
from typing import Any, Dict, List, Optional, Union
import datetime

from pydantic import BaseModel
from bencode import decode as bendecode
from bencode import str_to_be
from deluge_client import LocalDelugeRPCClient

import deluge.config

TORRENT_ID_IN_ERROR_PATTERN = re.compile(r"\(([a-zA-Z0-9]+)\)")

USER_AUTH_PATTERN = re.compile(r"^([^:]+):(\w+):([0-9]|10)$")


_Log = logging.getLogger()


# Requires Deluge to be installed first


class File(BaseModel):
    length: int
    path: List[str]


class MetaData(BaseModel):
    name: str
    files: Optional[List[File]] | None
    piece_length: int
    torrent_id: str

    def __str__(self) -> str:
        if self.files is not None:
            paths = ["\n".join(file.path) for file in self.files]
            formatted_path = "\n".join(paths)
        else:
            formatted_path = ""
        return f"Name: {self.name}\nPaths: {formatted_path}\nLength: {self.piece_length}\nTorrent ID: {self.torrent_id}"

    def get_paths(self) -> List[str]:
        if not self.files:
            return []
        paths = [path for file in self.files for path in file.path]
        return paths


class DelugeAccount(BaseModel):
    name: str
    password: str
    level: int


def _remove_showwindow_flag() -> subprocess.STARTUPINFO:
    """removes the show window flag so the terminal isnt shown when executing the adb commands

    Returns:
        int: new flag for startupinfo parameter
    """
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return startupinfo


def start_deluge_daemon() -> subprocess.Popen:
    process = subprocess.Popen(
        [deluge.config.DELUGE_DAEMON_PATH, "--port", f"{deluge.config.DAEMON_PORT}"],
        startupinfo=_remove_showwindow_flag(),
    )
    return process


def format_eta(eta_seconds: int) -> str:
    """Convert the eta_seconds value from seconds to a HH:MM:SS string


    Args:
        eta_seconds (int): time of download eta

    Returns:
        str: formatted string
    """
    delta = datetime.timedelta(seconds=eta_seconds)
    # Format the timedelta object into a HH:MM:SS string
    formatted_eta = str(delta).split(".")[0]
    return formatted_eta


def format_download_speed(download_speed: int) -> str:
    """converts download speed to a formatted string depending on the speed it is at

    Args:
        download_speed (int): _description_

    Returns:
        str: formatted string "xx MB/s"
    """
    # Convert the download_speed value from bytes to kilobytes
    kilobytes = math.ceil(download_speed / 1024)

    # Format the kilobyte value into KB/MB/GB string
    if kilobytes < 1024:
        formatted_speed = str(kilobytes) + " KB/s"
    elif kilobytes < 1024**2:
        megabytes = round(kilobytes / 1024, 2)
        formatted_speed = str(megabytes) + " MB/s"
    else:
        gigabytes = round(kilobytes / 1024**2, 2)
        formatted_speed = str(gigabytes) + " GB/s"

    return formatted_speed


def format_progress(progress) -> str:
    """formats the progress to a whole integer

    Args:
        progress (_type_): _description_

    Returns:
        str: formatted string ie 00, 01
    """

    # Limit the progress to a range of 0-100
    limited_progress = min(max(progress, 0), 100)
    # Cast the float value to an int
    limited_progress = int(limited_progress)
    # Format the progress to a string with 2 numbers
    formatted_progress = "{:02d}".format(limited_progress)

    return formatted_progress


def get_deluge_account(client_name: str) -> DelugeAccount | None:
    """incase you want to connect to a different deluge account rather than the  default localclient

    Args:
        client_name (str): username of the client. Must not be empty string

    Raises:
        ValueError: If client_name id empty string
        Exception: Unhandled exception

    Returns:
        DelugeAccount | None: check DelugeAccount for info
    """
    if not client_name.strip():
        raise ValueError("Client name must be a non-empty string")
    try:
        with open(deluge.config.AUTH_FILE_PATH, "r") as fp:
            for line in fp.read().split("\n"):
                match = USER_AUTH_PATTERN.match(line)
                if not match:
                    continue
                username = match.group(1)
                password_hash = match.group(2)
                admin_level = int(match.group(3))
                if username == client_name:
                    return DelugeAccount(
                        name=username, password=password_hash, level=admin_level
                    )
    except FileNotFoundError:
        return None
    except Exception as err:
        raise err
    return None


async def get_magnet_info(uri: str, timeout: int = 10) -> MetaData:
    """
    gets meta data from the magnet uri. Important if you want extra information about the torrent
    before adding to deluge session

    Args:
        uri (str): the magnet uri
        timeout (int, optional): how long the connection stays until timing out. Defaults to 10.

    Raises:
        Exception: unhandled exception

    Returns:
        deluge.utils.MetaData: check the deluge.utils module for properties
    """
    try:
        with LocalDelugeRPCClient() as deluge_client:
            torrent_id, b64_str = deluge_client.call(
                "core.prefetch_magnet_metadata", uri, timeout
            )
            if not b64_str:
                raise ValueError("b64_str was empty. Proberbly lack of seeders")
            # convert the binary encoded data to bytes
            be_base64 = str_to_be(b64_str)
            be_dict_data = base64.b64decode(be_base64)
            be_meta: Union[bytes, dict, int, list] = bendecode(be_dict_data)
            if type(be_meta) is not dict:
                raise TypeError("be_meta returned from bencode was not of type dict")

            # decode the binary keys to normal string keys
            # basically construct a new dict
            decoded_data = {}
            if b"files" in be_meta:
                decoded_data["files"] = list(
                    map(lambda bfile: decode_bfile(bfile), be_meta[b"files"])
                )
            decoded_data["piece_length"] = be_meta[b"piece length"]
            decoded_data["name"] = be_meta[b"name"].decode()
            decoded_data["torrent_id"] = torrent_id

            # validate and turn dict into class object
            metadata = MetaData(**decoded_data)
            return metadata

    except Exception as err:
        raise err


def decode_bfile(bfile: dict) -> Dict[str, Any]:
    """decode the file key from the meta data dict

    file is a dict and contains keys: length: int, path: List[str]

    Args:
        bfile (dict): the dict with the bytes key names

    Returns:
        Dict[str, Any]: returns a decoded key names as strings
    """
    decoded_file: Dict[str, Any] = {}
    decoded_file["length"] = bfile[b"length"]
    decoded_file["path"] = list(map(lambda path: path.decode(), bfile[b"path"]))
    return decoded_file


def get_log_data() -> str:
    """gets the log data from the

    Returns:
        str:
    """
    with open(deluge.config.DELUGED_LOG_PATH, "r") as fp:
        return fp.read()
