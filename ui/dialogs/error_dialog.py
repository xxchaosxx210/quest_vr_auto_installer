import wx
import asyncio

from lib.schemas import LogErrorRequest
from lib.api import post_error
from lib.settings import Settings


class ErrorDialog(wx.Dialog):
    def __init__(
        self,
        parent: wx.Frame,
        title: str,
        message: str,
        err: Exception,
        disable_send: bool = False,
    ) -> None:
        super().__init__(parent, title=title, size=(400, 300))

        self._exception = err

        # Error icon
        icon = wx.StaticBitmap(
            self, bitmap=wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_MESSAGE_BOX)
        )

        # Multiline Text Box
        text = wx.TextCtrl(self, value=message, style=wx.TE_MULTILINE | wx.TE_READONLY)

        # Two buttons
        send_error_button = wx.Button(self, label="Send Error")
        self.Bind(wx.EVT_BUTTON, self._on_send_error_button, send_error_button)
        send_error_button.Enable(not disable_send)
        close_button = wx.Button(self, id=wx.ID_CLOSE, label="Close")
        close_button.Bind(wx.EVT_BUTTON, lambda evt: self.EndModal(wx.CLOSE))

        # Sizer for buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(send_error_button, 0, wx.ALL, 5)
        button_sizer.Add(close_button, 0, wx.ALL, 5)

        # Main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(icon, 0, wx.ALL, 5)
        main_sizer.Add(text, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.SetSizer(main_sizer)

        self.CenterOnParent()

    def _on_send_error_button(self, evt: wx.CommandEvent) -> None:
        async def send_error(_error_request: LogErrorRequest) -> None:
            try:
                await post_error(_error_request)
            except Exception as err:
                wx.MessageBox(f"Unable to send. Reason: {str(err)}", "Error!")
            else:
                self.Destroy()

        exc = self._exception
        uuid = Settings.load().uuid
        error_request = LogErrorRequest(
            type=str(exc), uuid=uuid, exception="".join(exc.args), traceback=""
        )
        asyncio.get_event_loop().create_task(send_error(error_request))
