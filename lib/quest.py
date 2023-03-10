import asyncio
import logging
import os
import queue
import shutil
import threading
from typing import Callable, List

import adblib.adb_interface as adb_interface
import lib.config
import lib.utils
import lib.debug as debug


InstallStatusFunction = Callable[[str], None]

_Log = logging.getLogger()


class MonitorQuestDevices(threading.Thread):
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
        self.__selected_device = ""
        # keep the device selection thread safe
        self.__device_selection_lock = threading.Lock()

    def __process_message_request(self, msg: dict) -> bool:
        """handles the message request from the queue

        Args:
            msg (dict): should be a dict with a "request" key

            request: "stop" - stops the thread,
                     "selected-device" - sets the selected device,
                     "device-names-reset" - resets the prev_device_names

        Returns:
            bool: True if the request was handled
        """
        if msg["request"] == "stop":
            self._stop_event.set()
            return True
        elif msg["request"] == "selected-device":
            self.__set_selected_device(msg["device-name"])
            self._callback(
                {
                    "event": "device-selected",
                    "device-name": self.get_selected_device(),
                }
            )
            return True
        elif msg["request"] == "device-names-reset":
            self._prev_device_names.clear()
            return True
        else:
            return False

    def run(self) -> None:
        # start a new event loop for this thread
        self._event_loop = asyncio.new_event_loop()

        self._prev_device_names: List[str] = []
        while self._stop_event.is_set() is False:
            try:
                msg: dict = self._queue.get(timeout=3, block=True)
            except queue.Empty:
                pass
            else:
                self.__process_message_request(msg)
            finally:
                # if selected_device is non empty string then check device is in list
                # retrieved from get_device_names(). Also store a prev_device_names
                # and compare prev_device_names to current_device_names using sets
                device_names = self.get_device_names()
                if device_names is not None:
                    self._handle_device_names_changed(device_names)
                if not self.get_selected_device():
                    continue
                if (
                    device_names is not None
                    and self.get_selected_device() not in device_names
                ):
                    _Log.debug(f"{self.get_selected_device()} is not connected")
                    self.__set_selected_device("")
                    self._callback({"event": "device-disconnected"})
        self._event_loop.close()
        del self._event_loop

    def _handle_device_names_changed(self, device_names: List[str]) -> bool:
        """checks if the device_names match with self._prev_device_names if not then
        a device-names-changed event is sent to the callback

        Args:
            device_names (List[str]): the list of the device names returned from the ADB daemon

        Returns:
            bool: returns True if the device_names have changed
        """
        if device_names is None or self._prev_device_names == device_names:
            return False
        _Log.info("device names have changed")
        self._prev_device_names = device_names
        self._callback({"event": "device-names-changed", "device-names": device_names})
        return True

    def get_device_names(self) -> List[str] | None:
        """
        this handles the debug and normal mode for getting the device names
        also handles any exceptions

        Returns:
            List[str]: list of device names if exception then None
        """
        device_names: List[str] | None = None
        if self._debug_mode:
            device_names = debug.get_device_names(debug.FakeQuest.devices)
            return device_names
        try:
            device_names = adb_interface.get_device_names()
        except Exception as err:
            _Log.error(err.__str__() + " - MonitorSelectedDevice.get_device_names()")
            self._callback({"event": "error", "exception": err})
            device_names = None
        finally:
            if device_names is not None and not self._debug_mode:
                # filter out the non quest devices
                quest_device_names = filter_quest_device_names(device_names)
                return quest_device_names
            # debug mode no need to filter
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
        """gets the selected device

        Returns:
            str: if a device is selected then the return value will be a non empty string
        """
        with self.__device_selection_lock:
            return self.__selected_device

    def __set_selected_device(self, device_name: str) -> None:
        with self.__device_selection_lock:
            self.__selected_device = device_name

    def stop(self) -> None:
        """stops the running thread"""
        self._queue.put({"request": "stop"})
        self.join()

    def refresh_device_list(self) -> None:
        """resets the prev_device_names.

        I added this when a device list dialog is opened it gets called within its EVT_SHOW event
        in wxpython but can be called within any GUI framework.
        a hackish way and I need to think of a better way less confusing.

        This basically fires off another device names changed event to the callback handler

        """
        self._queue.put_nowait({"request": "device-names-reset"})


async def cleanup(path_to_remove: str, error_callback) -> None:
    """removes a directory and all its contents

    if any errors occur then the error_callback is called with the error string
    """

    def on_error(func: Callable, path: str, exc_info: tuple) -> None:
        """calls the callback by passing the string from the exception into the callback

        Args:
            func (Callable): the function callback to handle the error
            path (str): the path to which the exception was raised
            exc_info (tuple): information about the exception

            read the shutil.rmtree docs for more info
        """
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


def is_quest_device(device_name: str) -> bool:
    """checks if the device is a quest device

    Args:
        device_name (str): the name of the device to check

    Returns:
        bool: True if the device is a quest device
    """
    model = adb_interface.get_device_model(device_name=device_name)
    model = model.strip()
    is_quest = model == "Quest 2"
    if not is_quest:
        pass
    return is_quest


def filter_quest_device_names(device_names: List[str]) -> List[str]:
    """returns a new list of quest devices from the device_names list

    Args:
        device_names (List[str]): list of device names

    Returns:
        List[str]: list of quest devices
    """
    return [device for device in device_names if is_quest_device(device)]


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
        device_names = await adb_interface.async_get_device_names()
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


async def async_get_newly_installed_packages(
    device_name: str, original_packages: List[str]
) -> List[str]:
    """compares original list of packages with most recent and returns the difference
    hackish way of finding recently installed package names

    Args:
        device_name (str): the name of the Quest device
        original_packages (List[str]): the list of packages before the new packages were installed

    Returns:
        Set[str]: returns a set of newly installed packages
    """
    new_packages = await adb_interface.get_installed_packages(device_name)
    original_set = set(original_packages)
    new_set = set(new_packages)
    packages = new_set - original_set
    return list(packages)
