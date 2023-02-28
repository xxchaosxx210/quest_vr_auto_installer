import wx

from ui.panels.devices_listpanel import DevicesListPanel
from ui.panels.magnets_listpanel import MagnetsListPanel
from ui.panels.installed_listpanel import InstalledListPanel


class MainPanel(wx.Panel):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        splitter_window = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)

        self.install_listpanel = InstalledListPanel(parent=splitter_window)
        self.magnet_listpanel = MagnetsListPanel(parent=splitter_window)

        splitter_window.SplitHorizontally(
            self.install_listpanel, self.magnet_listpanel, 300
        )
        self.install_listpanel.SetMinSize((-1, 50))
        self.magnet_listpanel.SetMinSize((-1, 300))

        gs = wx.GridSizer(cols=1)
        gs.Add(splitter_window, 1, wx.EXPAND | wx.ALL, 0)
        self.SetSizer(gs)
