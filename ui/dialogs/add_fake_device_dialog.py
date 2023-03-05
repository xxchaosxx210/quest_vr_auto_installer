from typing import List, Tuple
import random

import wx

import lib.debug as debug


class AddFakeDeviceDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        self._do_properties()
        self._create_controls()
        self._do_layout()
        self._bind_events()

    def _do_properties(self) -> None:
        self.SetTitle("Add Fake Device")
        self.SetSize((300, 300))

    def _bind_events(self) -> None:
        self.Bind(wx.EVT_BUTTON, self.on_add_button_click, self.add_button)
        self.Bind(wx.EVT_BUTTON, self.on_gen_quest_button_click, self.gen_quest_button)
        self.Bind(wx.EVT_BUTTON, self.on_ok_button_click, self.ok_button)
        self.Bind(wx.EVT_BUTTON, self.on_cancel_button_click, self.cancel_button)

    def _create_controls(self) -> None:
        self.device_name_textctrl = wx.TextCtrl(self, -1, "")
        self.package_name_textctrl = wx.TextCtrl(self, -1, "")
        self.package_name_listbox = wx.ListBox(self, -1, size=(400, 100))
        self.gen_quest_button = wx.Button(self, -1, "Generate Quest")
        self.add_button = wx.Button(self, -1, "Add")
        self.ok_button = wx.Button(self, -1, "OK")
        self.cancel_button = wx.Button(self, -1, "Cancel")

    def _do_layout(self) -> None:
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.device_name_sizer = wx.StaticBoxSizer(
            wx.HORIZONTAL, self, label="Device Name"
        )
        self.package_name_sizer = wx.StaticBoxSizer(
            wx.VERTICAL, self, label="Package Names"
        )
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.qlist_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # add the controls to the sizers
        self.device_name_sizer.Add(self.device_name_textctrl, 1, wx.ALL | wx.EXPAND, 5)
        self.package_name_sizer.Add(
            self.package_name_textctrl, 0, wx.ALL | wx.EXPAND, 5
        )
        self.package_name_sizer.Add(self.package_name_listbox, 1, wx.ALL | wx.EXPAND, 5)
        self.qlist_btn_sizer.Add(self.gen_quest_button, 0, wx.ALL, 5)
        self.qlist_btn_sizer.Add(self.add_button, 0, wx.ALL, 5)
        self.package_name_sizer.Add(self.qlist_btn_sizer, 0, wx.ALL, 5)
        self.button_sizer.Add(self.ok_button, 0, wx.ALL, 5)
        self.button_sizer.Add(self.cancel_button, 0, wx.ALL, 5)

        # add the sizers to the main sizer
        self.main_sizer.Add(self.device_name_sizer, 0, wx.EXPAND, 5)
        self.main_sizer.Add(self.package_name_sizer, 1, wx.ALL | wx.EXPAND, 5)
        self.main_sizer.Add(self.button_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL, 5)

        # set the main sizer
        self.SetSizer(self.main_sizer)

    def on_add_button_click(self, event: wx.CommandEvent) -> None:
        package_name = self.package_name_textctrl.GetValue()
        self.package_name_listbox.Append(package_name)
        self.package_name_textctrl.Clear()

    def on_ok_button_click(self, event: wx.CommandEvent) -> None:
        self.EndModal(wx.ID_OK)

    def on_cancel_button_click(self, event: wx.CommandEvent) -> None:
        self.EndModal(wx.ID_CANCEL)

    def on_gen_quest_button_click(self, event: wx.CommandEvent) -> None:
        """generates a random quest device name and package names

        Args:
            event (wx.CommandEvent):
        """
        # get the global fake quest list
        quests = debug.FakeQuest.devices
        # generate a random device name
        name = debug.FakeQuest.generate_random_device_name(quests)
        # generate a random list of package names
        packages = debug.FakeQuest.generate_random_packages()
        # set the values in the dialog
        self.device_name_textctrl.SetValue(name)
        self.package_name_listbox.Clear()
        self.package_name_listbox.AppendItems(packages)

    def get_values_from_dialog(self) -> Tuple[str, List[str]]:
        """gets the device_name and package_names list from the dialog

        Returns:
            Tuple[str, List[str]]: device_name and the package names
        """
        device_name = self.device_name_textctrl.GetValue()
        package_names = []
        for i in range(self.package_name_listbox.GetCount()):
            package_names.append(self.package_name_listbox.GetString(i))
        return device_name, package_names
