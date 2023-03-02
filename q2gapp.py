import asyncio
import logging
import traceback

import wx
import wxasync


import qvrapi.api
import lib.utils
import lib.config as config
import lib.quest
import lib.tasks
import ui.utils
import adblib.adb_interface as adb_interface
import deluge.handler
import lib.debug as debug
from adblib.errors import RemoteDeviceError
from qvrapi.schemas import LogErrorRequest
from lib.settings import Settings


from ui.frames.main_frame import MainFrame
from ui.panels.installed_listpanel import InstalledListPanel
from ui.panels.magnets_listpanel import MagnetsListPanel
from ui.dialogs.error_dialog import ErrorDialog
from ui.dialogs.install_progress_dialog import InstallProgressDialog
from ui.dialogs.device_list_dialog import open_device_selection_dialog


_Log = logging.getLogger()


class Q2GApp(wxasync.WxAsyncApp):
    # global wxwindow instances
    magnets_listpanel: MagnetsListPanel | None = None
    install_listpanel: InstalledListPanel | None = None
    install_dialog: InstallProgressDialog | None = None

    selected_device: str = ""

    # store the global settings
    settings: Settings | None = None

    # online mode flag
    online_mode: bool = False

    # debug mode
    debug_mode: bool = False

    def __init__(self, debug_mode: bool, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.debug_mode = debug_mode

    def set_selected_device(self, device_name: str) -> None:
        """set the selected device name and load the device packages

        Args:
            device_name (str): the name of the device
        """
        self.selected_device = device_name
        if not self.selected_device:
            if self.install_listpanel is not None:
                self.install_listpanel.listctrl.DeleteAllItems()
            return
        self.frame.SetStatusText(f"Device: {device_name}", 1)
        if self.install_listpanel is None:
            return
        try:
            lib.tasks.check_task_and_create(
                self.install_listpanel.load, device_name=device_name
            )
        except lib.tasks.TaskIsRunning:
            pass

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

    def create_download_task(self, magnet_data: deluge.handler.MagnetData) -> None:
        """create the download task and store it in the global install

        Args:
            magnet_data (MagnetData):
        """
        try:
            lib.tasks.check_task_and_create(
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
        with ErrorDialog(
            parent=self.frame,
            title="There was an error!!",
            message=error_message,
            err=err,
            disable_send=False,
        ) as dialog:
            dialog.ShowModal()

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
        tb_string = "\n".join(traceback.format_exception(err))
        error_request = LogErrorRequest(
            type=str(err), uuid=uuid, exception=exception, traceback=tb_string
        )
        try:
            lib.tasks.check_task_and_create(send_error, _error_request=error_request)
        except lib.tasks.TaskIsRunning as err:
            self.exception_handler(err=err)

    async def start_download_process(
        self,
        callback: deluge.handler.StatusUpdateFunction,
        error_callback: deluge.handler.ErrorUpdateFunction,
        magnet_data: deluge.handler.MagnetData,
    ) -> None:
        """download using the deluge torrent client

        2 parts to this function: download part and install part

        basically using deluge to download the torrent files and then...
        using adb to install the apk along with its data files

        Args:
            callback (StatusUpdateFunction): any updates will be sent to this callback
            error_callback (ErrorUpdateFunction): any errors go to this callback
            magnet_data (MagnetData): extra information about the magnet to be downloaded
        """

        # check that a device is selected
        if not self.debug_mode and not self.selected_device:
            wx.MessageBox(
                "No device selected. Please connect your Quest Headset into the PC and select it from the Devices List",
                "No Device selected",
                style=wx.ICON_WARNING | wx.OK,
            )
            return

        # start the download task

        if self.debug_mode:
            try:
                ok_to_install = await debug.simulate_game_download(
                    callback=callback,
                    error_callback=error_callback,
                    magnet_data=magnet_data,
                    total_time=2,
                )
            except Exception as err:
                self.exception_handler(err=err)
                return
        else:
            ok_to_install = await deluge.handler.download(
                callback=callback,
                error_callback=error_callback,
                magnet_data=magnet_data,
            )

        settings = Settings.load()

        # check if user wants to continue to install step and make sure that download went ok

        if not settings.download_only and ok_to_install:
            await self.start_install_process(magnet_data.download_path)

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

        # show the progress dialog. i might change this to a wx.ProgressDialog

        self.install_dialog = InstallProgressDialog(self.frame)
        self.install_dialog.Show()

        if not self.selected_device:
            ui.utils.show_error_message("No Device selected. Cannot install")
            return False
        try:
            if self.debug_mode:
                # gets some fake files and a fake apk filename
                apk_path = debug.generate_apk_path_object(path)
                await debug.simulate_game_install(
                    callback=self.on_install_update,
                    device_name=self.selected_device,
                    apk_dir=apk_path,
                    raise_exception=None,
                )
            else:
                # loop through all the sub directories searching for apk files
                # for every apk file found copy the sub folders to the OBB directory
                # on the Quest device
                for apk_dir in lib.utils.find_install_dirs(path):
                    await lib.quest.install_game(
                        callback=self.on_install_update,
                        device_name=self.selected_device,
                        apk_dir=apk_dir,
                    )
        except Exception as err:
            self.on_install_update(f"Error: {err.__str__()}. Installation has quit")
            self.exception_handler(err)
            return False
        else:
            settings = Settings.load()
            # check no debug mode and remove files after install
            if not self.debug_mode and settings.remove_files_after_install:
                # delete the torrent files on the local path
                lib.quest.cleanup(
                    path_to_remove=path, error_callback=self.on_install_update
                )

            # check listpanel exists and reload the package listctrl

            if self.install_listpanel is not None:
                await self.install_listpanel.load(self.selected_device)

            # close install dialog?

            if settings.close_dialog_after_install:
                self.install_dialog.Destroy()
            else:
                # install went ok. Update statustext
                self.on_install_update("Installation has completed. Enjoy!!")
                wx.CallAfter(
                    self.frame.SetStatusText, text="Installation has completed. Enjoy!"
                )
        return True

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

        if not self.selected_device:
            return

        # dont want to upset mypy. check the listpanel exists
        # then disable the package listctrl while removing

        if self.install_listpanel is not None:
            self.install_listpanel.disable_list()

        # notify the user removing the package

        progress = ui.utils.load_progress_dialog(
            self.frame,
            "Removing Package",
            f"Removing {package_name} from Device {self.selected_device}",
        )
        progress.Pulse()
        try:
            await adb_interface.uninstall(self.selected_device, package_name)
        except RemoteDeviceError as err:
            self.exception_handler(err)
        except Exception as err:
            asyncio.get_event_loop().call_exception_handler(
                {"message": err.__str__(), "exception": err}
            )
        else:
            self.frame.SetStatusText("Uninstall was successful")

            # reload the new package list into package listctrl

            if self.install_listpanel is not None:
                await self.install_listpanel.load(self.selected_device)
        finally:
            progress.Destroy()

            # re-enable the package lisctrl

            if self.install_listpanel is not None:
                self.install_listpanel.enable_list()

    async def check_internet_and_notify(self) -> None:
        """
        checks the internet connectivity on the system
        """
        result = lib.utils.is_connected_to_internet()
        if result:
            return
        self.exception_handler(
            ConnectionError(
                "Unable to connect to the Internet please enable Wifi.\
                \nLoading in offline mode"
            )
        )

    async def load_resources(self) -> None:
        """
        Loads the games and starts the ADB daemon, then prompts the User to select a device
        """
        progress = ui.utils.load_progress_dialog(
            self.frame, config.APP_NAME, "Loading, Please wait..."
        )
        progress.Pulse()

        # start the tasks

        load_games_task = asyncio.create_task(self.load_games())
        load_adb_task = asyncio.create_task(adb_interface.start_adb())

        # check for any errors within the tasks

        exceptions = await asyncio.gather(
            load_adb_task, load_games_task, return_exceptions=True
        )

        for exception in exceptions:
            if isinstance(exception, Exception):
                self.exception_handler(exception)

        # destroy the progress dialog and sleep for half a second to allow the dialog to destroy
        # before displaying another dialog to ask the user to select a quest device

        progress.Destroy()
        await asyncio.sleep(0.5)
        await self.prompt_user_for_device()

    async def load_games(self) -> None:
        """
        start a new task retrieving the magnet games from the backend server
        """
        await asyncio.sleep(0.1)
        if self.magnets_listpanel is None:
            return
        await asyncio.create_task(self.magnets_listpanel.load_magnets_from_api())

    async def prompt_user_for_device(self) -> None:
        """
        loads the device selection dialog and retrieves a selected device to use
        for installing the games to
        """
        result, selected_device = await open_device_selection_dialog(
            self.frame,
            wx.ID_ANY,
            "Select a Device to install to",
            wx.DEFAULT_DIALOG_STYLE,
        )
        if result != wx.OK and result != 0:
            raise ValueError("Dialog did not return a wx.OK or Close id")
        if selected_device and self.install_listpanel is not None:
            self.set_selected_device(selected_device)
