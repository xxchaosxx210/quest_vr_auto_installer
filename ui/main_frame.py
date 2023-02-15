import wx
import asyncio

from ui.devices_listpanel import DevicesListPanel
from ui.magnets_listpanel import MagnetsListPanel
from ui.installed_listpanel import InstalledListPanel
from ui.dialogs.install_progress_dialog import InstallProgressDialog
from ui.dialogs.settings_dialog import SettingsDialog

import lib.image_manager as img_mgr


class MainFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
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
        menubar = wx.MenuBar()

        install_menu = wx.Menu()
        mi_settings = install_menu.Append(wx.ID_ANY, "Settings")
        self.Bind(wx.EVT_MENU, self._on_settings_menu, mi_settings)
        menubar.Append(install_menu, "Install")

        debug_menu = wx.Menu()
        mi_show_install_dialog = debug_menu.Append(wx.ID_ANY, "Show Install Dialog")
        self.Bind(wx.EVT_MENU, self._on_show_install_dialog, mi_show_install_dialog)
        menubar.Append(debug_menu, "Debug")

        help_menu = wx.Menu()
        mi_about = help_menu.Append(wx.ID_ANY, "About")
        self.Bind(wx.EVT_MENU, lambda *args: args, mi_about)
        menubar.Append(help_menu, "Help")

        self.SetMenuBar(menubar)

    def _on_settings_menu(self, evt: wx.MenuEvent) -> None:
        """load the settings dialog

        Args:
            evt (wx.MenuEvent): Not needed
        """
        dlg = SettingsDialog(self, "Settings", (300, 300))
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
            evt (wx.CommandEvent): _description_
        """
        loop = asyncio.get_event_loop()
        loop.create_task(self.load_lists(loop))

    async def load_lists(self, loop: asyncio.AbstractEventLoop) -> None:
        """create seperate coroutines to collect information for the quest device, game torrents
        load the listctrls

        Args:
            loop (asyncio.AbstractEventLoop): the event loop to create the tasks
        """
        app = wx.GetApp()
        wx.CallAfter(self.statusbar.SetStatusText, text="Scanning for Quest devices...")
        await asyncio.sleep(0.1)
        task1 = loop.create_task(app.devices_listpanel.load())
        task2 = loop.create_task(app.magnets_listpanel.load_magnets_from_api())
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
