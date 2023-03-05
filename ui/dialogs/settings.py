from typing import Tuple

import wx

from lib.settings import Settings


class DownloadPathPanel(wx.Panel):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        self.downloadctrl = wx.TextCtrl(
            self, size=(300, -1), style=wx.TE_NO_VSCROLL | wx.TE_READONLY
        )
        self.browse_button = wx.Button(self, -1, "Browse", size=(100, -1))
        self.Bind(wx.EVT_BUTTON, self._on_browse_button, self.browse_button)

        hs = wx.BoxSizer(wx.HORIZONTAL)

        hs.Add(self.downloadctrl, 1, wx.ALL | wx.EXPAND, 10)
        hs.Add(self.browse_button, 0, wx.EXPAND | wx.ALL, 10)

        vs = wx.BoxSizer(wx.VERTICAL)
        vs.Add(hs, 1, wx.ALL | wx.EXPAND, 0)

        self.SetSizer(vs)

    def set_path(self, path: str) -> None:
        self.downloadctrl.SetValue(path)

    def get_path(self) -> str:
        return self.downloadctrl.GetValue()

    def _on_browse_button(self, evt: wx.CommandEvent) -> None:
        """load the DirDialog and prompt for new download path

        Args:
            evt (wx.CommandEvent): ignored
        """
        path = Settings.load().download_path
        with wx.DirDialog(self, defaultPath=path, style=wx.DD_DEFAULT_STYLE) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.downloadctrl.SetValue(dlg.GetPath())


class SettingsDlg(wx.Dialog):
    def __init__(self, parent: wx.Frame, title: str, size: Tuple[int, int]):
        super().__init__(parent, title=title, size=size)

        # Create the scrolled window with vertical scrolling only
        scrolled = wx.ScrolledWindow(self, style=wx.VSCROLL)

        download_path_box = wx.StaticBox(scrolled, label="Download Path")
        download_path_box_sizer = wx.StaticBoxSizer(download_path_box, wx.HORIZONTAL)
        self.download_path_panel = DownloadPathPanel(download_path_box)
        download_path_box_sizer.Add(self.download_path_panel, 1, wx.ALL, 10)

        # Create the static box with label "Installation"
        installation_box = wx.StaticBox(scrolled, label="Installation")
        installation_sizer = wx.StaticBoxSizer(installation_box, wx.VERTICAL)

        # Add the checkbox to the static box
        self.download_only_checkbox = wx.CheckBox(
            installation_box, label="Download only"
        )
        self.delete_files_checkbox = wx.CheckBox(
            installation_box, label="Delete Files after successful Install"
        )
        self.close_dialog_checkbox = wx.CheckBox(
            installation_box, label="Close Dialog after Install Complete"
        )
        installation_sizer.Add(self.download_only_checkbox, 0, wx.ALL, 10)
        installation_sizer.Add(self.delete_files_checkbox, 0, wx.ALL, 10)
        installation_sizer.Add(self.close_dialog_checkbox, 0, wx.ALL, 10)

        # Add the static box sizer to the scrolled window's sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(download_path_box_sizer, 0, wx.ALL | wx.EXPAND, 10)
        sizer.Add(installation_sizer, 1, wx.ALL | wx.EXPAND, 10)
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

        self.CenterOnParent()

        # load the settings and initialize the controls
        self._init_controls()

    def _init_controls(self) -> None:
        settings = Settings.load()
        self.download_only_checkbox.SetValue(settings.download_only)
        self.delete_files_checkbox.SetValue(settings.remove_files_after_install)
        self.close_dialog_checkbox.SetValue(settings.close_dialog_after_install)
        self.download_path_panel.set_path(settings.download_path)

    def save_from_controls(self) -> None:
        """gets the values from GUI controls and saves them to file"""
        settings = Settings.load()
        settings.remove_files_after_install = self.delete_files_checkbox.GetValue()
        settings.close_dialog_after_install = self.close_dialog_checkbox.GetValue()
        settings.download_only = self.download_only_checkbox.GetValue()
        settings.download_path = self.download_path_panel.get_path()
        settings.save()
