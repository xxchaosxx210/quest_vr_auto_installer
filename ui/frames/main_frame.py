import logging
import wx
import asyncio
import random
import webbrowser

from aiohttp import ClientConnectionError
import wxasync

import lib.config
import lib.tasks as tasks
import api.client as client
import api.urls
import lib.debug
import ui.utils
import ui.paths
from ui.panels.main_panel import MainPanel
from ui.dialogs.install_progress import InstallProgressDlg
from ui.dialogs.settings import SettingsDlg
from ui.dialogs.find_text import FindTextDlg
from ui.dialogs.login import LoginDlg
from ui.dialogs.user_info import UserInfoDlg
from ui.dialogs.add_game import AddGameDlg
from ui.dialogs.about import load_dialog as load_about_dialog
from ui.dialogs.device_list import open_device_selection_dialog
from ui.dialogs.update_magnet import load_dialog as load_update_magnet_dialog
from ui.frames.logs_frame import LogsFrame
from lib.settings import Settings
from api.exceptions import ApiError


_Log = logging.getLogger()


# The menubar wx.Menu Labels
USER_MENU_LABEL = "User"
SEARCH_MENU_LABEL = "Search"
DEBUG_MENU_LABEL = "Debug"
HELP_MENU_LABEL = "Help"


class MainFrame(wx.Frame):
    def __init__(self, *args, **kw):
        # avoids circular import I need to fix this at some point
        from quest_cave_app import QuestCaveApp

        super().__init__(*args, **kw)
        self.app: QuestCaveApp = wx.GetApp()
        self.__do_controls()
        self.__do_events()
        self.__do_layout()
        self.__do_properties()

    def __do_events(self) -> None:
        # capture the on Window show event
        self.Bind(wx.EVT_SHOW, self.on_show)

    def __do_controls(self) -> None:
        """create the controls for the main frame"""
        self.main_panel = MainPanel(parent=self)
        self.__do_statusbar()
        self.__do_menubar()

    def __do_properties(self) -> None:
        self.SetIcon(wx.Icon(ui.paths.ICON_PATH))
        self.SetSize((800, 200))

    def __do_statusbar(self) -> None:
        """create the status bar for the main frame"""
        self.statusbar = wx.StatusBar(self)
        self.statusbar.SetFieldsCount(2)
        self.statusbar.SetStatusWidths([-2, -1])
        self.SetStatusBar(self.statusbar)

    def __do_layout(self) -> None:
        """set up the layout for the main window"""
        gs = wx.GridSizer(1)
        gs.Add(self.main_panel, 1, wx.ALL | wx.EXPAND, 0)
        self.SetSizerAndFit(gs)

    def __do_menubar(self) -> None:
        """create the menu bar for the main frame"""
        menubar = wx.MenuBar()
        menubar.Append(self._create_user_menu(), USER_MENU_LABEL)
        menubar.Append(self._create_search_menu(), SEARCH_MENU_LABEL)
        if self.app.debug_mode:
            menubar.Append(self._create_debug_menu(), DEBUG_MENU_LABEL)
        menubar.Append(self._create_help_menu(), HELP_MENU_LABEL)

        self.Bind(wx.EVT_MENU_OPEN, self._on_menu_open, menubar)
        self.SetMenuBar(menubar)

    def _create_help_menu(self) -> wx.Menu:
        """Creates the help menu for the main window"""

        def on_about_menu_item(evt: wx.MenuEvent) -> None:
            asyncio.create_task(
                load_about_dialog(
                    parent=self,
                    title="About",
                    id=wx.ID_ANY,
                    size=(300, 300),
                    app_name=lib.config.APP_NAME,
                    version=lib.config.APP_VERSION,
                    description="QuestCave is a tool for downloading and installing Quest 2 games for free\nI take no responsibility for the abuse of this program. Enjoy :)",
                    author=f"{lib.config.AUTHOR}",
                )
            )
            evt.Skip()

        menu = wx.Menu()
        # website link
        website_m_item = menu.Append(wx.ID_ANY, "Website")
        self.Bind(wx.EVT_MENU, self._on_website_item, website_m_item)
        # Help Link
        help_m_item = menu.Append(wx.ID_ANY, "Help")
        # help_m_item.SetAccel(wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F1))
        self.Bind(wx.EVT_MENU, self._on_help, help_m_item)
        # About
        menu.AppendSeparator()
        about_m_item = menu.Append(wx.ID_ANY, "About")
        self.Bind(wx.EVT_MENU, on_about_menu_item, about_m_item)
        return menu

    def _on_website_item(self, evt: wx.MenuEvent) -> None:
        """loads the index page in the default browser"""
        try:
            webbrowser.open(api.urls.URI_INDEX, new=0, autoraise=True)
        except (webbrowser.Error, OSError, IOError) as err:
            self.app.exception_handler(err)

    def _on_help(self, evt: wx.MenuEvent) -> None:
        """loads the help page in the default browser"""
        try:
            webbrowser.open(api.urls.URI_HELP, new=0, autoraise=True)
        except (webbrowser.Error, OSError, IOError) as err:
            self.app.exception_handler(err)

    def _create_search_menu(self) -> wx.Menu:
        """Creates the search menu for the main window

        Returns:
            wx.Menu: the search menu
        """
        menu = wx.Menu()
        find_installed_item: wx.MenuItem = menu.Append(
            wx.ID_ANY,
            "Installed Game\tCtrl+I",
            helpString="Find a Game that is currently installed on your QuestVR",
        )
        find_installed_item.SetAccel(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("I")))
        self.Bind(wx.EVT_MENU, self._on_find_installed, find_installed_item)
        find_magnet_m_item: wx.MenuItem = menu.Append(
            wx.ID_ANY, "Game\tCtrl+G", helpString="Find a game in the games list"
        )
        find_magnet_m_item.SetAccel(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("G")))
        self.Bind(wx.EVT_MENU, self._on_find_magnet, find_magnet_m_item)
        return menu

    def _create_debug_menu(self) -> wx.Menu:
        """Creates the debug menu for the main window"""
        menu = wx.Menu()
        install_dlg_m_item = menu.Append(wx.ID_ANY, "Show Install Dialog")
        self.Bind(wx.EVT_MENU, self._on_show_install_dialog, install_dlg_m_item)
        update_mag_m_item = menu.Append(wx.ID_ANY, "Show Update Magnet Dialog")
        self.Bind(wx.EVT_MENU, self._on_show_update_magnet_dialog, update_mag_m_item)
        menu.AppendSeparator()
        raise_caught_error_m_item = menu.Append(wx.ID_ANY, "Raise Caught Exception")
        self.Bind(
            wx.EVT_MENU,
            lambda *args: self.app.exception_handler(
                ValueError("This is a test from handled caught exception")
            ),
            raise_caught_error_m_item,
        )
        raise_unhandled_err_m_item = menu.Append(
            wx.ID_ANY, "Raise an Unhandled Exception"
        )
        self.Bind(wx.EVT_MENU, self._on_raise_unhandled, raise_unhandled_err_m_item)
        menu.AppendSeparator()
        disconnect_m_item = menu.Append(wx.ID_ANY, "Disconnect Device")
        self.Bind(wx.EVT_MENU, self._on_disconnect_device, disconnect_m_item)
        return menu

    def _create_user_menu(self) -> wx.Menu:
        """create the user menu for the main window

        Returns:
            wx.Menu: the user menu
        """
        settings = Settings.load()
        menu = wx.Menu()
        login_m_item = menu.Append(wx.ID_ANY, "Login")
        login_m_item.SetAccel(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("L")))
        self.Bind(wx.EVT_MENU, self._on_user_login, login_m_item)
        user_info_m_item = menu.Append(wx.ID_ANY, "Details")
        self.Bind(wx.EVT_MENU, self._on_user_info, user_info_m_item)
        remove_auth_m_item = menu.Append(wx.ID_ANY, "Logout")
        self.Bind(wx.EVT_MENU, self._on_logout_user, remove_auth_m_item)
        menu.AppendSeparator()

        # Device selection
        device_m_item = menu.Append(wx.ID_ANY, "Device\tCtrl+D")
        self.Bind(wx.EVT_MENU, self._on_device_dialog, device_m_item)
        device_m_item.SetAccel(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("D")))

        menu.AppendSeparator()

        # Create an Admin submenu
        self.admin_submenu = wx.Menu()
        admin_add_game_m_item = self.admin_submenu.Append(wx.ID_ANY, "Add Game")
        self.Bind(wx.EVT_MENU, self._on_add_game_dialog, admin_add_game_m_item)
        self.admin_submenu.AppendSeparator()
        admin_logs_m_item = self.admin_submenu.Append(wx.ID_ANY, "Logs")
        self.Bind(wx.EVT_MENU, self._on_logs_frame, admin_logs_m_item)
        ui.utils.enable_menu_items(self.admin_submenu, settings.is_user_admin())
        menu.AppendSubMenu(self.admin_submenu, "Admin", "Admin tools and testing")
        menu.AppendSeparator()

        settings_m_item = menu.Append(wx.ID_ANY, "Preferences\tCtrl+S")
        settings_m_item.SetAccel(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("S")))
        self.Bind(wx.EVT_MENU, self._on_settings_menu, settings_m_item)

        menu.AppendSeparator()
        exit_m_item = menu.Append(wx.ID_ANY, "Exit")
        self.Bind(wx.EVT_MENU, lambda *args: self.Close(), exit_m_item)
        return menu

    def _on_disconnect_device(self, evt: wx.MenuEvent) -> None:
        """simulates a device being disconnected (Debug only)

        Args:
            evt (wx.MenuEvent):
        """
        if not self.app.debug_mode:
            return
        # get the selected device from the background thread
        device_name = self.app.monitoring_device_thread.get_selected_device()
        # check if the device is connected and remove it
        if device_name and not lib.debug.FakeQuest.remove_device(device_name):
            _Log.error(f"Failed to remove device {device_name}. Reason: Not found")

    def _on_device_dialog(self, evt: wx.MenuEvent) -> None:
        """opens a DeviceListDialog and creates background running task to
        check for new quest devices connected

        Args:
            evt (wx.MenuEvent):
        """

        async def new_device_selection_task():
            result, device_name = await open_device_selection_dialog(
                self, wx.ID_ANY, "Select Device", wx.DEFAULT_DIALOG_STYLE
            )
            if result == wx.ID_OK:
                self.app.set_selected_device(device_name)

        tasks.check_task_and_create(new_device_selection_task)

    def _on_add_game_dialog(self, evt: wx.MenuEvent) -> None:
        """This method is triggered when the user selects an option to add a new game from a menu.
         The method first loads the user's settings and checks if the user is an admin.
         If the user is not an admin, an error message is displayed and the method exits.

        If the user is an admin, the method creates an instance of the AddGameDlg
        dialog box and displays it asynchronously using the
        wxasync.AsyncShowDialogModal method.
        If the user clicks the "Save" button in the dialog box, the game is saved to the database
        (although this functionality is not implemented in the code snippet provided).

        Args:
            evt (wx.MenuEvent): Not implemented
        """
        settings = Settings.load()
        if not settings.is_user_admin():
            ui.utils.show_error_message(
                "You do not have permission to access this function"
            )

        async def open_dialog():
            try:
                dlg = AddGameDlg(self, wx.ID_ANY, "Add Game", (640, 640))
            except Exception as err:
                self.app.exception_handler(err)
            else:
                result_code = await wxasync.AsyncShowDialogModal(dlg)
                if result_code == wx.ID_SAVE:
                    # FINISH THIS PLEASE!!!!
                    pass

        if Settings.load().is_user_admin():
            try:
                tasks.check_task_and_create(open_dialog)
            except tasks.TaskIsRunning:
                ui.utils.show_error_message("A task is already running")

    def _on_logs_frame(self, evt: wx.MenuEvent) -> None:
        """opens a LogsFrame to show the logs"""
        dlg = LogsFrame(self, size=(500, 500))
        dlg.Show()

    def _on_logout_user(self, evt: wx.MenuEvent) -> None:
        """remove the authentication token and user information on json file and
        disable admin sub menus

        Args:
            evt (wx.MenuEvent):
        """
        settings = Settings.load()
        settings.remove_auth()
        ui.utils.enable_menu_items(self.admin_submenu, False)

    def _on_menu_open(self, evt: wx.MenuEvent) -> None:
        """
        check when the User menu is opened and check if user is administrator to enable
        the admin sub menus

        Args:
            evt (wx.MenuEvent):
        """
        menu: wx.Menu = evt.GetMenu()
        if isinstance(menu, wx.Menu) and menu.GetTitle() == USER_MENU_LABEL:
            settings = Settings.load()
            ui.utils.enable_menu_items(self.admin_submenu, settings.is_user_admin())
        evt.Skip()

    def _on_user_info(self, evt: wx.MenuEvent) -> None:
        """get user account information from the api and open a dialog with
        that information

        Args:
            evt (wx.MenuEvent):
        """
        settings = Settings.load()
        if not settings.token:
            return

        async def _get_user_info(token: str) -> None:
            """gets the user information async

            Args:
                token (str): the token belonging to the user
            """
            try:
                user = await client.get_user_info(token)
            except ApiError as err:
                wx.MessageBox(
                    err.message, f"Status: {err.status_code}", wx.OK | wx.ICON_ERROR
                )
            except ClientConnectionError as err:
                self.app.exception_handler(err)
            else:
                with UserInfoDlg(parent=self, size=(500, -1), user=user) as dlg:
                    dlg.ShowModal()
            finally:
                return

        # check if a request is already running if so then ignore this event
        try:
            tasks.check_task_and_create(_get_user_info, token=settings.token)
        except tasks.TaskIsRunning as err:
            wx.MessageBox(err.__str__(), "", wx.OK)

    def _on_user_login(self, evt: wx.MenuEvent) -> None:
        """loads the login dialog box and authenticates user
        saving the token to settings directory

        Args:
            evt (wx.MenuEvent): Not used
        """
        settings = Settings.load()
        with LoginDlg(
            parent=self,
            id=wx.ID_ANY,
            title="Login",
            email_field=settings.get_user_email(),
            size=(300, -1),
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                # save the returned data to json file
                data = dlg.get_data()
                if data is not None:
                    settings.set_auth(data)
                    settings.save()
        # enable the admin sub menus
        ui.utils.enable_menu_items(
            menu=self.admin_submenu, enable=settings.is_user_admin()
        )

    def _on_find_installed(self, evt: wx.MenuEvent) -> None:
        """Launch the FindText Dialog and prompt for Installed Game search

        Args:
            evt (wx.MenuEvent): not used
        """
        with FindTextDlg(
            parent=self,
            label="Enter name of Installed Game",
            title="",
            size=(300, -1),
        ) as dlg:
            if dlg.ShowModal() == wx.ID_CANCEL:
                return
            text = dlg.get_text()
            if self.app.install_listpanel is not None and len(text) > 2:
                self.app.install_listpanel.search_installed_games(text)
            else:
                ui.utils.show_error_message("Text must be atleast 3 characters long")

    def _on_find_magnet(self, evt: wx.MenuEvent) -> None:
        """loads the find dialog box and searches for the magnet name in the games list
        highlights first match in the listctrl

        Args:
            evt (wx.MenuEvent): Not used
        """
        with FindTextDlg(
            parent=self,
            label="Enter name of Game",
            title="",
            size=(300, -1),
        ) as dlg:
            if dlg.ShowModal() == wx.ID_CANCEL:
                return
            text = dlg.get_text()
            if self.app.magnets_listpanel is not None and len(text) > 2:
                self.app.magnets_listpanel.search_game(text)
            else:
                ui.utils.show_error_message("Text must be at least 3 characters long")

    def _on_raise_unhandled(self, evt: wx.MenuEvent) -> None:
        """simulate an unhandled exception. This is to test the exception handler

        Args:
            evt (wx.MenuEvent):
        """

        exceptions = [KeyError, ValueError, ConnectionError, FileNotFoundError]
        exc = random.choice(exceptions)
        message = "This is to test the unhandled exceptions handler"
        raise exc(message)

    def _on_settings_menu(self, evt: wx.MenuEvent) -> None:
        """load the settings dialog

        Args:
            evt (wx.MenuEvent): Not needed
        """
        dlg = SettingsDlg(self, "Settings", (500, 600))
        if dlg.ShowModal() == wx.ID_OK:
            dlg.save_from_controls()
        dlg.Destroy()

    def _on_show_install_dialog(self, evt: wx.MenuEvent) -> None:
        """shows the install dialog box for testing purposes

        Args:
            evt (wx.MenuEvent):
        """
        dlg = InstallProgressDlg(self)
        dlg.Show()
        dlg.writeline("If you can see this text")
        dlg.writeline("then the dialog is working")
        dlg.writeline("another new line")

    def _on_show_update_magnet_dialog(self, evt: wx.MenuEvent) -> None:
        """shows the update magnet dialog box for testing purposes

        Args:
            evt (wx.MenuEvent):
        """
        try:
            tasks.check_task_and_create(
                load_update_magnet_dialog, parent=self, title="Demo", magnet=None
            )
        except tasks.TaskIsRunning:
            ui.utils.show_error_message("Task is alreasy running")

    def on_show(self, evt: wx.ShowEvent) -> None:
        """
        when the Window is shown load the device list dialog task and connect to the API
        or a saved json and load the magnets

        Args:
            evt (wx.CommandEvent): not used
        """
        if not self.app.skip:
            tasks.check_task_and_create(self.app.load_resources)
        evt.Skip()
