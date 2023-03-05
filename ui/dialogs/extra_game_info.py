import wx
from typing import List, Tuple


class GridInfoPanel(wx.Panel):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        self.name_label = wx.StaticText(self, -1, "Name: ")
        self.name_value = wx.StaticText(self, -1, "This is a Test")

        gs = wx.GridSizer(cols=2)
        gs.Add(self.name_label, 1, wx.ALL | wx.EXPAND, 0)
        gs.Add(self.name_value, 1, wx.ALL | wx.EXPAND, 0)

        self.SetSizerAndFit(gs)


class ExtraGameInfoDlg(wx.Dialog):
    def __init__(self, parent: wx.Window, size: Tuple[int, int]) -> None:
        super().__init__(parent, title="Extra Game Info", size=size)

        self.info_panel = GridInfoPanel(self)

        paths_sbox = wx.StaticBox(self, -1, "Paths")
        paths_sbox_sizer = wx.StaticBoxSizer(paths_sbox, wx.VERTICAL)

        self.paths_list_box = wx.ListBox(paths_sbox, -1, choices=[])
        paths_sbox_sizer.Add(self.paths_list_box, 1, wx.EXPAND | wx.ALL, 0)

        close_btn = wx.Button(self, -1, "Close")
        self.Bind(wx.EVT_BUTTON, lambda *args: self.EndModal(wx.CLOSE), close_btn)

        vbox = wx.BoxSizer(wx.VERTICAL)

        vbox.Add(self.info_panel, 1, wx.EXPAND | wx.ALL, 10)
        vbox.Add(paths_sbox_sizer, 1, wx.EXPAND | wx.ALL, 10)
        vbox.Add(close_btn, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        self.SetSizerAndFit(vbox)
        self.SetSize(size)
        self.CenterOnParent()

    def set_name(self, name: str) -> None:
        self.info_panel.name_value.SetLabel(name)

    def set_paths(self, paths: List[str]) -> None:
        self.paths_list_box.Set(paths)
