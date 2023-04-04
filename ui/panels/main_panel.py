import wx

import ui.consts
from ui.panels.magnets_listpanel import MagnetsListPanel
from ui.panels.installed_listpanel import InstalledListPanel


class MainPanel(wx.Panel):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        self.splitter_window = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)

        self.install_listpanel = InstalledListPanel(parent=self.splitter_window)
        self.magnet_listpanel = MagnetsListPanel(parent=self.splitter_window)

        self.splitter_window.SplitHorizontally(
            self.install_listpanel, self.magnet_listpanel, 300
        )
        self.install_listpanel.SetMinSize((-1, -1))
        self.magnet_listpanel.SetMinSize((-1, 300))

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddSpacer(ui.consts.SMALL_BORDER)
        hbox.Add(self.splitter_window, 1, wx.EXPAND | wx.ALL, 0)
        hbox.AddSpacer(ui.consts.SMALL_BORDER)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.AddSpacer(ui.consts.SMALL_BORDER)
        vbox.Add(hbox, 1, wx.EXPAND | wx.ALL, 0)
        vbox.AddSpacer(ui.consts.SMALL_BORDER)
        self.SetSizer(vbox)
