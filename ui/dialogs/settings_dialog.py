from typing import Tuple

import wx

from lib.config import Settings


class SettingsDialog(wx.Dialog):
    def __init__(self, parent: wx.Frame, title: str, size: Tuple[int, int]):
        super().__init__(parent, title=title, size=size)

        # Create the scrolled window with vertical scrolling only
        scrolled = wx.ScrolledWindow(self, style=wx.VSCROLL)

        # Create the static box with label "Installation"
        installation_box = wx.StaticBox(scrolled, label="Installation")
        installation_sizer = wx.StaticBoxSizer(installation_box, wx.VERTICAL)

        # Add the checkbox to the static box
        self.delete_files_checkbox = wx.CheckBox(
            installation_box, label="Delete Files after successful Install"
        )
        installation_sizer.Add(self.delete_files_checkbox, 0, wx.ALL, 10)

        # Add the static box sizer to the scrolled window's sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(installation_sizer, 0, wx.ALL | wx.EXPAND, 10)
        scrolled.SetSizer(sizer)

        # Set the scrolled window's virtual size so that it knows how big it should be
        sizer.Fit(scrolled)
        scrolled.SetVirtualSize(sizer.GetMinSize())

        # Add the scrolled window to the dialog's sizer
        dialog_sizer = wx.BoxSizer(wx.VERTICAL)
        dialog_sizer.Add(scrolled, 1, wx.EXPAND | wx.ALL, 10)

        # Add the save and cancel buttons to the dialog's sizer
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        save_button = wx.Button(self, id=wx.ID_OK, label="Save")
        cancel_button = wx.Button(self, id=wx.ID_CANCEL, label="Cancel")
        button_sizer.AddStretchSpacer(1)
        button_sizer.Add(save_button, 0, wx.ALL, 10)
        button_sizer.Add(cancel_button, 0, wx.ALL, 10)
        button_sizer.AddStretchSpacer(1)
        dialog_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 10)

        self.SetSizerAndFit(dialog_sizer)

        # load the settings and initialize the controls
        self._init_controls()

    def _init_controls(self) -> None:
        self.settings = Settings.load()
        self.delete_files_checkbox.SetValue(self.settings.remove_files_after_install)

    def save_from_controls(self) -> None:
        """gets the values from GUI controls and saves them to file"""
        self.settings.remove_files_after_install = self.delete_files_checkbox.GetValue()
        self.settings.save()
