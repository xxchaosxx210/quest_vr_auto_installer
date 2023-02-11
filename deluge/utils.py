import re
import math
import base64
import asyncio
import logging
import subprocess
from typing import List, Optional
import datetime

from pydantic import BaseModel
from bencode import decode as bendecode
from bencode import str_to_be
from deluge_client import LocalDelugeRPCClient

import deluge.config

TORRENT_ID_IN_ERROR_PATTERN = re.compile(r"\(([a-zA-Z0-9]+)\)")


_Log = logging.getLogger()


# Requires Deluge to be installed first


class File(BaseModel):
    length: int
    path: List[str]


class MetaData(BaseModel):
    name: str
    files: Optional[List[File]]
    piece_length: int
    torrent_id: str


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
        creationflags=0x08000000,
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


def get_deluge_account(client_name: str) -> DelugeAccount:
    """incase you want to connect to a different deluge account rather than the  default localclient

    Args:
        client_name (str): username of the client

    Returns:
        DelugeAccount: check DelugeAccount for info
    """
    with open(deluge.config.AUTH_FILE_PATH, "r") as fp:
        for line in fp.read().split("\n"):
            username, password, admin_level = line.split(":")
            if username == client_name:
                return DelugeAccount(
                    name=username, password=password, level=admin_level
                )
    return None


async def get_magnet_info(uri: str, timeout: int = 10) -> MetaData:
    """
    gets meta data from the magnet uri. Important if you want extra information about the torrent
    before adding to deluge session

    Args:
        uri (str): the magnet uri
        timeout (int, optional): how long the connection stays until timing out. Defaults to 10.

    Returns:
        deluge.utils.MetaData: check the deluge.utils module for properties
    """
    try:
        with LocalDelugeRPCClient() as deluge_client:
            torrent_id, b64_str = deluge_client.call(
                "core.prefetch_magnet_metadata", uri, timeout
            )

            bmeta_base64 = str_to_be(b64_str)
            bin_meta = base64.b64decode(bmeta_base64)
            bin_meta = bendecode(bin_meta)

            decoded_meta = {}
            if hasattr(bin_meta, "files"):
                decoded_meta["files"] = list(
                    map(lambda bfile: decode_bfile(bfile), bin_meta[b"files"])
                )
            decoded_meta["piece_length"] = bin_meta[b"piece length"]
            decoded_meta["name"] = bin_meta[b"name"].decode()
            decoded_meta["torrent_id"] = torrent_id

            metadata = MetaData(**decoded_meta)

            _Log.info(
                f"Meta Data recieved. Name: {metadata.name}, Piece Size: {metadata.piece_length}"
            )

    except Exception as err:
        loop = asyncio.get_event_loop()
        loop.call_exception_handler({"message": err.__str__(), "exception": err})
        metadata = None
    finally:
        return metadata


def decode_bfile(bfile: dict):
    decoded_file = {}
    decoded_file["length"] = bfile[b"length"]
    decoded_file["path"] = list(map(lambda path: path.decode(), bfile[b"path"]))
    return decoded_file


def get_log_data() -> str:
    with open(deluge.config.DELUGED_LOG_PATH, "r") as fp:
        return fp.read()
