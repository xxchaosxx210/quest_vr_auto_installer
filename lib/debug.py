import asyncio
import os
from typing import Any, Callable, Dict, List, Tuple, cast
import random


import deluge.handler as dh
import lib.utils
import lib.quest

MAX_DOWNLOAD_SPEED = 4500000.0
MIN_DOWNLOAD_SPEED = 2500000.0


class FakeQuest:
    # global list of fake quests. Use it in the app
    devices: List["FakeQuest"] = []

    def __init__(
        self,
        name: str,
        package_names: List[str],
    ) -> None:
        """holds the name and package names of a fake quest2 device

        Args:
            name (str): the name of the quest
            package_names (List[str]): list of package names that will be on the fake quest
        """
        self.name = name
        self.package_names = package_names

    @staticmethod
    def remove_device(name: str) -> bool:
        """remove a fake quest device from the global list

        Args:
            name (str): the name of the fake quest

            Returns:
                bool: True if the device was removed, False if it was not found
        """
        index = get_index_by_device_name(FakeQuest.devices, name)
        if index is None:
            return False
        FakeQuest.devices.pop(index)
        return True

    @staticmethod
    def add_device(name: str, packages: List[str]) -> None:
        """add a fake quest device to the global list

        Args:
            name (str): the name of the fake quest
            packages (List[str]): list of package names that will be on the fake quest
        """
        FakeQuest.devices.append(FakeQuest(name, packages))

    @staticmethod
    def generate_random_packages(max_packages: int = 50) -> List[str]:
        """generates a list of random package names

        Args:
            max_packages (int): the max number of packages to generate. Defaults to 50.

        Returns:
            List[str]: list of randomly generated package names
        """
        package_names = list(
            map(
                lambda x: f"com.oculus.fakeapp{x}",
                range(random.randint(1, max_packages)),
            )
        )
        return package_names

    @staticmethod
    def generate_random_device_name(
        fake_quests: List["FakeQuest"], suffix_name: str = "QUEST"
    ) -> str:
        """generates a random device name

        Args:
            fake_quests (List[FakeQuest]): list of fake quests to check against
            suffix_name (str, optional): the suffix to append to the beginning of the device name. Defaults to "QUEST".

        Returns:
            str: the random device name
        """
        prefix = 1
        while True:
            # append a number to the end of the device name if it already exists
            device_name = f"{suffix_name}-{prefix}"
            try:
                get_device(fake_quests, device_name)
            except LookupError:
                break
            prefix += 1
        return device_name


async def simulate_game_install(
    callback: lib.quest.InstallStatusFunction,
    device_name: str,
    fake_quests: List[FakeQuest],
    apk_dir: lib.utils.ApkPath,
    raise_exception: Exception | None = None,
    total_time_range: Tuple[float, float] = (1.0, 5.0),
) -> None:
    """fake install game function. Simulates the install process

    Args:
        callback (InstallStatusFunction): the callback to recieve updates to
        device_name (str): the name of the selected to device to install to
        fake_quests (List[FakeQuest]): list of fake quests to check against
        apk_dir (ApkPath): contains the apk file path, subpaths and subfiles to be pushed onto the remote device
        raise_exception (Exception, optional): if not None, will raise the exception. Defaults to None.
        total_time_range (Tuple[float, float], optional): the range of time to simulate the install process. Defaults to (1.0, 5.0).

    Raises:
        ValueError: if device_name is empty string
        LookupError: could not find the device in the device list. Possible disconnected Quest device
    """

    if not device_name:
        raise ValueError("No Device selected")
    try:
        device_names = get_device_names(fake_quests)
    except Exception as err:
        raise err
    if not device_name in device_names:
        raise LookupError("Device disconnected. Please reconnect device and re-install")

    # get file stats from apk package
    total_size = random.uniform(1000000.0, 10000000.0)
    formatted_size = lib.utils.format_size(float(total_size))
    apk_name = os.path.split(apk_dir.path)[-1]

    message = f"Installing {apk_name}. Total Size: {formatted_size}"
    callback(message)

    # start install
    # start_time = time.time()
    callback(f"Installing {apk_name} onto {device_name}")
    callback(f"Total size: {formatted_size}")
    callback(f"Starting install of {apk_name} onto {device_name}")
    callback(
        "Installing game this may take several minutes. Please do not disconnect your device"
    )
    await asyncio.sleep(random.uniform(*total_time_range))
    callback(
        "Moving files onto device. This may take a few minutes. Do not disconnect Device"
    )
    if raise_exception is not None:
        raise raise_exception
    await asyncio.sleep(random.uniform(*total_time_range))

    # elapsed_time = time.time() - start_time
    # formatted_time = str(timedelta(seconds=elapsed_time))

    callback(f"{apk_name} has been installed")


