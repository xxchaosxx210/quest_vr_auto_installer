import logging
from typing import List

import wx

import adblib.errors
import ui.utils
import lib.tasks
import lib.debug as debug
from adblib import adb_interface
from ui.panels.listctrl_panel import ListCtrlPanel, ColumnListType
from ui.dialogs.fake_device import FakeDeviceDlg


_Log = logging.getLogger()


newEVT_DEVICE_SELECTED = wx.NewEventType()
EVT_DEVICE_SELECTED = wx.PyEventBinder(newEVT_DEVICE_SELECTED, 1)


class DeviceEvent(wx.PyCommandEvent):
    def __init__(self, event_type: int, id: int, index: int, device_name: str = ""):
        super().__init__(event_type, id)
        self.DeviceName = device_name
        self._device_name = device_name
        self.Index = index
        self._index = index

    def GetIndex(self) -> int:
        return self._index

    def GetDeviceName(self) -> str:
        return self._device_name


class DevicesListPanel(ListCtrlPanel):
    def __init__(self, parent: wx.Window):
        from quest_cave_app import QuestCaveApp

        self.app: QuestCaveApp = wx.GetApp()
        # the device that is currently selected in the listctrl
        columns: ColumnListType = [{"col": 0, "heading": "Name", "width": 200}]
        super().__init__(
            parent=parent, title="Devices", columns=columns, toggle_col=False
        )
        self.insert_button_panel(self._create_button_panel(), 0, flag=wx.ALIGN_RIGHT)

    def _create_button_panel(self) -> wx.Panel:
        # create the button panel
        button_panel = wx.Panel(self, -1)

        # create the buttons and store them into the super classes bitmap_buttons dict
        if self.app.debug_mode:
            self.bitmap_buttons["remove"] = ui.utils.create_bitmap_button(
                "uninstall.png", "Remove Fake Device", button_panel, size=(24, 24)
            )
            self.bitmap_buttons["random-generate"] = ui.utils.create_bitmap_button(
                "random.png", "Random Generate", button_panel, size=(24, 24)
            )
            self.bitmap_buttons["add"] = ui.utils.create_bitmap_button(
                "add.png", "Add Fake Device", button_panel, size=(24, 24)
            )
            self.Bind(wx.EVT_BUTTON, self.dbg_add_device, self.bitmap_buttons["add"])
            self.Bind(
                wx.EVT_BUTTON,
                self.dbg_random_generate,
                self.bitmap_buttons["random-generate"],
            )
            self.Bind(
                wx.EVT_BUTTON,
                self.dbg_remove_device,
                self.bitmap_buttons["remove"],
            )

        hbox_btns = ListCtrlPanel.create_bitmap_button_sizer(
            self.bitmap_buttons, border=10
        )
        button_panel.SetSizer(hbox_btns)
        return button_panel

    def dbg_random_generate(self, evt: wx.CommandEvent) -> None:
        """randomly generate a fake device and add it to the list

        Args:
            evt (wx.CommandEvent): not used
        """
        # get the fake quests from the debug module
        quests = debug.FakeQuest.devices
        # generate a random device name
        name = debug.FakeQuest.generate_random_device_name(quests)
        # generate a random list of packages
        packages = debug.FakeQuest.generate_random_packages()
        # add the device to the debug module
        debug.FakeQuest.add_device(name, packages)
        # reload the device list
        lib.tasks.check_task_and_create(self.load)

    def dbg_remove_device(self, evt: wx.CommandEvent) -> None:
        """remove a fake device from the list"""
        index = self.listctrl.GetFirstSelected()
        if index == -1:
            return
        device_name = self.listctrl.GetItem(index, 0).GetText()
        index = debug.get_index_by_device_name(debug.FakeQuest.devices, device_name)
        if index is None:
            _Log.info("device not found in debug.FakeQuest.devices")
            return
        debug.FakeQuest.devices.pop(index)

    def dbg_add_device(self, evt: wx.CommandEvent) -> None:
        """add a fake device to the device list"""

        with FakeDeviceDlg(self) as dialog:
            result = dialog.ShowModal()
            if result == wx.ID_OK:
                device_name, package_names = dialog.get_values_from_dialog()
                debug.FakeQuest.add_device(device_name, package_names)
            lib.tasks.check_task_and_create(self.load)

    async def _get_device_names(self) -> List[str]:
        """loads device names either from debug settings or ADB

        Raises: RemoteDeviceError

        Returns:
            List[str]: list of device names if found
        """
        if self.app.debug_mode:
            device_names = debug.get_device_names(debug.FakeQuest.devices)
        else:
            device_names = await adb_interface.async_get_device_names()
        return device_names

    def load_listctrl(self, device_names: List[str]) -> None:
        self.listctrl.DeleteAllItems()
        for index, device in enumerate(device_names):
            wx.CallAfter(self.listctrl.InsertItem, index=index, label=device)

    async def load(self) -> None:
        """load the device names from ADB daemon

        Raises:
            err: RemoteDeviceError | Exception
        """
        # Clear the Device list
        self.listctrl.DeleteAllItems()
        self.app.set_selected_device("")
        try:
            device_names = await self._get_device_names()
        except adblib.errors.RemoteDeviceError as err:
            wx.CallAfter(self.app.exception_handler, err=err)
        except Exception as err:
            raise err
        else:
            # everything went ok insert the device names into the device listctrl
            for index, device in enumerate(device_names):
                wx.CallAfter(self.listctrl.InsertItem, index=index, label=device)
        finally:
            pass

    def on_item_double_click(self, evt: wx.ListEvent) -> None:
        """get the selected device name, create an obb path on the remote device
        and load the installed apps

        Args:
            evt (wx.ListEvent):

        Raises:
            err: unhandled exceptions
        """
        index = self.listctrl.GetFirstSelected()
        if index == -1:
            return
        item: wx.ListItem = self.listctrl.GetItem(index, 0)
        device_name = item.GetText()
        # set the global selected device
        self.app.set_selected_device(device_name)
        event = DeviceEvent(newEVT_DEVICE_SELECTED, self.GetId(), index, device_name)
        # wx.PostEvent(self.GetEventHandler(), event)
        handler: wx.Window = self.GetEventHandler()
        if isinstance(handler, wx.Window):
            handler.ProcessEvent(event)

    def get_selected_device_name(self) -> str | None:
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
        if not self.app.monitoring_device_thread.get_selected_device():
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
        if not self.app.monitoring_device_thread.get_selected_device():
            return
        cpb = wx.Clipboard()
        if not cpb.Open():
            return
        text_data = wx.TextDataObject()
        text_data.SetText(self.app.monitoring_device_thread.get_selected_device())
        cpb.SetData(text_data)
        cpb.Close()
