import os
import logging
from typing import Callable

import adblib.adb_interface as adb
from config import QUEST_OBB_DIRECTORY
from deluge.utils import find_apk_directory_async


_Log = logging.getLogger(__name__)


InstallStatusFunction = Callable[[str], None]


async def install(callback: InstallStatusFunction, device_name: str, path: str) -> None:
    # step 1
    # get the apk file and directories for pushing onto device

    # step 2
    # create a temp path for the apk and push onto device

    # step 3
    # install apk

    # step 4
    # get the package name and create package data dir in OBB dir

    apk_path, apk_sub_paths, apk_filename = await find_apk_directory_async(path)
    if not apk_path:
        raise FileNotFoundError(f"{apk_path} could not be found")
    if not device_name:
        raise ValueError("No Device selected")
    if not device_name in await adb.get_device_names():
        raise LookupError("Device disconnected. Please reconnect device and re-install")
    # local_path = os.path.join(apk_path, apk_filename)
    # copy the apk to the temp directory
    # stdout = await adb.copy_path(device_name, local_path, QUEST_APK_TEMP_DIRECTORY)
    # _Log.info(stdout)
    # run the install command
    # hack way of getting the package_name. I will change this later
    # but for now get a snap shot of the packages on the Quest, install and then check for
    # a new entry and the will be the package_name
    # previous_packages = await adb.get_installed_packages(device_name, ["-3"])
    # previous_packages.sort()
    # # now run the install
    # # quest_temp_apk_path = QUEST_APK_TEMP_DIRECTORY + "/" + apk_filename
    # full_apk_path = os.path.join(apk_path, apk_filename)
    # result_install = await adb.install_apk(device_name, full_apk_path)
    # _Log.info(result_install)
    # new_packages = await adb.get_installed_packages(device_name, ["-3"])
    # new_packages.sort()
    # newly_installed_package = list(set(new_packages) - set(previous_packages))
    # if len(newly_installed_package) == 0:
    #     raise IndexError(
    #         "Could not retrieve Package name. Please remove the Package and try again"
    #     )
    # package_name = newly_installed_package[0]
    # # create a package data path in the OBB directory and push all the contents
    # # into it
    # obb_path = QUEST_OBB_DIRECTORY + "/" + package_name
    # stdout = await adb.make_dir(device_name, obb_path)
    # _Log.info(stdout)
    # for subpath in apk_sub_paths:
    #     full_sub_path = os.path.join(apk_path, subpath)
    #     dest_path = obb_path + "/" + subpath
    #     stdout = await adb.copy_path(device_name, full_sub_path, dest_path)
    #     _Log.info(stdout)
    await callback("Appending apk file name to the full path")
    full_apk_path = os.path.join(apk_path, apk_filename)
    await callback(
        "Installing game this may take several minutes. Please do not disconnect your device"
    )
    await adb.install_apk(device_name, full_apk_path)
    await callback("Game has been installed. Moving to next step...")
    if not adb.path_exists(device_name, QUEST_OBB_DIRECTORY):
        await callback("OBB doesnt exist creating a new data folder")
        adb.make_dir(device_name, QUEST_OBB_DIRECTORY)
    await callback(
        "Moving files onto device. This may take a few minutes. Do not disconnect Device"
    )
    for subpath in apk_sub_paths:
        full_sub_path = os.path.join(apk_path, subpath)
        await adb.copy_path(device_name, full_sub_path, QUEST_OBB_DIRECTORY)
    await callback("Install has completed successfully. Enjoy!")
