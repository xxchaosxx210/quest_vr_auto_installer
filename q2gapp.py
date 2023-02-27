import asyncio

import wx
import wxasync


import qvrapi.api
import lib.utils
import lib.config as config
import lib.quest as quest
import lib.tasks
import adblib.adb_interface as adb_interface
from deluge.handler import download, MagnetData
from adblib.errors import RemoteDeviceError
from qvrapi.schemas import LogErrorRequest
from lib.settings import Settings
from lib.debug_settings import Debug

from ui.frames.main_frame import MainFrame
from ui.panels.devices_listpanel import DevicesListPanel
from ui.panels.installed_listpanel import InstalledListPanel
from ui.panels.magnets_listpanel import MagnetsListPanel
from ui.dialogs.error_dialog import ErrorDialog
from ui.dialogs.install_progress_dialog import InstallProgressDialog


class Q2GApp(wxasync.WxAsyncApp):
    # global wxwindow instances
    devices_listpanel: DevicesListPanel | None = None
    magnets_listpanel: MagnetsListPanel | None = None
    install_listpanel: InstalledListPanel | None = None
    install_dialog: InstallProgressDialog | None = None

    # store the global settings
    settings: Settings | None = None

    # online mode flag
    online_mode: bool = False

    def set_mode(self, mode: bool) -> None:
        """sets whether the app is in online or offline mode
        this is dependant on the network connection

        Args:
            mode (bool): True if online or false if not
        """
        self.online_mode = mode
        if mode == True:
            title = f"{self.title}\t(Online)"
        else:
            title = f"{self.title}\t(Offline)"
        wx.CallAfter(self.frame.SetTitle, title=title)

    def create_download_task(self, magnet_data: MagnetData) -> None:
        """create the download task and store it in the global install

        Args:
            magnet_data (MagnetData):
        """
        try:
            lib.tasks.create_install_task(
                self.start_download_process,
                callback=self.on_torrent_update,
                error_callback=self.exception_handler,
                magnet_data=magnet_data,
            )
        except lib.tasks.TaskIsRunning as err:
            wx.MessageBox(err.__str__(), "Game already installing")

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
        self.title = f"{config.APP_NAME} - version {config.APP_VERSION}"
        self.frame: MainFrame = MainFrame(parent=None, id=-1, title=self.title)
        self.frame.Show()
        return super().OnInit()

    def exception_handler(self, err: Exception) -> None:
        """shows a dialog box with error icon can be used within a thread

        Args:
            err (Exception): exception error instance to be processed
        """
        if isinstance(err, qvrapi.api.ApiError):
            error_message = f"{err.message}\n\nCode: {err.status_code}"
        else:
            error_message = err.__str__()
        dialog = ErrorDialog(
            self.frame,
            "There was an error!!",
            error_message,
            err=err,
            disable_send=False,
        )
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return

        # User clicked the send error button. Send exception to the database

        async def send_error(_error_request: LogErrorRequest) -> None:
            try:
                await qvrapi.api.post_error(_error_request)
            except Exception as _err:
                wx.MessageBox(f"Unable to send. Reason: {str(_err)}", "Error!")

        uuid = Settings.load().uuid
        if hasattr(err, "args"):
            exception = "".join(err.args)
        elif hasattr(err, "message"):
            exception = err.message
        else:
            exception = str(err)
        error_request = LogErrorRequest(
            type=str(err), uuid=uuid, exception=exception, traceback=""
        )
        try:
            lib.tasks.create_log_error_task(send_error, _error_request=error_request)
        except lib.tasks.TaskIsRunning:
            pass

    async def start_download_process(self, **kwargs) -> None:
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
            not Debug.enabled
            and self.devices_listpanel is not None
            and not self.devices_listpanel.selected_device
        ):
            wx.MessageBox(
                "No device selected. Please connect your Quest Headset into the PC and select it from the Devices List",
                "No Device selected",
                style=wx.ICON_WARNING | wx.OK,
            )
            return

        ok_to_install = await download(**kwargs)

        settings = Settings.load()

        if not settings.download_only and ok_to_install:
            # start the install process
            magnet_data: MagnetData = kwargs["magnet_data"]
            install_success = await self.start_install_process(
                magnet_data.download_path
            )
            if not install_success:
                raise ValueError("Installation was unsuccessful")

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
        # set the return value to False. Set to True if everything went ok
        return_value = False
        if self.devices_listpanel is None:
            return return_value
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
            return_value = True
            settings = Settings.load()
            if settings.remove_files_after_install:
                # delete the torrent files on the local path
                quest.cleanup(
                    path_to_remove=path, error_callback=self.on_install_update
                )
            # reload the package list
            if self.install_listpanel is not None:
                await self.install_listpanel.load(device_name)
            if settings.close_dialog_after_install:
                self.install_dialog.Destroy()
            else:
                self.on_install_update("Installation has completed. Enjoy!!")
        finally:
            return return_value

    async def on_torrent_update(self, torrent_status: dict) -> None:
        """passes the torrent status onto the update list item function in the magnet listpanel

        Args:
            torrent_status (dict): a dict containing torrent download status
        """
        if self.magnets_listpanel is not None:
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
        if (
            self.devices_listpanel is None
            or self.devices_listpanel.selected_device == ""
        ):
            return
        device_name = self.devices_listpanel.selected_device
        if self.install_listpanel is not None:
            self.install_listpanel.disable_list()
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
            if self.install_listpanel is not None:
                await self.install_listpanel.load(device_name)
        finally:
            if self.install_listpanel is not None:
                self.install_listpanel.enable_list()
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
