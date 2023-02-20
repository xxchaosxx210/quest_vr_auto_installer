import wx
import asyncio
import random

from aiohttp import ClientConnectionError

from ui.devices_listpanel import DevicesListPanel
from ui.magnets_listpanel import MagnetsListPanel
from ui.installed_listpanel import InstalledListPanel
from ui.dialogs.install_progress_dialog import InstallProgressDialog
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.find_text_dialog import FindTextDialog
from ui.dialogs.login_dialog import LoginDialog
from ui.dialogs.user_info_dialog import UserInfoDialog
from lib.settings import Settings
import lib.image_manager as img_mgr
import qvrapi.api as api
import lib.tasks as tasks
import ui.utils


class MainFrame(wx.Frame):
    def __init__(self, *args, **kw):
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
        self.statusbar = wx.StatusBar(self)
        self.SetStatusBar(self.statusbar)
        self._create_menubar()
        self.SetIcon(wx.Icon(img_mgr.ICON_PATH))

    def _create_menubar(self) -> None:
        settings = Settings.load()

        menubar = wx.MenuBar()

        install_menu = wx.Menu()
        mi_settings = install_menu.Append(wx.ID_ANY, "Settings")
        self.Bind(wx.EVT_MENU, self._on_settings_menu, mi_settings)
        menubar.Append(install_menu, "Install")

        user_menu = wx.Menu()
        mi_login = user_menu.Append(wx.ID_ANY, "Login")
        self.Bind(wx.EVT_MENU, self._on_user_login, mi_login)
        user_menu.AppendSeparator()
        mi_user_info = user_menu.Append(wx.ID_ANY, "Details")
        self.Bind(wx.EVT_MENU, self._on_user_info, mi_user_info)
        user_menu.AppendSeparator()
        mi_remove_auth = user_menu.Append(wx.ID_ANY, "Logout")
        self.Bind(wx.EVT_MENU, self._on_logout_user, mi_remove_auth)
        # Create an Admin submenu
        user_menu.AppendSeparator()
        self.mi_admin_menu = wx.Menu()
        mi_admin_logs = self.mi_admin_menu.Append(wx.ID_ANY, "Logs")
        ui.utils.enable_menu_items(self.mi_admin_menu, settings.is_user_admin())
        user_menu.AppendSubMenu(self.mi_admin_menu, "Admin", "Admin tools and testing")
        menubar.Append(user_menu, "Account")

        view_menu = wx.Menu()
        mi_find_magnet = view_menu.Append(wx.ID_ANY, "Game")
        self.Bind(wx.EVT_MENU, self._on_find_magnet, mi_find_magnet)
        menubar.Append(view_menu, "Search")

        debug_menu = wx.Menu()
        mi_show_install_dialog = debug_menu.Append(wx.ID_ANY, "Show Install Dialog")
        self.Bind(wx.EVT_MENU, self._on_show_install_dialog, mi_show_install_dialog)
        debug_menu.AppendSeparator()
        mi_raise_caught_exception = debug_menu.Append(
            wx.ID_ANY, "Raise Caught Exception"
        )
        self.Bind(
            wx.EVT_MENU,
            lambda *args: self.app.exception_handler(
                ValueError("This is a test from handled caught exception")
            ),
            mi_raise_caught_exception,
        )
        mi_raise_unhandled_exception = debug_menu.Append(
            wx.ID_ANY, "Raise an Unhandled Exception"
        )
        self.Bind(wx.EVT_MENU, self._on_raise_unhandled, mi_raise_unhandled_exception)
        menubar.Append(debug_menu, "Debug")

        help_menu = wx.Menu()
        mi_about = help_menu.Append(wx.ID_ANY, "About")
        self.Bind(wx.EVT_MENU, lambda *args: args, mi_about)
        menubar.Append(help_menu, "Help")

        self.Bind(wx.EVT_MENU_OPEN, self._on_menu_open, menubar)
        self.SetMenuBar(menubar)

    def _on_logout_user(self, evt: wx.MenuEvent) -> None:
        settings = Settings.load()
        settings.remove_auth()
        ui.utils.enable_menu_items(self.mi_admin_menu, False)

    def _on_menu_open(self, evt: wx.MenuEvent) -> None:
        menu: wx.Menu = evt.GetMenu()
        if menu.GetTitle() != "Account":
            pass
        evt.Skip()

    def _on_user_info(self, evt: wx.MenuEvent) -> None:
        settings = Settings.load()
        if not settings.token:
            return

        async def _get_user_info(token: str) -> None:
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
            data = dlg.get_data()
            if data:
                settings.set_auth(data)
                settings.save()
        dlg.Destroy()
        ui.utils.enable_menu_items(
            menu=self.mi_admin_menu, enable=settings.is_user_admin()
        )

    def _on_find_magnet(self, evt: wx.MenuEvent) -> None:
        """laods the find dialog box and searches for the magnet in the games list
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


class MainPanel(wx.Panel):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        self.device_listpanel = DevicesListPanel(parent=self)
        self.magnet_listpanel = MagnetsListPanel(parent=self)
        self.install_listpanel = InstalledListPanel(parent=self)

        sizer = wx.GridBagSizer()

        # Add device_listpanel to top left
        sizer.Add(self.device_listpanel, pos=(0, 0), flag=wx.LEFT)
        # Add install_listpanel to top right
        sizer.Add(self.install_listpanel, pos=(0, 1), flag=wx.EXPAND | wx.ALL)
        # Add magnet_listpanel to bottom, expanded
        sizer.Add(self.magnet_listpanel, pos=(1, 0), span=(1, 2), flag=wx.EXPAND)

        sizer.AddGrowableRow(1, 1)
        sizer.AddGrowableCol(1, 1)
        # Set the sizer for the panel
        self.SetSizer(sizer)
