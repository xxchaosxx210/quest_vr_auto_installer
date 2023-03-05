from typing import Tuple

import wx
import wxasync

import ui.panels.devices_listpanel as devices_panel


async def open_device_selection_dialog(
    parent: wx.Frame, id: int, title: str, style: int
) -> Tuple[int, str]:
    """creates an async modal dialog

    Args:
        parent (wx.Frame): parent frame
        id (int):
        title (str): title of the dialog
        style (int): the dialog style
        size (Tuple[int, int]): size of the dialog

    Returns:
        Tuple[int, str]: return code and selected device name
    """
    dlg = DeviceListDlg(parent=parent, id=id, title=title, style=style)
    result = await wxasync.AsyncShowDialogModal(dlg=dlg)
    return (result, dlg.get_device_name())


class DeviceListDlg(wx.Dialog):
    instance: "DeviceListDlg | None" = None

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._selected_device_name: str = ""
        # store an instance of the dialog when it is created as this will be
        # used in the App to see if the dialog is open
        DeviceListDlg.instance = self
        self.device_listpanel = devices_panel.DevicesListPanel(self)
        # custom event when a device name is selected
        wxasync.AsyncBind(
            devices_panel.EVT_DEVICE_SELECTED,
            self._on_device_selected,
            self.device_listpanel,
        )

        skip_button = wx.Button(self, wx.ID_OK, "Skip")
        wxasync.AsyncBind(wx.EVT_BUTTON, self._on_skip_clicked, skip_button)

        gs = wx.GridSizer(cols=1)
        gs.Add(self.device_listpanel, 1, wx.EXPAND | wx.ALL, 0)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(gs, 1, wx.EXPAND | wx.ALL, 0)
        vbox.Add(skip_button, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        self.SetSizerAndFit(vbox)
        parent_width, parent_height = self.GetParent().GetSize()
        self.SetSize(int(parent_width * 0.6), int(parent_height * 0.6))
        self.CenterOnParent()

        # capture the dialog show event
        # hackish way at the moment. this resets the device names in the background
        # thread which is monitoring for new devices and whether the user
        # has disconnected their device
        wxasync.AsyncBind(wx.EVT_SHOW, self._on_show, self)

    async def _on_show(self, evt: wx.ShowEvent) -> None:
        wx.GetApp().monitoring_device_thread.refresh_device_list()

    async def _on_skip_clicked(self, evt: wx.CommandEvent) -> None:
        self.SetReturnCode(wx.OK)
        self.Close()

    async def _on_device_selected(self, evt: devices_panel.DeviceEvent) -> None:
        self._selected_device_name = evt.GetDeviceName()
        if self._selected_device_name:
            self.SetReturnCode(wx.OK)
            self.Close()

    def get_device_name(self) -> str:
        return self._selected_device_name

    def Close(self, force=False):
        self.instance = None
        return super().Close(force)
