import asyncio
import logging
from typing import Any, Dict, Tuple

import wx

import lib.tasks as tasks
import api.client
from api.exceptions import ApiError
from ui.utils import TextCtrlStaticBox

_Log = logging.getLogger()


class LoginDlg(wx.Dialog):
    def __init__(
        self,
        parent: wx.Window,
        id: int,
        title: str,
        email_field: str,
        size: Tuple[int, int],
        style=wx.DEFAULT_DIALOG_STYLE,
    ):
        super().__init__(parent=parent, id=id, title=title, style=style)

        self._login_data: Dict[str, Any] | None = None
        self._create_controls(email_field)
        self._bind_events()
        self._do_laylout()
        self.SetSize(size)
        self.CenterOnParent()

    def _do_laylout(self) -> None:
        vbox = wx.BoxSizer(wx.VERTICAL)
        gs = wx.GridSizer(cols=1)
        # textctrls
        gs.Add(self.username_sbox.sizer, 1, wx.EXPAND | wx.ALL, 10)
        gs.Add(self.password_sbox.sizer, 1, wx.ALL | wx.EXPAND, 10)
        vbox.Add(gs, 0, wx.EXPAND, 10)
        # bottom buttons
        gs = wx.GridSizer(cols=2)
        gs.Add(self.submit_button, 1, wx.EXPAND | wx.ALL, 5)
        gs.Add(self.cancel_button, 1, wx.EXPAND | wx.ALL, 5)
        vbox.Add(gs, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)
        self.SetSizerAndFit(vbox)

    def _bind_events(self) -> None:
        self.Bind(wx.EVT_BUTTON, self._on_submit_button, self.submit_button)
        self.Bind(
            wx.EVT_BUTTON, lambda *args: self.EndModal(wx.ID_CANCEL), self.cancel_button
        )

    def _create_controls(self, email_field: str) -> None:
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
        self.cancel_button = wx.Button(self, wx.ID_CANCEL, "Cancel")

    def _on_submit_button(self, evt: wx.CommandEvent) -> None:
        """Creates a thread which then creates an eventful that authenticates
        with the backend api to login

        Args:
            evt (wx.CommandEvent):
        """

        async def authenticate() -> None:
            try:
                self._login_data = await api.client.login(
                    email=username, password=password
                )
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
                wx.CallAfter(self.EndModal, retCode=wx.ID_OK)

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
            th = tasks.check_thread_and_start(running_thread)
            th.join()
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
