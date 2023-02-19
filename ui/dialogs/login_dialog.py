import wx

from ui.utils import TextCtrlStaticBox


class LoginDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        username_sbox = TextCtrlStaticBox(self, "", wx.TE_PROCESS_TAB, label="Username")
        password_sbox = TextCtrlStaticBox(self, "", wx.TE_PASSWORD, label="Password")

        submit_button = wx.Button(self, -1, "Submit")
        self.Bind(
            wx.EVT_BUTTON,
            lambda *args: wx.MessageBox("You pressed the submit button"),
            submit_button,
        )
        cancel_button = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.Bind(wx.EVT_BUTTON, lambda *args: self.EndModal(wx.CANCEL), cancel_button)

        gs = wx.GridSizer(cols=1)

        gs.Add(username_sbox.sizer, 1, wx.EXPAND | wx.ALL, 10)
        gs.Add(password_sbox.sizer, 1, wx.ALL | wx.EXPAND, 10)

        vbox = wx.BoxSizer(wx.VERTICAL)

        vbox.Add(gs, 0, wx.EXPAND, 10)

        gs = wx.GridSizer(cols=2)
        gs.Add(submit_button, 1, wx.EXPAND | wx.ALL, 5)
        gs.Add(cancel_button, 1, wx.EXPAND | wx.ALL, 5)

        vbox.Add(gs, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        self.SetSizerAndFit(vbox)
        self.SetSize(kw["size"])
        self.CenterOnParent()
