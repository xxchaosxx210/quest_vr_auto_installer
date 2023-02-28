import wx

from ui.panels.devices_listpanel import DevicesListPanel
from ui.panels.magnets_listpanel import MagnetsListPanel
from ui.panels.installed_listpanel import InstalledListPanel


class MainPanel(wx.Panel):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        self.magnet_listpanel = MagnetsListPanel(parent=self)
        self.install_listpanel = InstalledListPanel(parent=self)

        panel_vbox = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.install_listpanel, 1, wx.EXPAND, wx.ALL, 0)
        panel_vbox.Add(hbox, 0, wx.EXPAND | wx.ALL, 0)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.magnet_listpanel, 1, wx.EXPAND, wx.ALL, 0)
        panel_vbox.Add(hbox, 2, wx.EXPAND | wx.ALL, 0)
        self.SetSizer(panel_vbox)
