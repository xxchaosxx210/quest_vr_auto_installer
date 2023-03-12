import logging

import wx

import lib.config
import lib.tasks
import ui.utils
import lib.debug as debug
from ui.panels.listctrl_panel import ListCtrlPanel, ColumnListType
from adblib import adb_interface


_Log = logging.getLogger(__name__)


class InstalledListPanel(ListCtrlPanel):
    def __init__(self, parent: wx.Window):
        from quest_cave_app import QuestCaveApp

        self.app: QuestCaveApp = wx.GetApp()
        columns: ColumnListType = [{"col": 0, "heading": "Name", "width": 100}]
        super().__init__(
            parent=parent, title="Installed Games", columns=columns, toggle_col=False
        )

        self.app.install_listpanel = self

        self.insert_button_panel(self._create_button_panel(), 0, flag=wx.ALIGN_RIGHT)

    def _create_button_panel(self) -> wx.Panel:
        # create the button panel
        button_panel = wx.Panel(self, -1)

        # create the buttons and store them into the super classes bitmap_buttons dict
        self.bitmap_buttons["refresh"] = ui.utils.create_bitmap_button(
            "refresh.png", "Refresh Apps on the device", button_panel
        )
        self.bitmap_buttons["uninstall"] = ui.utils.create_bitmap_button(
            "uninstall.png", "Uninstall App", button_panel
        )
        self.Bind(
            wx.EVT_BUTTON, self.on_uninstall_click, self.bitmap_buttons["uninstall"]
        )

        hbox_btns = ListCtrlPanel.create_bitmap_button_sizer(self.bitmap_buttons)
        button_panel.SetSizer(hbox_btns)
        return button_panel

    async def load(self, device_name: str) -> None:
        """get the installed packages from the device_name string using the ADB interface.
        device_name cannot be empty string

        Args:
            device_name (str): the name of the device to get the installed packages from

        Raises:
            ValueError: device_name is an empty string then exception is raised
            LookupError: (Debug mode only) if device_name cant be found then this will be raised
        """
        self.listctrl.DeleteAllItems()
        if not device_name:
            return
        if self.app.debug_mode:
            try:
                fake_quest = debug.get_device(debug.FakeQuest.devices, device_name)
            except LookupError:
                _Log.error(f"No device found with name {device_name}")
                return
            else:
                package_names = fake_quest.package_names
        else:
            package_names = await adb_interface.get_installed_packages(
                device_name, ["-3"]
            )
        package_names.sort()
        for index, package_name in enumerate(package_names):
            wx.CallAfter(self.listctrl.InsertItem, index=index, label=package_name)

    def on_right_click(self, evt: wx.ListEvent):
        menu = wx.Menu()
        uninstall_item = menu.Append(wx.ID_ANY, "Uninstall")
        self.Bind(wx.EVT_MENU, self.on_uninstall, uninstall_item)
        self.listctrl.PopupMenu(menu)

    def uninstall(self) -> None:
        # handle the uninstall event here
        try:
            package_name = self.get_package_name()
        except IndexError:
            return
        try:
            lib.tasks.check_task_and_create(
                self.app.remove_package, package_name=package_name
            )
        except lib.tasks.TaskIsRunning as err:
            wx.MessageBox(err.__str__(), "Uninstall issue")

    def on_uninstall(self, evt: wx.MenuEvent):
        self.uninstall()

    def on_uninstall_click(self, evt: wx.CommandEvent) -> None:
        self.uninstall()

    def get_package_name(self) -> str:
        """gets the package name from the selected item in the listctrl

        Raises:
            IndexError: raises if no package item is selected

        Returns:
            str: package name
        """
        index: int = self.listctrl.GetFirstSelected()
        if index < 0:
            raise IndexError("No Package selected")
        listitem: wx.ListItem = self.listctrl.GetItem(index, 0)
        package_name: str = listitem.GetText()
        return package_name

    def search_installed_games(self, text: str) -> None:
        """search the installed games for the text string
        and select the row if it is found

        Args:
            text (str): the text to search
        """
        self.find_text_and_select_column(0, text)
