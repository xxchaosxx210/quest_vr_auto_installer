import logging

import wx

import lib.config
import lib.tasks
from ui.listpanel import ListPanel
from adblib import adb_interface


_Log = logging.getLogger(__name__)


class InstalledListPanel(ListPanel):
    def __init__(self, *args, **kw):
        from q2gapp import Q2GApp

        self.app: Q2GApp = wx.GetApp()
        columns = [{"col": 0, "heading": "Name", "width": 100}]
        super().__init__(title="Installed Games", columns=columns, *args, **kw)

        self.app.install_listpanel = self

    async def load(self, device_name: str):
        if lib.config.DebugSettings.enabled:
            package_names = lib.config.DebugSettings.package_names
        else:
            package_names = await adb_interface.get_installed_packages(
                device_name, ["-3"]
            )
        package_names.sort()
        self.listctrl.DeleteAllItems()
        for index, package_name in enumerate(package_names):
            wx.CallAfter(self.listctrl.InsertItem, index=index, label=package_name)

    def on_right_click(self, evt: wx.ListEvent):
        menu = wx.Menu()
        uninstall_item = menu.Append(wx.ID_ANY, "Uninstall")
        self.Bind(wx.EVT_MENU, self.on_uninstall, uninstall_item)
        self.listctrl.PopupMenu(menu)

    def on_uninstall(self, evt: wx.MenuEvent):
        # handle the uninstall event here
        try:
            package_name = self.get_package_name()
        except IndexError:
            return
        try:
            lib.tasks.remove_package_task(
                self.app.remove_package, package_name=package_name
            )
        except lib.tasks.TaskIsRunning as err:
            wx.MessageBox(err.__str__(), "Uninstall issue")

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
