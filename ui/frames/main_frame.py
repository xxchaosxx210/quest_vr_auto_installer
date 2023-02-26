import wx
import asyncio
import random

from aiohttp import ClientConnectionError
import wxasync

from ui.panels.main_panel import MainPanel
from ui.dialogs.install_progress_dialog import InstallProgressDialog
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.find_text_dialog import FindTextDialog
from ui.dialogs.login_dialog import LoginDialog
from ui.dialogs.user_info_dialog import UserInfoDialog
from ui.dialogs.add_game_dialog import AddGameDialog
from ui.frames.logs_frame import LogsFrame
from lib.settings import Settings
import lib.image_manager as img_mgr
import qvrapi.api as api
import lib.tasks as tasks
import ui.utils


class MainFrame(wx.Frame):
    def __init__(self, *args, **kw):
        # avoids circular import I need to fix this at some point
        from q2gapp import Q2GApp

        super().__init__(*args, **kw)
        self.app: Q2GApp = wx.GetApp()
        self._init_ui()
        self.main_panel = MainPanel(parent=self)
        gs = wx.GridSizer(1)
        gs.Add(self.main_panel, 1, wx.ALL | wx.EXPAND, 0)
        self.SetSizerAndFit(gs)
        self.SetSize((800, 600))
        self.Bind(wx.EVT_SHOW, self.on_show)

    def _init_ui(self) -> None:
        """set up the statusbar, icon and menubar for the main window"""
        self.statusbar = wx.StatusBar(self)
        self.SetStatusBar(self.statusbar)
        self._create_menubar()
        self.SetIcon(wx.Icon(img_mgr.ICON_PATH))

    def _create_menubar(self) -> None:
        menubar = wx.MenuBar()
        menubar.Append(self._create_install_menu(), "Install")
        menubar.Append(self._create_user_menu(), "Account")
        menubar.Append(self._create_search_menu(), "Search")
        menubar.Append(self._create_debug_menu(), "Debug")
        menubar.Append(self._create_help_menu(), "Help")

        self.Bind(wx.EVT_MENU_OPEN, self._on_menu_open, menubar)
        self.SetMenuBar(menubar)

    def _create_help_menu(self) -> wx.Menu:
        menu = wx.Menu()
        about_m_item = menu.Append(wx.ID_ANY, "About")
        self.Bind(wx.EVT_MENU, lambda *args: args, about_m_item)
        return menu

    def _create_search_menu(self) -> wx.Menu:
        menu = wx.Menu()
        find_magnet_m_item = menu.Append(wx.ID_ANY, "Game")
        self.Bind(wx.EVT_MENU, self._on_find_magnet, find_magnet_m_item)
        return menu

    def _create_install_menu(self) -> wx.Menu:
        menu = wx.Menu()
        settings_m_item = menu.Append(wx.ID_ANY, "Settings")
        self.Bind(wx.EVT_MENU, self._on_settings_menu, settings_m_item)
        return menu

    def _create_debug_menu(self) -> wx.Menu:
        menu = wx.Menu()
        install_dlg_m_item = menu.Append(wx.ID_ANY, "Show Install Dialog")
        self.Bind(wx.EVT_MENU, self._on_show_install_dialog, install_dlg_m_item)
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
        return menu

    def _create_user_menu(self) -> wx.Menu:
        settings = Settings.load()
        menu = wx.Menu()
        login_m_item = menu.Append(wx.ID_ANY, "Login")
        self.Bind(wx.EVT_MENU, self._on_user_login, login_m_item)
        menu.AppendSeparator()
        user_info_m_item = menu.Append(wx.ID_ANY, "Details")
        self.Bind(wx.EVT_MENU, self._on_user_info, user_info_m_item)
        menu.AppendSeparator()
        remove_auth_m_item = menu.Append(wx.ID_ANY, "Logout")
        self.Bind(wx.EVT_MENU, self._on_logout_user, remove_auth_m_item)

        # Create an Admin submenu
        menu.AppendSeparator()
        self.admin_submenu = wx.Menu()
        admin_add_game_m_item = self.admin_submenu.Append(wx.ID_ANY, "Add Game")
        self.Bind(wx.EVT_MENU, self._on_add_game_dialog, admin_add_game_m_item)
        self.admin_submenu.AppendSeparator()
        admin_logs_m_item = self.admin_submenu.Append(wx.ID_ANY, "Logs")
        self.Bind(wx.EVT_MENU, self._on_logs_frame, admin_logs_m_item)
        ui.utils.enable_menu_items(self.admin_submenu, settings.is_user_admin())
        menu.AppendSubMenu(self.admin_submenu, "Admin", "Admin tools and testing")
        return menu

    def _on_add_game_dialog(self, evt: wx.MenuEvent) -> None:
        settings = Settings.load()
        if not settings.is_user_admin():
            ui.utils.show_error_message(
                "You do not have permission to access this function"
            )

        async def open_dialog():
            dlg = AddGameDialog(self, wx.ID_ANY, "Add Game", (640, 640))
            result_code = await wxasync.AsyncShowDialog(dlg)
            if result_code == wx.ID_SAVE:
                # save game to database
                pass
            dlg.Destroy()

        asyncio.get_event_loop().create_task(open_dialog())

    def _on_logs_frame(self, evt: wx.MenuEvent) -> None:
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
        """check when the Account menu is opened and check if user is administrator to enable
        the admin sub menus

        Args:
            evt (wx.MenuEvent):
        """
        menu: wx.Menu = evt.GetMenu()
        if menu.GetTitle() != "Account":
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
                user = await api.get_user_info(token)
            except api.ApiError as err:
                wx.MessageBox(
                    err.message, f"Status: {err.status_code}", wx.OK | wx.ICON_ERROR
                )
            except ClientConnectionError as err:
                self.app.exception_handler(err)
            else:
                dlg = UserInfoDialog(parent=self, size=(500, -1), user=user)
                dlg.ShowModal()
                dlg.Destroy()
            finally:
                return

        # check if a request is already running if so then ignore this event
        try:
            tasks.get_user_info(_get_user_info, token=settings.token)
        except tasks.TaskIsRunning as err:
            wx.MessageBox(err.__str__(), "", wx.OK)

    def _on_user_login(self, evt: wx.MenuEvent) -> None:
        """loads the login dialog box and authenticates user
        saving the token to settings directory

        Args:
            evt (wx.MenuEvent): Not used
        """
        settings = Settings.load()
        dlg = LoginDialog(
            parent=self,
            title="Login",
            email_field=settings.get_user_email(),
            size=(300, -1),
        )
        return_code = dlg.ShowModal()
        if return_code == wx.OK:
            # save the returned data to json file
            data = dlg.get_data()
            if data is not None:
                settings.set_auth(data)
                settings.save()
        dlg.Destroy()
        ui.utils.enable_menu_items(
            menu=self.admin_submenu, enable=settings.is_user_admin()
        )

    def _on_find_magnet(self, evt: wx.MenuEvent) -> None:
        """loads the find dialog box and searches for the magnet name in the games list
        highlights first match in the listctrl

        Args:
            evt (wx.MenuEvent): Not used
        """
        dlg = FindTextDialog(
            parent=self,
            label="Enter name of Game",
            title="",
            size=(300, -1),
        )
        if dlg.ShowModal() == wx.ID_OK:
            text = dlg.GetText()
        else:
            text = None
        dlg.Destroy()
        if isinstance(text, str) and len(text) > 0:
            self.app.magnets_listpanel.search_game(text)

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
        dlg = SettingsDialog(self, "Settings", (500, 600))
        if dlg.ShowModal() == wx.ID_OK:
            dlg.save_from_controls()
        dlg.Destroy()

    def _on_show_install_dialog(self, evt: wx.MenuEvent) -> None:
        """shows the install dialog box for testing purposes

        Args:
            evt (wx.MenuEvent):
        """
        dlg = InstallProgressDialog(self)
        dlg.Show()

    def on_show(self, evt: wx.CommandEvent):
        """when the window is shown load the listctrls

        Args:
            evt (wx.CommandEvent):
        """
        loop = asyncio.get_event_loop()
        loop.create_task(self.load_lists(loop))

    async def load_lists(self, loop: asyncio.AbstractEventLoop) -> None:
        """create seperate coroutines to collect information for the quest device, game torrents
        load the listctrls

        Args:
            loop (asyncio.AbstractEventLoop): the event loop to create the tasks
        """
        wx.CallAfter(self.statusbar.SetStatusText, text="Scanning for Quest devices...")
        await asyncio.sleep(0.1)
        task1 = loop.create_task(self.app.devices_listpanel.load())
        task2 = loop.create_task(self.app.magnets_listpanel.load_magnets_from_api())
        while not task1.done() and not task2.done():
            await asyncio.sleep(0.1)
        wx.CallAfter(self.statusbar.SetStatusText, text="All Complete")
