import asyncio
import logging
import webbrowser
from typing import List

import wx
import wxasync
from wakepy import keepawake

import lib.utils
import lib.config as config
import lib.tasks
import lib.debug as debug
import lib.quest
import ui.utils
import api.client
import api.schemas
import api.urls
import deluge.handler
import adblib.adb_interface as adb_interface
from lib.settings import Settings
from adblib.errors import RemoteDeviceError, UnInstallError
from api.schemas import LogErrorRequest

import ui.dialogs.device_list as dld
import ui.dialogs.update as update_dialog
from ui.frames.main_frame import MainFrame
from ui.panels.installed_listpanel import InstalledListPanel
from ui.panels.magnets_listpanel import MagnetsListPanel
from ui.dialogs.error import ErrorDlg
from ui.dialogs.install_progress import InstallProgressDlg


_Log = logging.getLogger()


class QuestCaveApp(wxasync.WxAsyncApp):
    # global wxwindow instances
    magnets_listpanel: MagnetsListPanel | None = None
    install_listpanel: InstalledListPanel | None = None
    install_dialog: InstallProgressDlg | None = None

    # store the global settings
    settings: Settings | None = None

    # online mode flag
    online_mode: bool = False

    # global debug mode flag
    debug_mode: bool = False
    # gloabl skip flag
    skip: bool = False
    # local_host
    local_host: bool = False

    def on_device_event(self, event: dict) -> None:
        """handles the device events. Update GUI

        Args:
            event (dict): the event message
        """
        try:
            if event["event"] == "device-selected":
                device_name = event["device-name"]
                message = "Device: "
                if not device_name:
                    message += "Not Selected"
                else:
                    message += device_name
                wx.CallAfter(
                    self.frame.SetStatusText,
                    text=message,
                    number=1,
                )
            elif event["event"] == "device-disconnected":
                wx.MessageBox("Device Disconnected", "", wx.OK | wx.ICON_INFORMATION)
                # update and notify user
                wx.CallAfter(
                    self.frame.SetStatusText, text="Device: Disconnected", number=1
                )
                # clear the package list
                if self.install_listpanel is not None:
                    wx.CallAfter(self.install_listpanel.listctrl.DeleteAllItems)
            elif event["event"] == "error":
                wx.CallAfter(self.exception_handler, err=event["exception"])
            elif event["event"] == "device-names-changed":
                dialog: dld.DeviceListDlg | None = (
                    dld.DeviceListDlg.get_global_instance()
                )
                if dialog is not None and dialog.IsShown():
                    _Log.info(event["device-names"])
                    wx.CallAfter(
                        dialog.device_listpanel.load_listctrl,
                        device_names=event["device-names"],
                    )
        except RuntimeError as err:
            # weird things happen within threads. output the error
            _Log.error(err.__str__())
        except Exception as err:
            wx.CallAfter(self.exception_handler, err=err)
        finally:
            return

    def set_selected_device(self, device_name: str) -> None:
        """set the selected device name and load the device packages

        Args:
            device_name (str): the name of the device
        """

        self.monitoring_device_thread.send_message_and_wait(
            {"request": "selected-device", "device-name": device_name}
        )

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

    @staticmethod
    def init_global_options(debug: bool, skip: bool, localhost: bool) -> None:
        """sets the global debug and skip flags"""
        QuestCaveApp.debug_mode = debug
        QuestCaveApp.skip = skip
        QuestCaveApp.local_host = localhost

    def OnInit(self) -> bool:
        """app has loaded create the main frame

        Returns:
            bool:
        """
        self.title = f"{config.APP_NAME} - version {config.APP_VERSION}"
        self.frame: MainFrame = MainFrame(parent=None, id=-1, title=self.title)
        self.frame.Show()
        if not self.skip:
            self.monitoring_device_thread = lib.quest.MonitorQuestDevices(
                callback=self.on_device_event, debug_mode=self.debug_mode
            )
            self.monitoring_device_thread.start()
        return super().OnInit()

    def exception_handler(self, err: Exception) -> None:
        """shows a dialog box with error icon can be used within a thread

        Args:
            err (Exception): exception error instance to be processed
        """
        # get the error text and show the basic message to the user in a dialog box
        error_message = err.__str__()
        with ErrorDlg(
            parent=self.frame,
            title="There was an error!!",
            message=error_message,
            err=err,
            disable_send=False,
        ) as dialog:
            if dialog.ShowModal() == wx.ID_CLOSE:
                return

        # User clicked the send error button. Format and send the error to the server
        error_request = LogErrorRequest.format_error(err, Settings.load().uuid)
        try:
            lib.tasks.check_task_and_create(
                self.send_error, error_request=error_request
            )
        except lib.tasks.TaskIsRunning:
            ui.utils.show_error_message(
                "Unable to send error log as another Task is already running",
                "Client Error",
            )

    async def send_error(self, error_request: LogErrorRequest) -> None:
        try:
            await api.client.post_error(error_request)
        except Exception as _err:
            wx.MessageBox(f"Unable to send. Reason: {str(_err)}", "Error!")

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
        selected_device = self.monitoring_device_thread.get_selected_device()
        if not self.debug_mode and not selected_device:
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
                    total_time=10,
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
            # take a snap shot of the packages before the install
            if not self.debug_mode:
                quest_packages = await adb_interface.get_installed_packages(
                    selected_device
                )
            else:
                quest_packages = debug.get_device(
                    debug.FakeQuest.devices, selected_device
                ).package_names

            # run the install step and keep the screen awake
            with keepawake(keep_screen_awake=True):
                install_task = lib.tasks.check_task_and_create(
                    self.start_install_process, path=magnet_data.download_path
                )
                try:
                    await asyncio.wait_for(install_task, timeout=None)
                except asyncio.CancelledError:
                    # User pressed the cancel button
                    self.on_install_update("Installation Cancelled")
                    self.on_install_update("Removing Packages...")
                    try:
                        await self.cleanup_from_cancel_installation(
                            selected_device, magnet_data.download_path, quest_packages
                        )
                    except Exception as err:
                        self.exception_handler(err=err)

    async def cleanup_from_cancel_installation(
        self, device_name: str, download_path: str, quest_packages: List[str]
    ) -> None:
        """finds any new installed packages and removes them, then removes the data files
        from the device_name

        Args:
            device_name (str): the selected device
            download_path (str): the path where the files were downloaded to
            quest_packages (List[str]): the original list of package names before the install

        """
        if self.debug_mode:
            self.on_install_update("Skipping cleanup as running Debug Mode")
            return
        # get the Device name to remove the files and packages from
        # remove the packages first
        packages_to_remove = await lib.quest.async_get_newly_installed_packages(
            device_name, quest_packages
        )
        for package_to_remove in packages_to_remove:
            self.on_install_update(f"Removing {package_to_remove}")
            try:
                await adb_interface.uninstall(device_name, package_to_remove)
            except (RemoteDeviceError, UnInstallError) as err:
                self.on_install_update(f"Error uninstalling: {err.__str__()}")
            else:
                self.on_install_update(f"Removed {package_to_remove}")

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

        # show the progress dialog. I might change this to a wx.ProgressDialog

        self.install_dialog = InstallProgressDlg(self.frame)
        self.install_dialog.Show()

        if not self.monitoring_device_thread.get_selected_device():
            ui.utils.show_error_message("No Device selected. Cannot install")
            return False
        try:
            if self.debug_mode:
                # gets some fake files and a fake apk filename
                apk_path = debug.generate_apk_path_object(path)
                await debug.simulate_game_install(
                    callback=self.on_install_update,
                    device_name=self.monitoring_device_thread.get_selected_device(),
                    fake_quests=debug.FakeQuest.devices,
                    apk_dir=apk_path,
                    raise_exception=None,
                    total_time_range=(62.0, 65.0),
                )
            else:
                # loop through all the sub directories searching for apk files
                # for every apk file found copy the sub folders to the OBB directory
                # on the Quest device
                for apk_dir in lib.utils.find_install_dirs(path):
                    await lib.quest.install_game(
                        callback=self.on_install_update,
                        device_name=self.monitoring_device_thread.get_selected_device(),
                        apk_dir=apk_dir,
                    )
        except Exception as err:
            self.on_install_update(f"Error: {err.__str__()}. Installation has quit")
            self.exception_handler(err)
            return False
        else:
            settings = Settings.load()
            # check if user wants to remove the files after install
            if settings.remove_files_after_install:
                self.on_install_update("Removing files...")
                try:
                    await self.cleanup_files(path)
                except Exception as err:
                    self.exception_handler(err)
                else:
                    self.on_install_update("Files removed")

            # check listpanel exists and reload the package listctrl
            if self.install_listpanel is not None:
                await self.install_listpanel.load(
                    self.monitoring_device_thread.get_selected_device()
                )
            self.install_dialog.complete()
            # close install dialog?
            if settings.close_dialog_after_install:
                self.install_dialog.close()
            else:
                # install went ok. Update statustext
                self.on_install_update("Installation has completed. Enjoy!!")
        return True

    async def cleanup_files(self, path: str) -> None:
        """removes the torrent files from the path

        Args:
            path (str): the path to remove
        """
        if not self.debug_mode:
            # delete the torrent files on the local path
            task = asyncio.create_task(
                lib.quest.cleanup(
                    path_to_remove=path, error_callback=self.on_install_update
                )
            )
        else:
            # simulate the cleanup
            task = asyncio.create_task(
                debug.simulate_cleanup(
                    path_to_remove=path,
                    error_callback=self.on_install_update,
                    force_error=False,
                )
            )
        await asyncio.wait_for(task, timeout=None)

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
        self.install_dialog.writeline(message)

    async def remove_package(self, package_name: str) -> None:
        """communicates with the ADB daemon and uninstalls the package from package name

        Args:
            package_name (str): the name of the package to uninstall
        """

        if not self.monitoring_device_thread.get_selected_device():
            return

        # dont want to upset mypy. check the listpanel exists
        # then disable the package listctrl while removing

        if self.install_listpanel is not None:
            self.install_listpanel.disable_list()

        # notify the user removing the package

        progress = ui.utils.load_progress_dialog(
            self.frame,
            "Removing Package",
            f"Removing {package_name} from Device {self.monitoring_device_thread.get_selected_device()}",
        )
        progress.Pulse()
        try:
            await adb_interface.uninstall(
                self.monitoring_device_thread.get_selected_device(), package_name
            )
        except (RemoteDeviceError, UnInstallError) as err:
            self.exception_handler(err)
        except Exception as err:
            asyncio.get_event_loop().call_exception_handler(
                {"message": err.__str__(), "exception": err}
            )
        else:
            self.frame.SetStatusText("Uninstall was successful")

            # reload the new package list into package listctrl

            if self.install_listpanel is not None:
                await self.install_listpanel.load(
                    self.monitoring_device_thread.get_selected_device()
                )
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

        load_adb_task = asyncio.create_task(adb_interface.start_adb())
        load_games_task = asyncio.create_task(self.load_games())
        get_app_details = asyncio.create_task(api.client.get_app_details())

        # check for any errors within the tasks

        results = await asyncio.gather(
            load_adb_task, load_games_task, get_app_details, return_exceptions=True
        )

        for result in results:
            if isinstance(result, Exception):
                self.exception_handler(result)

        # destroy the progress dialog and sleep for half a second to allow the dialog to destroy
        # before displaying another dialog to ask the user to select a quest device
        progress.Destroy()
        await asyncio.sleep(0.5)

        if not self.skip:
            # Check for update
            if isinstance(results[2], api.schemas.AppVersionResponse):
                app_details: api.schemas.AppVersionResponse = results[2]
                if await self.check_app_version_and_prompt_for_update(
                    app_details=app_details
                ):
                    # user wants to update
                    # delete local games list
                    if config.remove_file(config.QUEST_MAGNETS_PATH):
                        _Log.info("Removed local games list")
                    webbrowser.open(app_details.url)
                    # wait 1/2 second and close the app
                    await asyncio.sleep(0.5)
                    self.frame.Close()
                else:
                    await self.prompt_user_for_device()
            else:
                await self.prompt_user_for_device()

    async def load_games(self) -> None:
        """
        start a new task retrieving the magnet games from the backend server
        """
        await asyncio.sleep(0.1)
        if self.magnets_listpanel is None:
            return
        await asyncio.create_task(self.magnets_listpanel.load_magnets_from_api())

    async def check_app_version_and_prompt_for_update(
        self, app_details: api.schemas.AppVersionResponse
    ) -> bool:
        """checks the app version and prompts the user if new update is availible

        Args:
            app_details (api.schemas.AppVersionResponse): _description_

        Returns:
            bool: returns True if User selected download. False if wants to skip
        """
        try:
            if config.APP_VERSION < app_details.version:
                dlg = update_dialog.UpdateDialog(
                    parent=self.frame,
                    id=wx.ID_ANY,
                    title="Software Update",
                    size=self.frame.GetSize(),
                    style=wx.DEFAULT_DIALOG_STYLE,
                    update_details=app_details,
                )
                result = await wxasync.AsyncShowDialogModal(dlg)
                if result == update_dialog.ID_DOWNLOAD:
                    return True
            return False
        except Exception as err:
            self.exception_handler(err=err)
            return False

    async def prompt_user_for_device(self) -> None:
        """
        loads the device selection dialog and retrieves a selected device to use
        for installing the games to
        """
        result, selected_device = await dld.open_device_selection_dialog(
            self.frame,
            wx.ID_ANY,
            "Select a Device to install to",
            wx.DEFAULT_DIALOG_STYLE,
        )
        if result != wx.OK and result != 0:
            raise ValueError("Dialog did not return a wx.OK or Close id")
        if selected_device and self.install_listpanel is not None:
            self.set_selected_device(selected_device)
