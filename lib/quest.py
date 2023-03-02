import logging
import os
import shutil
from typing import Callable, List
from dataclasses import dataclass

from adblib import adb_interface
import lib.config
import lib.utils


_Log = logging.getLogger()


InstallStatusFunction = Callable[[str], None]


@dataclass
class InstallPackage:
    apk_path: str
    apk_sub_directories: List[str]
    apk_filename: str


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
