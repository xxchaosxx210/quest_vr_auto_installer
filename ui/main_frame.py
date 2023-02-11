import wx
import asyncio

from ui.devices_listpanel import DevicesListPanel
from ui.magnets_listpanel import MagnetsListPanel
from ui.installed_listpanel import InstalledListPanel

import lib.image_manager as img_mgr


class MainFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.statusbar = wx.StatusBar(self)
        self.SetStatusBar(self.statusbar)
        self.main_panel = MainPanel(parent=self)
        gs = wx.GridSizer(1)
        gs.Add(self.main_panel, 1, wx.ALL | wx.EXPAND, 0)
        self.SetSizerAndFit(gs)
        self.SetSize((800, 600))
        self.Bind(wx.EVT_SHOW, self.on_show)

        self.init_icon()

    def init_icon(self) -> None:
        """sets the apps icon"""
        icon = wx.Icon(img_mgr.ICON_PATH)
        self.SetIcon(icon)

    def on_show(self, evt: wx.CommandEvent):
        """when the window is shown load the listctrls

        Args:
            evt (wx.CommandEvent): _description_
        """
        loop = asyncio.get_event_loop()
        loop.create_task(self.load_lists(loop))

    async def load_lists(self, loop: asyncio.AbstractEventLoop):
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
