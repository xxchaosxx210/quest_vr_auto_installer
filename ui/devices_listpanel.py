import logging
from typing import List

import wx

import lib.config as config
import adblib.errors
import lib.tasks
import lib.quest as quest
from adblib import adb_interface
from ui.listpanel import ListPanel


_Log = logging.getLogger()


class DevicesListPanel(ListPanel):
    def __init__(self, *args, **kwargs):
        from q2gapp import Q2GApp

        self.app: Q2GApp = wx.GetApp()
        # the device that is currently selected in the listctrl
        self.selected_device: str = None
        columns = [{"col": 0, "heading": "Name", "width": 200}]
        super().__init__(title="Devices", columns=columns, *args, **kwargs)
        self.app.devices_listpanel = self

    async def _get_device_names(self) -> List[str]:
        """loads device names either from debug settings or ADB

        Raises: RemoteDeviceError

        Returns:
            List[str]: list of device names if found
        """
        if config.DebugSettings.enabled:
            device_names = config.DebugSettings.device_names
        else:
            device_names = await adb_interface.get_device_names()
        return device_names

    async def load(self):
        self.listctrl.DeleteAllItems()
        try:
            device_names = await self._get_device_names()
        except adblib.errors.RemoteDeviceError as err:
            wx.CallAfter(self.app.exception_handler, err=err)
        else:
            for index, device in enumerate(device_names):
                wx.CallAfter(self.listctrl.InsertItem, index=index, label=device)
        finally:
            return

    def on_listitem_selected(self, evt: wx.ListEvent) -> None:
        """get the selected device name, create an obb path on the remote device
        and load the installed apps

        Args:
            evt (wx.ListEvent):

        Raises:
            err: unhandled exceptions
        """
        index = evt.GetSelection()
        item: wx.ListItem = self.listctrl.GetItem(index, 0)
        device_name = item.GetText()
        # set the global selected device
        self.selected_device = device_name

        async def create_obb_dir():
            """create the data directory on the quest device"""
            try:
                quest.create_obb_path(device_name, config.QUEST_OBB_DIRECTORY)
            except adblib.errors.RemoteDeviceError as err:
                wx.CallAfter(self.app.exception_handler, err=err)
            except Exception as err:
                raise err
            finally:
                return

        try:
            lib.tasks.create_obb_dir_task(create_obb_dir)
        except lib.tasks.TaskIsRunning:
            pass
        # Load the installed apps into the install listctrl
        try:
            lib.tasks.load_installed_task(
                self.app.install_listpanel.load, device_name=device_name
            )
        except lib.tasks.TaskIsRunning:
            pass

    def get_selected_device_name(self) -> str:
        """gets the selected device name

        Returns:
            str: returns None if no device selected
        """
        index = self.listctrl.GetFirstSelected()
        if index < 0:
            return None
        item: wx.ListItem = self.listctrl.GetItem(index, 0)
        device_name = item.GetText()
        return device_name

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
