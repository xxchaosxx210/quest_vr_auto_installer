import logging
import os
import queue
import shutil
import threading
from typing import Callable, List
from dataclasses import dataclass

import adblib.adb_interface as adb_interface
import lib.config
import lib.utils
import lib.debug as debug


InstallStatusFunction = Callable[[str], None]

_Log = logging.getLogger()


@dataclass
class InstallPackage:
    apk_path: str
    apk_sub_directories: List[str]
    apk_filename: str


"""I want a thread to monitor the selected device by calling the adb_interface.get_devices_names, every 3 seconds
 and seeing if the selected device is still connected. 
 If it is not connected then I want to notify the parent thread that it has been disconnect"""


class MonitorSelectedDevice(threading.Thread):
    def __init__(self, callback: Callable[[dict], None], debug_mode: bool) -> None:
        """
        callback should take a dict properties:

        {"event": "device-selected", "device-name": str}
        {"event": "device-disconnected"}
        {"event": "error", "exception": Exception}

        Args:
            callback (Callable[[dict], None]): check above for the callback properties
        """
        super().__init__(name="device-monitor", daemon=True)
        self._queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._callback = callback
        self._debug_mode = debug_mode
        self._selected_device = ""
        self._lock = threading.Lock()

    def run(self) -> None:
        while self._stop_event.is_set() is False:
            try:
                msg: dict = self._queue.get(timeout=3, block=True)
            except queue.Empty:
                pass
            else:
                # process message
                if msg["request"] == "stop":
                    self._stop_event.set()
                elif msg["request"] == "selected-device":
                    self.set_selected_device(msg["device-name"])
                    self._callback(
                        {
                            "event": "device-selected",
                            "device-name": self.get_selected_device(),
                        }
                    )
            finally:
                # check if a device is selected which would be a non empty string
                # if a device is selected then check if it is in the returned device names list
                if not self.get_selected_device():
                    continue
                device_names = self.get_device_names()
                if (
                    device_names is not None
                    and self.get_selected_device() not in device_names
                ):
                    _Log.debug(f"{self.get_selected_device()} is not connected")
                    self.set_selected_device("")
                    self._callback({"event": "device-disconnected"})

    def get_device_names(self) -> List[str] | None:
        """
        this handles the debug and normal mode for getting the device names also handles any exceptions

        Returns:
            List[str]: list of device names if exception then None
        """
        device_names: List[str] | None = None
        if self._debug_mode:
            device_names = debug.get_device_names(debug.fake_quests)
            return device_names
        try:
            device_names = adb_interface.sync_get_device_names()
        except Exception as err:
            _Log.error(err.__str__() + " - MonitorSelectedDevice.get_device_names()")
            self._callback({"event": "error", "exception": err})
            device_names = None
        finally:
            return device_names

    def send_message_no_block(self, message: dict) -> None:
        """sends a message to the thread without non blocking

        message requests:
        {"request": "stop"}
        {"request": "selected-device", "device-name": str}

        Args:
            message (dict): see above for message requests
        """
        self._queue.put_nowait(message)

    def send_message_and_wait(self, message: dict) -> None:
        """sends a message to the thread without blocking

        message requests:
        {"request": "stop"}
        {"request": "selected-device", "device-name": str}

        Args:
            message (dict): see above for message requests
        """
        self._queue.put(message)

    def get_selected_device(self) -> str:
        with self._lock:
            return self._selected_device

    def set_selected_device(self, device_name: str) -> None:
        with self._lock:
            self._selected_device = device_name

    def stop(self) -> None:
        self._queue.put({"request": "stop"})
        self.join()


def cleanup(path_to_remove: str, error_callback) -> None:
    def on_error(func: Callable, path: str, exc_info: tuple) -> None:
        error_callback(exc_info[1].__str__())

    shutil.rmtree(path_to_remove, ignore_errors=False, onerror=on_error)


def create_obb_path(
    device_name: str, obb_path: str = lib.config.QUEST_OBB_DIRECTORY
) -> bool:
    """creates an OBB data directory on remote device if path doesnt exist

    Args:
        device_name (str): the name of the quest device
        obb_path (str): the data directory for storing game information

    Returns:
        bool: True if new directory created or False if no directory was created
    """

    obb_path_exists = adb_interface.path_exists(device_name=device_name, path=obb_path)
    if not obb_path_exists:
        _Log.debug(f"{obb_path} does not exist. Creating new data directory...")
        adb_interface.make_dir(device_name=device_name, path=obb_path)
        _Log.debug(f"{obb_path} created successfully")
    return not obb_path_exists


async def install_game(
    callback: InstallStatusFunction, device_name: str, apk_dir: lib.utils.ApkPath
) -> None:
    """installs the APK file and copies any subdirectories onto the Quest devices OBB path

    Args:
        callback (InstallStatusFunction): the callback to recieve updates to
        device_name (str): the name of the selected to device to install to
        apk_dir (ApkPath): contains the apk file path, subpaths and subfiles to be pushed onto the remote device

    Raises:
        FileNotFoundError: if no apk file can be found
        ValueError: if device_name is empty string
        LookupError: could not find the device in the device list. Possible disconnected Quest device
    """
    if not os.path.exists(apk_dir.path):
        raise FileNotFoundError(f"{apk_dir.path} could not be found")
    if not device_name:
        raise ValueError("No Device selected")
    try:
        device_names = await adb_interface.get_device_names()
    except Exception as err:
        raise err
    if not device_name in device_names:
        raise LookupError("Device disconnected. Please reconnect device and re-install")

    # get file stats from apk package
    total_size = lib.utils.get_folder_size(apk_dir.root)
    formatted_size = lib.utils.format_size(float(total_size))
    apk_name = os.path.split(apk_dir.path)[-1]
    message = f"Installing {apk_name}. Total Size: {formatted_size}"

    callback(message)

    await adb_interface.install_apk(device_name, apk_path=apk_dir.path)
    callback(
        f"Copying data files onto {device_name}. Do not disconnect device. This may take several minutes depending on the size"
    )
    if not adb_interface.path_exists(device_name, lib.config.QUEST_OBB_DIRECTORY):
        adb_interface.make_dir(device_name, lib.config.QUEST_OBB_DIRECTORY)
    # copy the sub data folders into the remote OBB path
    for subpath in apk_dir.data_dirs:
        await adb_interface.copy_path(
            device_name, subpath, lib.config.QUEST_OBB_DIRECTORY
        )
    # copy the sub files into the remote OBB directory
    for subfile in apk_dir.file_paths:
        await adb_interface.copy_path(
            device_name=device_name,
            local_path=subfile,
            destination_path=lib.config.QUEST_OBB_DIRECTORY,
        )
    callback(f"{apk_name} has been installed.\n")