async def simulate_game_download(
    callback: dh.StatusUpdateFunction,
    error_callback: dh.ErrorUpdateFunction,
    magnet_data: dh.MagnetData,
    total_time: int,
) -> bool:
    """replicates the deluge.handler.download function

    Args:
        callback (dh.StatusUpdateFunction): a callback handle the torrent update status
        error_callback (dh.ErrorUpdateFunction): a callback to handle any errors
        magnet_data (dh.MagnetData): data about the magnet link
        total_time (int): the total time in seconds to simulate the download

    Returns:
        bool: if successful returns True else False
    """
    for seconds in range(total_time):
        torrent_status = get_torrent_status(seconds, total_time)
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


async def simulate_cleanup(
    path_to_remove: str,
    error_callback: Callable[[str], None],
    force_error: bool,
    wait_time: float = 3.0,
) -> None:
    """simulate the cleanup function in the quest module

    Args:
        path_to_remove (str): the path to remove
        error_callback (_type_): the callback to handle the error
        force_error (bool): if True, will force an error to be raised
        wait_time (float, optional): the time to wait to simulate the path removal. Defaults to 3.0.
    """

    def on_error(func: Callable[[str], None], path: str, exc_info: tuple) -> None:
        """calls the callback by passing the string from the exception into the callback

        Args:
            func (Callable): the function callback to handle the error
            path (str): the path to which the exception was raised
            exc_info (tuple): information about the exception

            read the shutil.rmtree docs for more info
        """
        func(f"Error removing path {path}, reason: {exc_info[1].__str__()})")

    if force_error:
        on_error(error_callback, path_to_remove, (None, OSError("forced error"), None))
    await asyncio.sleep(3)


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
        download_payload_rate = random.uniform(MIN_DOWNLOAD_SPEED, MAX_DOWNLOAD_SPEED)
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


def get_device_names(quests: List[FakeQuest]) -> List[str]:
    """simulate the adblib.adb_interface.get_device_names method

    Returns:
        List[str]: list of fake Quest device names
    """
    quest_names = list(map(lambda quest: quest.name, quests))
    return quest_names


def get_index_by_device_name(fake_quests: List[FakeQuest], name: str) -> int | None:
    """finds the index of the name in the list of fake_quests

    Args:
        name (str): the name of the device to retrieve

    Returns:
        int: if name is matched then index will be an integer otherwise it will return None
    """
    index = next(
        (i for i, fake_quest in enumerate(fake_quests) if fake_quest.name == name), None
    )
    return index


def get_device(quests: List[FakeQuest], name: str) -> FakeQuest:
    """gets the device related to the device name

    Args:
        name (str): the name of the device to retrieve

    Raises:
        LookupError: if no device found then this gets raised

    Returns:
        Quest: the Quest fake object for testing
    """
    matched_quests = list(filter(lambda quest: quest.name == name, quests))
    if not matched_quests:
        raise LookupError("Could not find device with that name")

    # return the first element

    return matched_quests[0]


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
