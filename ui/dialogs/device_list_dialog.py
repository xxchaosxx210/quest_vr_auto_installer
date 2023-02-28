from typing import Tuple
import wx
import wxasync


from ui.panels.devices_listpanel import DevicesListPanel


async def open_device_selection_dialog(
    parent: wx.Frame, id: int, title: str, style: int, size: Tuple[int, int]
) -> int:
    dlg = DeviceListDialog(parent=parent, id=id, title=title, style=style, size=size)
    result = await wxasync.AsyncShowDialogModal(dlg=dlg)
    dlg.Destroy()
    return result


class DeviceListDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        try:
            self.device_listpanel = DevicesListPanel(self)
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

    async def _on_skip_clicked(self, evt: wx.CommandEvent) -> None:
        self.SetReturnCode(wx.OK)
        self.Close()
