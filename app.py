"""
app.py the main module for QuestVRAutoInstaller
"""

import wxasync
import asyncio
import multiprocessing

import wx

from ui.main_frame import MainFrame
from ui.devices_listpanel import DevicesListPanel
from ui.installed_listpanel import InstalledListPanel
from ui.magnets_listpanel import MagnetsListPanel
from ui.dialogs.error_dialog import ErrorDialog
from ui.dialogs.install_progress_dialog import InstallProgressDialog

from deluge.utils import start_deluge_daemon
from deluge.handler import download, MagnetData

from adblib import adb_interface
from adblib.errors import RemoteDeviceError


import lib.config as config
import lib.api
import lib.utils
import lib.quest as quest


class Q2GApp(wxasync.WxAsyncApp):
    # global wxwindow instances
    devices_listpanel: DevicesListPanel = None
    magnets_listpanel: MagnetsListPanel = None
    install_listpanel: InstalledListPanel = None
    install_dialog: InstallProgressDialog = None

    settings: config.Settings = None

    def set_status_text(self, text: str) -> None:
        """sets the text on the main frame statusbar

        Args:
            text (str):
        """
        self.statusbar.SetStatusText(text=text)

    def OnInit(self) -> bool:
        """app has loaded create the main frame

        Returns:
            bool:
        """
        title = f"{config.APP_NAME} - version {config.APP_VERSION}"
        self.frame: MainFrame = MainFrame(parent=None, id=-1, title=title)
        self.frame.Show()
        return super().OnInit()

    def exception_handler(self, err: Exception) -> None:
        """shows a dialog box with error icon can be used within a thread

        Args:
            err (Exception): exception error instance to be processed
        """
        if isinstance(err, lib.api.ApiError):
            error_message = f"{err.message}\n\nCode: {err.status_code}"
        else:
            error_message = err.__str__()
        dialog = ErrorDialog(self.frame, "There was an error!!", error_message)
        dialog.ShowModal()
        dialog.Destroy()

    async def start_download_process(self, **kwargs) -> str:
        """download using the deluge torrent client

        Args:
            callback (StatusUpdateFunction): any updates will be sent to this callback
            error_callback (ErrorUpdateFunction): any errors go to this callback
            magnet_data (MagnetData): extra information about the magnet to be downloaded

        Returns:
            str: "download-error" | "success" | "install-error"
        """

        # check that a device is selected
        if (
            not config.DebugSettings.enabled
            and not self.devices_listpanel.selected_device
        ):
            wx.MessageBox(
                "No device selected. Please connect your Quest Headset into the PC and select it from the Devices List",
                "No Device selected",
                style=wx.ICON_WARNING | wx.OK,
            )
            return

        ok_to_install = await download(**kwargs)
        if not ok_to_install:
            return "download-error"

        if config.Settings.load().download_only:
            # skip the installation but leave the files locally
            return "success"

        magnet_data: MagnetData = kwargs["magnet_data"]
        install_success = await self.start_install_process(magnet_data.download_path)
        if not install_success:
            return "install-error"
        return "success"

    async def start_install_process(self, path: str) -> bool:
        """starts the install process communicates with ADB and pushes any data paths onto
        the obb directory

        Args:
            path (str): the path of the apk package and data path

        Raises:
            Exception: general exception raised

        Returns:
            bool: True if install was successful. False is no install
        """
        self.install_dialog = InstallProgressDialog(self.frame)
        self.install_dialog.Show()
        result = False
        try:
            device_name = self.devices_listpanel.selected_device
            # if not device_name:
            #     raise Exception("No device selected")
            for apk_dir in lib.utils.find_install_dirs(path):
                await quest.install_game(
                    callback=self.on_install_update,
                    device_name=device_name,
                    apk_dir=apk_dir,
                )
        except Exception as err:
            # show the error dialog
            # await asyncio.sleep(0.5)
            self.on_install_update(f"Error: {err.__str__()}. Installation has quit")
        else:
            result = True
            settings = config.Settings.load()
            if settings.remove_files_after_install:
                # delete the torrent files on the local path
                quest.cleanup(
                    path_to_remove=path, error_callback=self.on_install_update
                )
            # reload the package list
            await self.install_listpanel.load(device_name)
            if settings.close_dialog_after_install:
                self.install_dialog.Destroy()
            else:
                self.on_install_update("Installation has completed. Enjoy!!")
        finally:
            return result

    async def on_torrent_update(self, torrent_status: dict) -> None:
        """passes the torrent status onto the update list item function in the magnet listpanel

        Args:
            torrent_status (dict): a dict containing torrent download status
        """
        wx.CallAfter(
            self.magnets_listpanel.update_list_item, torrent_status=torrent_status
        )

    def on_install_update(self, message: str) -> None:
        """update the Progress Dialog textbox from the install process

        Args:
            message (str): the current step in the install process
        """
        if not self.install_dialog:
            return
        self.install_dialog.write(message)

    async def remove_package(self, package_name: str) -> None:
        """communicates with the ADB daemon and uninstalls the package from package name

        Args:
            package_name (str): the name of the package to uninstall
        """
        device_name = self.devices_listpanel.selected_device
        if not device_name:
            return
        try:
            self.frame.SetStatusText(
                f"Removing {package_name} from Device {device_name}"
            )
            await adb_interface.uninstall(device_name, package_name)
            self.frame.SetStatusText("Uninstall was successful")
        except RemoteDeviceError as err:
            self.exception_handler(err)
        except Exception as err:
            asyncio.get_event_loop().call_exception_handler(
                {"message": err.__str__(), "exception": err}
            )
        else:
            # reload the package list
            await self.install_listpanel.load(device_name)
        finally:
            return

    async def check_internet_and_notify(self) -> None:
        result = lib.utils.is_connected_to_internet()
        if result:
            return
        self.exception_handler(
            ConnectionError(
                "Unable to connect to the Internet please enable Wifi.\
                \nLoading in offline mode"
            )
        )


async def main():
    # parse command line arguments
    args = config.parse_args()
    # set the debug flag
    config.DebugSettings.enabled = args.debug
    # load the settings.json
    settings = config.Settings.load()
    # create the data and download path
    config.create_data_paths(download_path=settings.download_path)
    # create the default logger
    config.initalize_logger()
    try:
        daemon = start_deluge_daemon()
    except FileNotFoundError:
        # download and install deluge daemon
        config._Log.error("Unable to locate the Deluge Daemon. Please reinstall Deluge")
        return
    multiprocessing.freeze_support()
    app = Q2GApp()
    asyncio.get_event_loop().set_exception_handler(config.async_log_handler)
    asyncio.get_event_loop().create_task(app.check_internet_and_notify())
    await app.MainLoop()
    daemon.terminate()
    adb_interface.close_adb()


if __name__ == "__main__":
    asyncio.run(main())
