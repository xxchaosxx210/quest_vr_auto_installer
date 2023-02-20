import wx

from ui.devices_listpanel import DevicesListPanel
from ui.magnets_listpanel import MagnetsListPanel
from ui.installed_listpanel import InstalledListPanel


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
