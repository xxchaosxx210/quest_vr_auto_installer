import logging
from typing import List

import wx

import adblib.errors
import ui.utils
import lib.tasks
import lib.debug as debug
from adblib import adb_interface
from ui.panels.listpanel import ListPanel, ColumnListType
from ui.dialogs.add_fake_device_dialog import AddFakeDeviceDialog


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


class DevicesListPanel(ListPanel):
    def __init__(self, parent: wx.Window):
        from q2gapp import Q2GApp

        self.app: Q2GApp = wx.GetApp()
        # the device that is currently selected in the listctrl
        columns: ColumnListType = [{"col": 0, "heading": "Name", "width": 200}]
        super().__init__(parent=parent, title="Devices", columns=columns)
        self.insert_button_panel(self._create_button_panel(), 0, flag=wx.ALIGN_RIGHT)

    def _create_button_panel(self) -> wx.Panel:
        # create the button panel
        button_panel = wx.Panel(self, -1)

        # create the buttons and store them into the super classes bitmap_buttons dict
        if self.app.debug_mode:
            self.bitmap_buttons["remove"] = ui.utils.create_bitmap_button(
                "uninstall.png", "Remove Fake Device", button_panel, size=(24, 24)
            )
            self.bitmap_buttons["add"] = ui.utils.create_bitmap_button(
                "add.png", "Add Fake Device", button_panel, size=(24, 24)
            )
            self.Bind(wx.EVT_BUTTON, self.dbg_add_device, self.bitmap_buttons["add"])
            self.Bind(
                wx.EVT_BUTTON,
                self.dbg_remove_device,
                self.bitmap_buttons["remove"],
            )
        self.bitmap_buttons["refresh"] = ui.utils.create_bitmap_button(
            "refresh.png", "Refresh Games List", button_panel, size=(24, 24)
        )
        self.Bind(wx.EVT_BUTTON, self.on_refresh_click, self.bitmap_buttons["refresh"])

        hbox_btns = ListPanel.create_bitmap_button_sizer(self.bitmap_buttons, border=10)
        button_panel.SetSizer(hbox_btns)
        return button_panel

    def dbg_remove_device(self, evt: wx.CommandEvent) -> None:
        index = self.listctrl.GetFirstSelected()
        if index == -1:
            return
        device_name = self.listctrl.GetItem(index, 0).GetText()
        index = debug.get_index_by_device_name(debug.fake_quests, device_name)
        if index is None:
            _Log.info("device not found in debug.fake_quests")
            return
        debug.fake_quests.pop(index)

    def dbg_add_device(self, evt: wx.CommandEvent) -> None:
        """add a fake device to the device list"""

        with AddFakeDeviceDialog(self) as dialog:
            result = dialog.ShowModal()
            if result == wx.ID_OK:
                device_name, package_names = dialog.get_values_from_dialog()
                debug.fake_quests.append(debug.FakeQuest(device_name, package_names))
            lib.tasks.check_task_and_create(self.load)

    def on_refresh_click(self, evt: wx.CommandEvent) -> None:
        """reload the device list from ADB daemon"""
        lib.tasks.check_task_and_create(self.load)

    async def _get_device_names(self) -> List[str]:
        """loads device names either from debug settings or ADB

        Raises: RemoteDeviceError

        Returns:
            List[str]: list of device names if found
        """
        if self.app.debug_mode:
            device_names = debug.get_device_names(debug.fake_quests)
        else:
            device_names = await adb_interface.get_device_names()
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

        # async def create_obb_dir():
        #     """create the data directory on the quest device"""
        #     try:
        #         quest.create_obb_path(device_name, config.QUEST_OBB_DIRECTORY)
        #     except adblib.errors.RemoteDeviceError as err:
        #         wx.CallAfter(self.app.exception_handler, err=err)
        #     except Exception as err:
        #         raise err
        #     finally:
        #         return

        # try:
        #   lib.tasks.check_task_and_create(create_obb_dir)
        # except lib.tasks.TaskIsRunning:
        #     pass
        # # Load the installed apps into the install listctrl
        # if self.app.install_listpanel is not None:
        #     try:
        #         lib.tasks.check_task_and_create(
        #             self.app.install_listpanel.load, device_name=device_name
        #         )
        #     except lib.tasks.TaskIsRunning:
        #         pass

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
