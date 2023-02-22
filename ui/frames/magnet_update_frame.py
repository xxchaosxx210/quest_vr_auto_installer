from typing import Tuple
from collections import OrderedDict
import wx


from ui.utils import TextCtrlStaticBox
from qvrapi.schemas import QuestMagnetWithKey
from lib.utils import format_timestamp


class MagnetUpdateFrame(wx.Frame):
    def __init__(
        self,
        parent: wx.Frame,
        title: str,
        size: Tuple[int, int],
        magnet: QuestMagnetWithKey,
    ):
        super().__init__(parent=parent, title=title, size=size)

        panel = wx.Panel(self, -1)

        self.static_txtctrls = self._create_static_text_ctrls(panel, magnet)

        panel_vbox = wx.BoxSizer(wx.VERTICAL)

        for st_txt_ctrl in self.static_txtctrls.values():
            panel_vbox.Add(st_txt_ctrl.sizer, 0, wx.EXPAND, 0)

        update_btn = wx.Button(panel, wx.ID_SAVE, "Update")
        delete_btn = wx.Button(panel, wx.ID_DELETE, "Delete")
        close_btn = wx.Button(panel, wx.ID_CLOSE, "Close")
        self.Bind(wx.EVT_BUTTON, lambda *args: self.Destroy(), close_btn)
        self.Bind(wx.EVT_BUTTON, self._on_update_button, update_btn)
        self.Bind(wx.EVT_BUTTON, self._on_delete_button, delete_btn)

        btn_hbox = wx.BoxSizer(wx.HORIZONTAL)
        btn_hbox.Add(update_btn, 0, wx.EXPAND, 0)
        btn_hbox.Add(delete_btn, 0, wx.EXPAND, 0)
        btn_hbox.Add(close_btn, 0, wx.EXPAND, 0)

        panel_vbox.Add(btn_hbox, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        panel.SetSizerAndFit(panel_vbox)

        gs = wx.GridSizer(cols=1)
        gs.Add(panel, 1, wx.EXPAND | wx.ALL, 0)
        self.SetSizerAndFit(gs)
        self.SetSize(size)

    def _create_static_text_ctrls(
        self, parent: wx.Panel, magnet: QuestMagnetWithKey
    ) -> OrderedDict:
        ctrls = OrderedDict()
        ctrls["key"] = TextCtrlStaticBox(
            parent, magnet.key, wx.TE_READONLY | wx.TE_NO_VSCROLL, "Key"
        )
        ctrls["name"] = TextCtrlStaticBox(parent, magnet.name, wx.TE_NO_VSCROLL, "Name")
        ctrls["display_name"] = TextCtrlStaticBox(
            parent, magnet.display_name, wx.TE_NO_VSCROLL, "Display Name"
        )
        ctrls["magnet"] = TextCtrlStaticBox(
            parent, magnet.decoded_uri, wx.TE_MULTILINE, "Magnet Link"
        )
        ctrls["version"] = TextCtrlStaticBox(
            parent, str(magnet.version), wx.TE_NO_VSCROLL, "Version"
        )
        ctrls["filesize"] = TextCtrlStaticBox(
            parent, f"{magnet.filesize / 1000}", wx.TE_NO_VSCROLL, "FileSize (MB)"
        )
        ctrls["date_added"] = TextCtrlStaticBox(
            parent,
            format_timestamp(magnet.date_added, True),
            wx.TE_NO_VSCROLL,
            "Date Added",
        )
        ctrls["id"] = TextCtrlStaticBox(
            parent, magnet.id, wx.TE_NO_VSCROLL, "Torrent ID"
        )

        return ctrls

    def _on_update_button(self, evt: wx.CommandEvent) -> None:
        evt.Skip()

    def _on_delete_button(self, evt: wx.CommandEvent) -> None:
        evt.Skip()
