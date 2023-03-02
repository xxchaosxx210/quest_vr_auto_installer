"""
main.py the main module for QuestVRAutoInstaller
"""

import asyncio
import multiprocessing
import sys


import lib.config as config
from lib.debug import DebugState
from deluge.utils import start_deluge_daemon
from adblib import adb_interface
from lib.settings import Settings
from q2gapp import Q2GApp


async def _main():
    # parse command line arguments
    args = config.parse_args()
    # set the debug flag
    DebugState.enabled = args.debug
    # load the settings.json
    settings = Settings.load()
    # create the data and download path
    config.create_data_paths(download_path=settings.download_path)
    # create the default logger
    config.initalize_logger()
    try:
        daemon = start_deluge_daemon()
    except FileNotFoundError:
        # download and install deluge daemon
        sys.exit("Unable to locate the Deluge Daemon. Please reinstall Deluge Torrent")
    multiprocessing.freeze_support()
    app = Q2GApp()
    # catch any unhandled exceptions in the event loop
    asyncio.get_event_loop().set_exception_handler(config.async_log_handler)
    # check for an internet connection, notify user to turn back on
    asyncio.get_event_loop().create_task(app.check_internet_and_notify())
    await app.MainLoop()
    # cleanup
    daemon.terminate()
    adb_interface.close_adb()


if __name__ == "__main__":
    asyncio.run(_main())
