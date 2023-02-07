import logging
import asyncio

import wx

from ui.listpanel import ListPanel

from adblib import adb_interface


_Log = logging.getLogger(__name__)


class InstalledListPanel(ListPanel):
    def __init__(self, *args, **kw):
        columns = [{"col": 0, "heading": "Name", "width": 100}]
        super().__init__(title="Installed Games", columns=columns, *args, **kw)

        wx.GetApp().install_listpanel = self

    async def load(self, device_name: str):
        package_names = await adb_interface.get_installed_packages(device_name, ["-3"])
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
        app = wx.GetApp()
        asyncio.get_event_loop().create_task(app.remove_package(package_name))

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
