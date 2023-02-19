import wx


class TextCtrlStaticBox(wx.StaticBox):
    def __init__(
        self, parent: wx.Window, texctrl_value: str, textctrl_style: int, label: str
    ):
        super().__init__(parent=parent, label=label)

        self.textctrl = wx.TextCtrl(
            self, id=-1, value=texctrl_value, style=textctrl_style
        )

        self.sizer = wx.StaticBoxSizer(self, wx.VERTICAL)
        self.sizer.Add(self.textctrl, flag=wx.EXPAND | wx.ALL, border=0)

    def get_text(self) -> str:
        return self.textctrl.GetValue()
