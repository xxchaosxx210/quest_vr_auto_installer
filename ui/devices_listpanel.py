import asyncio
import logging

import wx

import config
from adblib import adb_interface
from ui.listpanel import ListPanel

_Log = logging.getLogger()


class DevicesListPanel(ListPanel):
    def __init__(self, *args, **kwargs):
        # the device that is currently selected in the listctrl
        self.selected_device: str = None
        columns = [{"col": 0, "heading": "Name", "width": 200}]
        super().__init__(title="Devices", columns=columns, *args, **kwargs)
        wx.GetApp().devices_listpanel = self

    async def load(self):
        self.listctrl.DeleteAllItems()
        device_names = await adb_interface.get_device_names()
        for index, device in enumerate(device_names):
            wx.CallAfter(self.listctrl.InsertItem, index=index, label=device)

    def on_listitem_selected(self, evt: wx.ListEvent):
        index = evt.GetSelection()
        item: wx.ListItem = self.listctrl.GetItem(index, 0)
        device_name = item.GetText()
        self.selected_device = device_name

        async def create_obb_dir():
            """create the data directory on the quest device"""
            result = adb_interface.path_exists(
                device_name=device_name, path=config.QUEST_OBB_DIRECTORY
            )
            if not result:
                adb_interface.make_dir(
                    device_name=device_name, path=config.QUEST_OBB_DIRECTORY
                )

        app = wx.GetApp()
        loop = asyncio.get_event_loop()
        loop.create_task(create_obb_dir())
        loop.create_task(app.install_listpanel.load(device_name))

    def on_right_click(self, evt: wx.ListEvent):
        """creates a popup menu for device list

        Args:
            evt (wx.ListEvent): _description_
        """
        if not self.selected_device:
            return
        menu = wx.Menu()
        debug_menu = wx.Menu()
        copy_dname_item = debug_menu.Append(wx.ID_ANY, "Copy ID to Clipboard")
        self.Bind(wx.EVT_MENU, self.on_copy_device_name, copy_dname_item)
        menu.AppendSubMenu(debug_menu, "Debug")
        self.listctrl.PopupMenu(menu)

    def on_copy_device_name(self, evt: wx.MenuItem):
        """copies the device name to the clipboard

        Args:
            evt (wx.MenuItem):
        """
        if not self.selected_device:
            return
        cpb = wx.Clipboard()
        if not cpb.Open():
            return
        text_data = wx.TextDataObject()
        text_data.SetText(self.selected_device)
        cpb.SetData(text_data)
        cpb.Close()
