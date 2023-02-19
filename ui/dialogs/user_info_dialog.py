import wx

from lib.schemas import User
from lib.utils import format_timestamp
from lib.api import get_account_type


class UserInfoDialog(wx.Dialog):
    def __init__(self, user: User, *args, **kw):
        super().__init__(*args, **kw)

        email_label = wx.StaticText(self, -1, "Email: ")
        email_value = wx.StaticText(self, -1, user.email)

        date_created_label = wx.StaticText(self, -1, "Date Registered: ")
        date_created_value = wx.StaticText(
            self, -1, format_timestamp(user.date_created, include_hms=True)
        )

        account_type_label = wx.StaticText(self, -1, "Account Type: ")
        account_type_value = wx.StaticText(self, -1, get_account_type(user))

        close_button = wx.Button(self, wx.ID_CLOSE, "Close")
        self.Bind(wx.EVT_BUTTON, lambda *args: self.EndModal(wx.CANCEL), close_button)

        gs = wx.GridSizer(cols=2)

        gs.Add(email_label, 0, wx.ALL | wx.EXPAND, 10)
        gs.Add(email_value, 0, wx.ALL | wx.EXPAND, 10)
        gs.Add(date_created_label, 0, wx.ALL | wx.EXPAND, 10)
        gs.Add(date_created_value, 0, wx.ALL | wx.EXPAND, 10)
        gs.Add(account_type_label, 0, wx.ALL | wx.EXPAND, 10)
        gs.Add(account_type_value, 0, wx.ALL | wx.EXPAND, 10)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(gs, 1, wx.ALL | wx.EXPAND, 10)
        vbox.Add(close_button, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)
        vbox.AddSpacer(10)
        self.SetSizerAndFit(vbox)
        self.SetSize(kw["size"])
        self.CenterOnParent()
