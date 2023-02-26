import asyncio
import logging
from typing import Any, Dict

import wx

import lib.tasks as tasks

from qvrapi.api import login, ApiError

from ui.utils import TextCtrlStaticBox

_Log = logging.getLogger(__name__)


class LoginDialog(wx.Dialog):
    def __init__(self, email_field: str, *args, **kw):
        super().__init__(*args, **kw)

        self._login_data: Dict[str, Any] | None = None

        self.username_sbox = TextCtrlStaticBox(
            self,
            email_field,
            wx.TE_NO_VSCROLL,
            label="Email",
        )
        self.password_sbox = TextCtrlStaticBox(
            self, "", wx.TE_PASSWORD, label="Password"
        )

        self.submit_button = wx.Button(self, -1, "Submit")
        self.Bind(wx.EVT_BUTTON, self._on_submit_button, self.submit_button)
        cancel_button = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.Bind(wx.EVT_BUTTON, lambda *args: self.EndModal(wx.CANCEL), cancel_button)

        gs = wx.GridSizer(cols=1)

        gs.Add(self.username_sbox.sizer, 1, wx.EXPAND | wx.ALL, 10)
        gs.Add(self.password_sbox.sizer, 1, wx.ALL | wx.EXPAND, 10)

        vbox = wx.BoxSizer(wx.VERTICAL)

        vbox.Add(gs, 0, wx.EXPAND, 10)

        gs = wx.GridSizer(cols=2)
        gs.Add(self.submit_button, 1, wx.EXPAND | wx.ALL, 5)
        gs.Add(cancel_button, 1, wx.EXPAND | wx.ALL, 5)

        vbox.Add(gs, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        self.SetSizerAndFit(vbox)
        self.SetSize(kw["size"])
        self.CenterOnParent()

    def _on_submit_button(self, evt: wx.CommandEvent) -> None:
        """Creates a thread which then creates an eventful that authenticates
        with the backend api to login

        Args:
            evt (wx.CommandEvent):
        """

        async def authenticate() -> None:
            try:
                self._login_data = await login(email=username, password=password)
            except ApiError as err:
                wx.CallAfter(
                    wx.MessageBox,
                    message=err.__str__(),
                    caption="Error",
                    style=wx.MB_OK | wx.ICON_ERROR,
                )

        def running_thread() -> None:
            asyncio.run(authenticate())
            wx.CallAfter(self.submit_button.Enable, enable=True)
            if self._login_data is not None:
                wx.CallAfter(self.EndModal, retCode=wx.OK)

        username = self.username_sbox.get_text()
        password = self.password_sbox.get_text()
        if not username and not password:
            wx.MessageBox(
                "You must fill both fields. Username and Password",
                "Please enter both",
                wx.MB_OK | wx.ICON_ERROR,
            )
            return
        self.submit_button.Enable(False)
        try:
            tasks.login_submit_thread(running_thread)
        except tasks.TaskIsRunning:
            _Log.error(
                "A login request is already being processed. Please wait until this request has finished"
            )
            self.submit_button.Enable(True)

    def get_data(self) -> Dict[str, Any] | None:
        """gets the token if been authenticated

        Returns:
            Dict[str, Any] | None: token string or none if not authenticated
        """
        return self._login_data
