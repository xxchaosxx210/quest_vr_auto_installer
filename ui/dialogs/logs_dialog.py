import asyncio

from typing import Tuple

import wx


from ui.utils import ListCtrlPanel


class LogsListCtrlPanel(ListCtrlPanel):
    pass


class LogsDialog(wx.Dialog):
    def __init__(self, parent: wx.Window, size: Tuple[int, int] = wx.DefaultSize):
        super().__init__(
            parent=parent,
            style=wx.DEFAULT_DIALOG_STYLE | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX,
        )

        columns = [
            {"col": 0, "heading": "Type", "width": 50},
            {"col": 1, "heading": "UUID", "width": 120},
            {"col": 2, "heading": "Traceback", "width": 120},
            {"col": 3, "heading": "Exception", "width": 120},
            {"col": 4, "heading": "Date Added", "width": 50},
        ]
        self.logslstctrl_panel = LogsListCtrlPanel(
            parent=self, columns=columns, title="Errors"
        )
        close_btn = wx.Button(self, wx.ID_CLOSE, "Close")

        self.Bind(wx.EVT_BUTTON, self._on_close_button, close_btn)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.logslstctrl_panel, 1, wx.ALL | wx.EXPAND, 10)
        vbox.Add(close_btn, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)
        vbox.AddSpacer(10)
        self.SetSizerAndFit(vbox)
        self.SetSize(size)
        self.CenterOnParent()

    async def load_list(self) -> None:
        pass

    def _on_close_button(self, evt: wx.CommandEvent) -> None:
        if self.IsModal():
            self.EndModal(wx.ID_CLOSE)
            return
        self.Destroy()
