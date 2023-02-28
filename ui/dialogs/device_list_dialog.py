import asyncio
from typing import Tuple, Union

import wx
import wxasync

import ui.panels.devices_listpanel as devices_panel


async def open_device_selection_dialog(
    parent: wx.Frame, id: int, title: str, style: int, size: Tuple[int, int]
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
    dlg = DeviceListDialog(parent=parent, id=id, title=title, style=style, size=size)
    result = await wxasync.AsyncShowDialogModal(dlg=dlg)
    return (result, dlg.selected_device_name)


class DeviceListDialog(wx.Dialog):
    selected_device_name: str = ""

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        try:
            self.device_listpanel = devices_panel.DevicesListPanel(self)
            wxasync.AsyncBind(
                devices_panel.EVT_DEVICE_SELECTED,
                self._on_device_selected,
                self.device_listpanel,
            )
        except Exception as err:
            raise err

        skip_button = wx.Button(self, wx.ID_OK, "Skip")
        wxasync.AsyncBind(wx.EVT_BUTTON, self._on_skip_clicked, skip_button)

        gs = wx.GridSizer(cols=1)
        gs.Add(self.device_listpanel, 1, wx.EXPAND | wx.ALL, 0)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(gs, 1, wx.EXPAND | wx.ALL, 0)
        vbox.Add(skip_button, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        self.SetSizerAndFit(vbox)
        self.SetSize(*self.GetSize())
        self.CenterOnParent()

        asyncio.create_task(self.device_listpanel.load())

    async def _on_skip_clicked(self, evt: wx.CommandEvent) -> None:
        self.SetReturnCode(wx.OK)
        self.Close()

    async def _on_device_selected(self, evt: devices_panel.DeviceEvent) -> None:
        self.selected_device_name = evt.GetDeviceName()
        if self.selected_device_name:
            self.SetReturnCode(wx.OK)
            self.Close()
