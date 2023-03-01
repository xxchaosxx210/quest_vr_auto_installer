import asyncio
from typing import Any, Dict, List, cast
import random

import deluge.handler as dh

MAX_DOWNLOAD_SPEED = 4500000.0
MIN_DOWNLOAD_SPEED = 2500000.0


class Quest:
    def __init__(self, name: str, package_names: List[str]) -> None:
        self.name = name
        self.package_names = package_names

    @staticmethod
    def get_torrent_status(seconds: int, total_time: int) -> Dict[str, Any]:
        torrent_status: Dict[str, Any] = {}
        if seconds + 1 < total_time:
            state = dh.State.Downloading
        else:
            state = dh.State.Finished
        if state == dh.State.Downloading:
            download_payload_rate = random.uniform(
                MIN_DOWNLOAD_SPEED, MAX_DOWNLOAD_SPEED
            )
            eta = total_time - seconds
            seconds_left = eta
            progress = (total_time - seconds_left) / total_time * 100
        else:
            download_payload_rate = 0.0
            eta = 0
            progress = 100.0
        torrent_status["state"] = state
        torrent_status["progress"] = progress
        torrent_status["download_payload_rate"] = download_payload_rate
        torrent_status["eta"] = eta
        return torrent_status

    async def simulate_download(
        self,
        callback: dh.StatusUpdateFunction,
        error_callback: dh.ErrorUpdateFunction,
        magnet_data: dh.MagnetData,
        total_time: int,
    ) -> bool:
        """replicates the deluge.handler.download function

        Args:
            callback (dh.StatusUpdateFunction): _description_
            error_callback (dh.ErrorUpdateFunction): _description_
            magnet_data (dh.MagnetData): _description_

        Returns:
            bool: if successful returns True else False
        """
        for seconds in range(total_time):
            torrent_status = Quest.get_torrent_status(seconds, total_time)
            torrent_status["index"] = magnet_data.index

            if magnet_data.queue is None:
                raise TypeError(
                    "magnet_data.queue cannot be of None type when retrieving messages"
                )
            try:
                message = await asyncio.wait_for(magnet_data.queue.get(), timeout=1)
            except asyncio.TimeoutError:
                pass
            else:
                if isinstance(message, dict):
                    if message["request"] == dh.QueueRequest.CANCEL:
                        return False
            finally:
                await cast(Any, callback)(torrent_status)
        return True


class Debug:

    """
    for testing the GUI controls
    """

    enabled: bool = False
    devices = [
        Quest("QUEST1", ["com.fake.MarioKart"]),
        Quest("QUEST2", ["com.fake.Zelda", "org.com.F1"]),
    ]

    @staticmethod
    def get_device_names() -> List[str]:
        """simulate the adblib.adb_interface.get_device_names method

        Returns:
            List[str]: list of device names
        """
        device_names = list(map(lambda quest: quest.name, Debug.devices))
        return device_names

    @staticmethod
    def get_device(name: str) -> Quest:
        """gets the device related to the device name

        Args:
            name (str): the name of the device to retrieve

        Raises:
            LookupError: if no device found then this gets raised

        Returns:
            Quest: the Quest fake object for testing
        """
        found_devices = list(filter(lambda device: device.name == name, Debug.devices))
        if not found_devices:
            raise LookupError("Could not find device with that name")
        # return the first element
        return found_devices[0]
