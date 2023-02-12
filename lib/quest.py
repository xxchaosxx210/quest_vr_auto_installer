import logging

import adblib
import lib.config


_Log = logging.getLogger(__name__)


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

    obb_path_exists = adblib.adb_interface.path_exists(
        device_name=device_name, path=obb_path
    )
    if not obb_path_exists:
        _Log.debug(f"{obb_path} does not exist. Creating new data directory...")
        adblib.adb_interface.make_dir(device_name=device_name, path=obb_path)
        _Log.debug(f"{obb_path} created successfully")
    return not obb_path_exists
