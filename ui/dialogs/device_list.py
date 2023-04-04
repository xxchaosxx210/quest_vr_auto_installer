from typing import Tuple

import wx
import wxasync

import ui.panels.devices_listpanel as devices_panel
import ui.consts
from ui.ctrls.bitmap_button_label import BitmapButtonLabel


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
    """dialog for selecting a Quest 2 device"""

    # store an instance of the dialog when it is created as this will be used in the App
    __instance: "DeviceListDlg | None" = None

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.__do_set_properties()
        self.__do_create_controls()
        self.__do_bind_events()
        self.__do_layout()

    def __do_create_controls(self):
        self.device_listpanel = devices_panel.DevicesListPanel(self)
        bmp = wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_BUTTON)
        self._skip_btn = BitmapButtonLabel(
            self, wx.ID_OK, "Skip", bmp, (10, 10), (100, 30)
        )

    def __do_bind_events(self):
        # custom event when a device name is selected
        wxasync.AsyncBind(
            devices_panel.EVT_DEVICE_SELECTED,
            self._on_device_selected,
            self.device_listpanel,
        )
        wxasync.AsyncBind(wx.EVT_BUTTON, self._on_skip_clicked, self._skip_btn)
        # capture the dialog show event
        # hackish way at the moment. this resets the device names in the background
        # thread which is monitoring for new devices and whether the user
        # has disconnected their device
        wxasync.AsyncBind(wx.EVT_SHOW, self._on_show, self)

    def __do_layout(self):
        dev_lstpnl_hbox = wx.BoxSizer(wx.HORIZONTAL)
        dev_lstpnl_hbox.Add(self.device_listpanel, 1, wx.EXPAND | wx.ALL, 0)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(dev_lstpnl_hbox, 1, wx.EXPAND | wx.ALL, 0)
        vbox.Add(self._skip_btn, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        vbox.AddSpacer(ui.consts.LARGE_BORDER)
        self.SetSizerAndFit(vbox)
        # set the size of the dialog to 60% of the parent frame
        parent_width, parent_height = self.GetParent().GetSize()
        self.SetSize(int(parent_width * 0.6), int(parent_height * 0.6))
        self.CenterOnParent()

    def __do_set_properties(self):
        self._selected_device_name: str = ""
        # store an instance of the dialog when it is created as this will be
        # used in the App to see if the dialog is open
        DeviceListDlg.set_global_instance(self)

    async def _on_show(self, evt: wx.ShowEvent) -> None:
        wx.GetApp().monitoring_device_thread.refresh_device_list()

    async def _on_skip_clicked(self, evt: wx.CommandEvent) -> None:
        self.SetReturnCode(wx.OK)
        self.Close()

    async def _on_device_selected(self, evt: devices_panel.DeviceEvent) -> None:
        """device name has been double clicked get the string value and close the dialog

        Args:
            evt (devices_panel.DeviceEvent): device name seelection name
        """
        self._selected_device_name = evt.GetDeviceName()
        if self._selected_device_name:
            self.SetReturnCode(wx.OK)
            self.Close()

    def get_device_name(self) -> str:
        return self._selected_device_name

    def Close(self, force=False):
        DeviceListDlg.set_global_instance(None)
        return super().Close(force)

    @staticmethod
    def set_global_instance(instance: "DeviceListDlg | None") -> None:
        DeviceListDlg.__instance = instance

    @staticmethod
    def get_global_instance() -> "DeviceListDlg | None":
        return DeviceListDlg.__instance
