import asyncio
from datetime import timedelta
import os
import time
from typing import Any, Dict, List, cast
import random

import deluge.handler as dh
import lib.utils
import lib.quest

MAX_DOWNLOAD_SPEED = 4500000.0
MIN_DOWNLOAD_SPEED = 2500000.0


class Quest:
    def __init__(self, name: str, package_names: List[str]) -> None:
        """generates a fake quest installation environment

        Args:
            name (str): the name of the quest
            package_names (List[str]): list of package names that will be on the fake quest
        """
        self.name = name
        self.package_names = package_names

    @staticmethod
    def get_torrent_status(seconds: int, total_time: int) -> Dict[str, Any]:
        """simulate the deluge client function get_torrent_status

        Args:
            seconds (int): how many seconds from 0 to total_time
            total_time (int): the total time in seconds

        Returns:
            Dict[str, Any]: the torrent status contains: state, progress, download_payload_rate, eta
        """
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

    async def install_game(
        self,
        callback: lib.quest.InstallStatusFunction,
        device_name: str,
        apk_dir: lib.utils.ApkPath,
        raise_exception: Exception | None = None,
    ) -> None:
        """fake install game function. Simulates the install process

        Args:
            callback (InstallStatusFunction): the callback to recieve updates to
            device_name (str): the name of the selected to device to install to
            apk_dir (ApkPath): contains the apk file path, subpaths and subfiles to be pushed onto the remote device
            raise_exception (Exception, optional): if not None, will raise the exception. Defaults to None.

        Raises:
            ValueError: if device_name is empty string
            LookupError: could not find the device in the device list. Possible disconnected Quest device
        """

        if not device_name:
            raise ValueError("No Device selected")
        try:
            device_names = Debug.get_device_names()
        except Exception as err:
            raise err
        if not device_name in device_names:
            raise LookupError(
                "Device disconnected. Please reconnect device and re-install"
            )

        # get file stats from apk package
        total_size = random.uniform(1000000.0, 10000000.0)
        formatted_size = lib.utils.format_size(float(total_size))
        apk_name = os.path.split(apk_dir.path)[-1]

        message = f"Installing {apk_name}. Total Size: {formatted_size}"

        callback(message)

        # start install
        start_time = time.time()
        callback(f"Installing {apk_name} onto {device_name}")
        callback(f"Total size: {formatted_size}")
        callback(f"Starting install of {apk_name} onto {device_name}")
        callback(
            "Installing game this may take several minutes. Please do not disconnect your device"
        )
        await asyncio.sleep(random.uniform(1.0, 5.0))
        callback(
            "Moving files onto device. This may take a few minutes. Do not disconnect Device"
        )
        if raise_exception is not None:
            raise raise_exception
        await asyncio.sleep(random.uniform(1.0, 5.0))

        elapsed_time = time.time() - start_time
        formatted_time = str(timedelta(seconds=elapsed_time))

        callback("Install has completed successfully. Enjoy!")
        callback(f"Install time: {formatted_time}")

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
    for testing the GUI controls and simulation of the Quest device
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
            List[str]: list of fake Quest device names
        """
        device_names = list(map(lambda quest: quest.name, Debug.devices))
        return device_names

    @staticmethod
    def add_device(name: str, packages: List[str]) -> None:
        """adds a fake Quest device to the list of devices

        Args:
            name (str): the name of the device
            packages (List[str]): list of packages installed on the device
        """
        Debug.devices.append(Quest(name, packages))

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

    @staticmethod
    def generate_apk_path_object(root: str) -> lib.utils.ApkPath:
        """generate a fake apk download path complete with fake files

        Args:
            root (str): the base directory where the torrent files are downloaded

        Returns:
            lib.utils.ApkPath: the fake apk path object
        """
        path = os.path.join(root, "fake_game", "fake_gamev5674[ENG]")
        data_dirs = [os.path.join(path, "com.fake.game")]
        file_paths = [
            os.path.join(path, "base.apk"),
            os.path.join(data_dirs[0], "main.1234567890.com.example.game.obb"),
        ]
        return lib.utils.ApkPath(root, path, data_dirs, file_paths)
