import asyncio
import logging
import os
import time
from datetime import timedelta
from typing import Callable
from dataclasses import dataclass

from adblib import adb_interface
from adblib.errors import RemoteDeviceError
import lib.config
import lib.utils


_Log = logging.getLogger(__name__)


InstallStatusFunction = Callable[[str], None]


@dataclass
class InstallPackage:
    apk_path: str
    apk_sub_directories: str
    apk_filename: str


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
    if lib.config.DebugSettings.enabled:
        obb_path_exists = True
        return not obb_path_exists

    obb_path_exists = adb_interface.path_exists(device_name=device_name, path=obb_path)
    if not obb_path_exists:
        _Log.debug(f"{obb_path} does not exist. Creating new data directory...")
        adb_interface.make_dir(device_name=device_name, path=obb_path)
        _Log.debug(f"{obb_path} created successfully")
    return not obb_path_exists


async def dummy_install_game(
    callback: InstallStatusFunction,
    device_name: str,
    path: str,
    raise_exception: bool,
    time_to_install: float,
) -> InstallPackage:
    """simulates an install process

    Args:
        callback (InstallStatusFunction): the callback to update to
        device_name (str): the name of the device to install to
        path (str): the path of the apk file to install
        raise_exception (bool): if true then a raise exception will be made. This is to test
        time_to_install (float): timeout period before install is complete
        exception handling
    """
    start_time = time.time()
    await callback("Appending apk file name to the full path")
    apk_path = "C:\\Users\\somerandomname\\Games\\somerandomquestgame\\"
    apk_sub_paths = list(
        map(
            lambda _path: os.path.join(apk_path, _path),
            ["random_game_data", "more_random_game_data"],
        )
    )
    apk_filename = os.path.join(apk_path, "random_game.apk")
    install_results = InstallPackage(
        apk_path=apk_path, apk_sub_directories=apk_sub_paths, apk_filename=apk_filename
    )
    asyncio.sleep(0.2)
    await callback(
        "Installing game this may take several minutes. Please do not disconnect your device"
    )
    asyncio.sleep(time_to_install)
    await callback("Game has been installed. Moving to next step...")
    await callback(
        "Moving files onto device. This may take a few minutes. Do not disconnect Device"
    )
    if raise_exception:
        raise RemoteDeviceError("Remote device not responding")

    asyncio.sleep(5)

    elapsed_time = time.time() - start_time
    formatted_time = str(timedelta(seconds=elapsed_time))

    await callback("Install has completed successfully. Enjoy!")


async def install_game(
    callback: InstallStatusFunction, device_name: str, path: str
) -> None:
    """installs the APK file and copies any subdirectories onto the Quest devices OBB path

    Args:
        callback (InstallStatusFunction): the callback to recieve updates to
        device_name (str): the name of the selected to device to install to
        path (str): the path of the app data. Must include APK file!

    Raises:
        FileNotFoundError: if no apk file can be found
        ValueError: if device_name is empty string
        LookupError: could not find the device in the device list. Possible disconnected Quest device
    """
    # step 1
    # get the apk file and directories for pushing onto device

    # step 2
    # install apk

    # step 3
    # get the package name and create package data dir in OBB dir

    apk_path, apk_sub_paths, apk_filename = await lib.utils.find_apk_directory_async(
        path
    )
    if not apk_path:
        raise FileNotFoundError(f"{apk_path} could not be found")
    if not device_name:
        raise ValueError("No Device selected")
    if not device_name in await adb_interface.get_device_names():
        raise LookupError("Device disconnected. Please reconnect device and re-install")
    # local_path = os.path.join(apk_path, apk_filename)
    # copy the apk to the temp directory
    # stdout = await adb_interface.copy_path(device_name, local_path, QUEST_APK_TEMP_DIRECTORY)
    # _Log.info(stdout)
    # run the install command
    # hack way of getting the package_name. I will change this later
    # but for now get a snap shot of the packages on the Quest, install and then check for
    # a new entry and the will be the package_name
    # previous_packages = await adb_interface.get_installed_packages(device_name, ["-3"])
    # previous_packages.sort()
    # # now run the install
    # # quest_temp_apk_path = QUEST_APK_TEMP_DIRECTORY + "/" + apk_filename
    # full_apk_path = os.path.join(apk_path, apk_filename)
    # result_install = await adb_interface.install_apk(device_name, full_apk_path)
    # _Log.info(result_install)
    # new_packages = await adb_interface.get_installed_packages(device_name, ["-3"])
    # new_packages.sort()
    # newly_installed_package = list(set(new_packages) - set(previous_packages))
    # if len(newly_installed_package) == 0:
    #     raise IndexError(
    #         "Could not retrieve Package name. Please remove the Package and try again"
    #     )
    # package_name = newly_installed_package[0]
    # # create a package data path in the OBB directory and push all the contents
    # # into it
    # obb_path = lib.config.QUEST_OBB_DIRECTORY + "/" + package_name
    # stdout = await adb_interface.make_dir(device_name, obb_path)
    # _Log.info(stdout)
    # for subpath in apk_sub_paths:
    #     full_sub_path = os.path.join(apk_path, subpath)
    #     dest_path = obb_path + "/" + subpath
    #     stdout = await adb_interface.copy_path(device_name, full_sub_path, dest_path)
    #     _Log.info(stdout)
    await callback("Appending apk file name to the full path")
    full_apk_path = os.path.join(apk_path, apk_filename)
    await callback(
        "Installing game this may take several minutes. Please do not disconnect your device"
    )
    await adb_interface.install_apk(device_name, full_apk_path)
    await callback("Game has been installed. Moving to next step...")
    if not adb_interface.path_exists(device_name, lib.config.QUEST_OBB_DIRECTORY):
        await callback("OBB doesnt exist creating a new data folder")
        adb_interface.make_dir(device_name, lib.config.QUEST_OBB_DIRECTORY)
    await callback(
        "Moving files onto device. This may take a few minutes. Do not disconnect Device"
    )
    for subpath in apk_sub_paths:
        full_sub_path = os.path.join(apk_path, subpath)
        await adb_interface.copy_path(
            device_name, full_sub_path, lib.config.QUEST_OBB_DIRECTORY
        )
    await callback("Install has completed successfully. Enjoy!")
