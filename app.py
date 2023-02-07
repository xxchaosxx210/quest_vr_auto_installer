"""
app.py the main module for QuestVRAutoInstaller
"""

import wxasync
import asyncio
import logging
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
import lib.quest_installer as quest_installer


logging.basicConfig(level=logging.INFO)
_Log = logging.getLogger(__name__)


class Q2GApp(wxasync.WxAsyncApp):
    # global wxwindow instances
    devices_listpanel: DevicesListPanel = None
    magnets_listpanel: MagnetsListPanel = None
    install_listpanel: InstalledListPanel = None
    install_dialog: InstallProgressDialog = None

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
        dialog = ErrorDialog(self.frame, "There was an error!!", err.__str__())
        dialog.ShowModal()
        dialog.Destroy()

    async def start_download_process(self, **kwargs) -> None:
        """download using the deluge torrent client

        Args:
            callback (StatusUpdateFunction): any updates will be sent to this callback
            error_callback (ErrorUpdateFunction): any errors go to this callback
            magnet_data (MagnetData): extra information about the magnet to be downloaded
        """
        ok_to_install = await download(**kwargs)
        if not ok_to_install:
            return

        magnet_data: MagnetData = kwargs["magnet_data"]
        await self.start_install_process(magnet_data.download_path)

    async def start_install_process(self, path: str):
        """starts the install process communicates with ADB and pushes any data paths onto
        the obb directory

        Args:
            path (str): the path of the apk package and data path

        Raises:
            Exception: general exception raised
        """
        self.install_dialog = InstallProgressDialog(self.frame)
        self.install_dialog.Show()
        try:
            device_name = self.devices_listpanel.selected_device
            if not device_name:
                raise Exception("No device selected")
            await quest_installer.install(
                callback=self.on_install_update,
                device_name=device_name,
                path=path,
            )
        except Exception as err:
            # show the error dialog
            self.exception_handler(err)
        else:
            # reload the package list
            await self.install_listpanel.load(device_name)
        finally:
            self.install_dialog.Destroy()
            self.install_dialog = None

    async def on_torrent_update(self, torrent_status: dict) -> bool:
        wx.CallAfter(
            self.magnets_listpanel.update_list_item, torrent_status=torrent_status
        )

    async def on_install_update(self, message: str) -> None:
        """update from the install process

        Args:
            message (str): the current step in the install process
        """
        if not self.install_dialog:
            return
        await self.install_dialog.write(message)

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


async def main():
    config.create_data_paths()
    daemon = start_deluge_daemon()
    multiprocessing.freeze_support()
    app = Q2GApp()
    await app.MainLoop()
    daemon.terminate()


if __name__ == "__main__":
    asyncio.run(main())
