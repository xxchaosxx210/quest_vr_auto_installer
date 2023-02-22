from typing import Tuple
import wx


from ui.utils import TextCtrlStaticBox
from qvrapi.schemas import QuestMagnetWithKey
from lib.utils import decode_Base64


class MagnetUpdateFrame(wx.Frame):
    def __init__(
        self,
        parent: wx.Frame,
        title: str,
        size: Tuple[int, int],
        magnet: QuestMagnetWithKey,
    ):
        super().__init__(parent=parent, title=title, size=size)
        """
        class QuestMagnet(BaseModel):
        name: str
        display_name: str
        magnet: str
        version: float
        filesize: int
        date_added: float
        id: str

        @property
        def uri(self) -> str:
            return self.magnet
        """

        panel = wx.Panel(self, -1)

        self.key_sbox = TextCtrlStaticBox(
            panel, magnet.key, wx.TE_READONLY | wx.TE_NO_VSCROLL, "Key"
        )
        self.name_sbox = TextCtrlStaticBox(panel, magnet.name, wx.TE_NO_VSCROLL, "Name")
        self.dis_sbox = TextCtrlStaticBox(
            panel, magnet.display_name, wx.TE_NO_VSCROLL, "Display Name"
        )
        self.mag_sbox = TextCtrlStaticBox(
            panel, decode_Base64(magnet.magnet), wx.TE_NO_VSCROLL, "Magnet Link"
        )
        panel_vbox = wx.BoxSizer(wx.VERTICAL)

        panel_vbox.Add(self.key_sbox.sizer, 0, wx.EXPAND, 0)
        panel_vbox.Add(self.name_sbox.sizer, 0, wx.EXPAND, 0)
        panel_vbox.Add(self.dis_sbox.sizer, 0, wx.EXPAND, 0)
        panel_vbox.Add(self.mag_sbox.sizer, 0, wx.EXPAND, 0)

        update_btn = wx.Button(panel, wx.ID_SAVE, "Update")
        delete_btn = wx.Button(panel, wx.ID_DELETE, "Delete")
        close_btn = wx.Button(panel, wx.ID_CLOSE, "Close")
        self.Bind(wx.EVT_BUTTON, lambda *args: self.Destroy(), close_btn)

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
