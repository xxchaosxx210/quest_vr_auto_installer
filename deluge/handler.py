"""

torrent.py - uses the deluge_client library and connects to the Deluge daemon
for retrieving meta information and downloading torrents

IMPORTANT!!! requires Deluge to be installed

if converting app to binary package make sure to install with deluge using inno or MSI etc.


TorrentOptions create a dict of the torrent options.
    Attributes:
        add_paused (bool): Add the torrrent in a paused state.
        auto_managed (bool): Set torrent to auto managed mode, i.e. will be started or queued automatically.
        download_location (str): The path for the torrent data to be stored while downloading.
        file_priorities (list of int): The priority for files in torrent, range is [0..7] however
            only [0, 1, 4, 7] are normally used and correspond to [Skip, Low, Normal, High]
        mapped_files (dict): A mapping of the renamed filenames in 'index:filename' pairs.
        max_connections (int): Sets maximum number of connections this torrent will open.
            This must be at least 2. The default is unlimited (-1).
        max_download_speed (float): Will limit the download bandwidth used by this torrent to the
            limit you set.The default is unlimited (-1) but will not exceed global limit.
        max_upload_slots (int): Sets the maximum number of peers that are
            unchoked at the same time on this torrent. This defaults to infinite (-1).
        max_upload_speed (float): Will limit the upload bandwidth used by this torrent to the limit
            you set. The default is unlimited (-1) but will not exceed global limit.
        move_completed (bool): Move the torrent when downloading has finished.
        move_completed_path (str): The path to move torrent to when downloading has finished.
        name (str): The display name of the torrent.
        owner (str): The user this torrent belongs to.
        pre_allocate_storage (bool): When adding the torrent should all files be pre-allocated.
        prioritize_first_last_pieces (bool): Prioritize the first and last pieces in the torrent.
        remove_at_ratio (bool): Remove the torrent when it has reached the stop_ratio.
        seed_mode (bool): Assume that all files are present for this torrent (Only used when adding a torent).
        sequential_download (bool): Download the pieces of the torrent in order.
        shared (bool): Enable the torrent to be seen by other Deluge users.
        stop_at_ratio (bool): Stop the torrent when it has reached stop_ratio.
        stop_ratio (float): The seeding ratio to stop (or remove) the torrent at.
        super_seeding (bool): Enable super seeding/initial seeding.

"""

import asyncio
from enum import Enum, auto as auto_enum
from typing import Any, Callable, Dict, cast
from dataclasses import dataclass

from deluge_client import (
    LocalDelugeRPCClient,
    # DelugeClientException
)


import deluge.config
import deluge.utils
from deluge.exceptions import TorrentIdNotFound


StatusUpdateFunction = Callable[[Dict[str, Any]], None]
ErrorUpdateFunction = Callable[[Exception], bool]


class QueueRequest(Enum):
    PAUSE = auto_enum()
    RESUME = auto_enum()
    CANCEL = auto_enum()


class State:
    Queued = "Queued"
    Checking = "Checking"
    Downloading = "Downloading"
    Seeding = "Seeding"
    Paused = "Paused"
    Error = "Error"
    Finished = "Finished"
    Downloaded = "Downloaded"
    Cancelled = "Cancelled"
    Unknown = "Unknown"


@dataclass
class MagnetData:
    """
    uri: str                - the magnet uri decoded to UTF-8
    download_path: str      - the folder the torrent will be saved to
    timeout: float          - the wait in seconds for the next iteration
    """

    uri: str
    download_path: str
    index: int
    name: str
    torrent_id: str
    queue: asyncio.Queue | None = None
    timeout: float = 1.0


async def add_magnet_to_session(
    deluge_client: LocalDelugeRPCClient, magnet_uri: str, options: dict
) -> str:
    """add the magnet to the deluge session and return the torrent id

    Args:
        magnet_uri (str): the magnet to download
        options (dict):
            download_path: str
            add_paused: bool
        deluge_client (LocalDelugeRPCClient): the client socket

    Raises:
        Exception: unhandled exception

    Returns:
        str: the torrent ID for that session
    """
    try:
        # pdb.set_trace()
        torrent_id = deluge_client.call("core.add_torrent_magnet", magnet_uri, options)
    except Exception as err:
        torrent_id = None
        if (
            "deluge.error.AddTorrentError: Torrent already in session"
            not in err.__str__()
        ):
            raise err
        # get the torrent ID from the torrent already in deluged session
        match = deluge.utils.TORRENT_ID_IN_ERROR_PATTERN.search(err.__str__())
        if match:
            torrent_id = match.group(1)
        else:
            raise TorrentIdNotFound("Could not find Torrent ID in regular expression")
    finally:
        return torrent_id


