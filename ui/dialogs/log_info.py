from typing import Tuple
import wx

from qvrapi.schemas import ErrorLog
from lib.utils import format_timestamp_to_str
from ui.utils import TextCtrlStaticBox


class LogInfoDlg(wx.Dialog):
    def __init__(
        self, parent: wx.Frame, log: ErrorLog, size: Tuple[int, int], style: int
    ):
        super().__init__(
            parent=parent, id=-1, title="Error Log Information", style=style
        )

        key_sbox = TextCtrlStaticBox(self, log.key, wx.TE_NO_VSCROLL, "Key")
        uuid_sbox = TextCtrlStaticBox(self, str(log.uuid), wx.TE_NO_VSCROLL, "UUID")
        exception_sbox = TextCtrlStaticBox(
            self, log.exception, wx.TE_MULTILINE, "Exception"
        )
        traceback_sbox = TextCtrlStaticBox(
            self, log.traceback, wx.TE_MULTILINE, "Traceback"
        )
        date_added_sbox = TextCtrlStaticBox(
            self,
            format_timestamp_to_str(log.date_added),
            wx.TE_NO_VSCROLL,
            "Date Created",
        )

        close_btn = wx.Button(self, wx.ID_CLOSE, "Close")
        self.Bind(wx.EVT_BUTTON, lambda *args: self.EndModal(wx.ID_CLOSE), close_btn)

        vbox = wx.BoxSizer(wx.VERTICAL)
        BORDER = 10
        vbox.Add(key_sbox.sizer, 0, wx.EXPAND, BORDER)
        vbox.Add(uuid_sbox.sizer, 0, wx.EXPAND, BORDER)
        vbox.Add(date_added_sbox.sizer, 0, wx.EXPAND, BORDER)
        vbox.Add(exception_sbox.sizer, 1, wx.EXPAND | wx.ALL, BORDER)
        vbox.Add(traceback_sbox.sizer, 1, wx.EXPAND | wx.ALL, BORDER)
        vbox.Add(close_btn, 0, wx.ALIGN_CENTER_HORIZONTAL, BORDER)
        vbox.AddSpacer(BORDER)
        self.SetSizerAndFit(vbox)
        self.SetSize(size)
        self.CenterOnParent()