async def download(
    callback: StatusUpdateFunction,
    error_callback: ErrorUpdateFunction,
    magnet_data: MagnetData,
) -> bool:
    """connects to the deluged daemon, adds the magnet to the session for downloading
    retrieves the torrent ID and gets regular status until download is complete or
    error occurs

    Args:
        callback (Callable[[str, dict], bool]): event callback handler
        error_callback (Callable[[Exception], None]): error callback handler
        queue (asyncio.Queue): the atomic queue so the main coroutine can communicate with this one
        magnet_data (MagnetData): check the class for details

    Raises:
        TorrentIdNotFound: if no torrent ID can be found
    """

    # Status keys that can be passed for deluge 2.1.1

    # 'state': returns the state of the torrent as a string
    # 'progress': returns the progress of the torrent as a float
    # 'download_payload_rate': returns the download rate in bytes per second
    # 'upload_payload_rate': returns the upload rate in bytes per second
    # 'eta': returns the estimated time until completion as an integer
    # 'num_seeds': returns the number of seeds for the torrent
    # 'total_seeds': returns the total number of seeds for the torrent
    # 'num_peers': returns the number of peers for the torrent
    # 'total_peers': returns the total number of peers for the torrent
    # 'ratio': returns the share ratio for the torrent as a float
    # 'file_progress': returns the progress of each file in the torrent
    # 'distributed_copies': returns the distributed copies for the torrent as a float
    # 'time_added': returns the time the torrent was added as a timestamp
    # 'tracker_host': returns the hostname of the tracker for the torrent
    # 'next_announce': returns the time of the next announce as a timestamp
    ok_to_install = False
    remove_data_when_complete = False
    try:
        with LocalDelugeRPCClient() as deluge_client:
            torrent_id = await add_magnet_to_session(
                deluge_client,
                magnet_data.uri,
                {"download_location": magnet_data.download_path, "add_paused": False},
            )
            if not torrent_id:
                raise TorrentIdNotFound("Could not get Torrent ID from Daemon")
            while True:
                torrent_status: Dict[str, Any] = deluge_client.call(
                    "core.get_torrent_status",
                    torrent_id,
                    ["progress", "state", "download_payload_rate", "eta", "name"],
                )
                state = torrent_status.get("state", State.Finished)
                # magnet reference for the calling thread
                torrent_status["index"] = magnet_data.index
                if not torrent_status:
                    # torrent no longer is in session
                    break
                if state == State.Seeding or state == State.Finished:
                    torrent_status["state"] = State.Finished
                    await cast(Any, callback)(torrent_status)
                    break
                elif state == State.Error:
                    await cast(Any, error_callback)(
                        Exception(deluge_client.utils.get_log_data())
                    )
                    break
                elif state == State.Downloading or state == State.Paused:
                    await cast(Any, callback)(torrent_status)
                try:
                    if magnet_data.queue is None:
                        raise TypeError(
                            "queue is not type queue.Queue. cannot wait on queue"
                        )
                    message = await asyncio.wait_for(
                        magnet_data.queue.get(), timeout=1.0
                    )
                    request = message["request"]
                    if request == QueueRequest.PAUSE:
                        deluge_client.call("core.pause_torrent", torrent_id)
                    elif request == QueueRequest.RESUME:
                        deluge_client.call("core.resume_torrent", torrent_id)
                    elif request == QueueRequest.CANCEL:
                        remove_data_when_complete = True
                        torrent_status["state"] = State.Cancelled
                        torrent_status["download_payload_rate"] = 0
                        torrent_status["eta"] = 0
                        torrent_status["progress"] = 0.0
                        await cast(Any, callback)(torrent_status)
                        break
                except asyncio.TimeoutError:
                    pass
            # remove the torrent from the session but dont delete the data
            if torrent_id:
                deluge_client.call(
                    "core.remove_torrent", torrent_id, remove_data_when_complete
                )
    except Exception as err:
        cast(Any, error_callback)(err)
        raise err
    else:
        return ok_to_install
