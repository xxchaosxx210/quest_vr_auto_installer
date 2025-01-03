import wx

import wxasync

import ui.utils


async def load_dialog(*args, **kwargs) -> bool:
    dlg = AboutDlg(*args, **kwargs)
    result = await wxasync.AsyncShowDialogModal(dlg)
    return result


class AboutDlg(wx.Dialog):
    def __init__(
        self,
        parent: wx.Window,
        id: int,
        title: str,
        size: wx.Size,
        app_name: str,
        version: str,
        description: str,
        author: str,
    ):
        super().__init__(parent, id, title, size=size)

        self.panel = wx.Panel(self, -1)

        self.bitmap = ui.utils.get_image("logo.png")
        self.bitmap = wx.StaticBitmap(self.panel, -1, self.bitmap.ConvertToBitmap())

        self.app_name = wx.StaticText(self.panel, -1, app_name)
        self.app_name.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD))

        self.version = wx.StaticText(self.panel, -1, f"Version: {version}")
        self.version.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL))

        self.description = wx.StaticText(
            self.panel,
            -1,
            description,
        )
        self.description.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL))

        self.author = wx.StaticText(self.panel, -1, f"Developed by: {author}")
        self.author.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL))

        self.close_button = wx.Button(self.panel, wx.ID_CLOSE, "Close")
        self.close_button.Bind(wx.EVT_BUTTON, self.on_close_button)

        self.__do_layout()

    def on_close_button(self, event: wx.CommandEvent) -> None:
        """close the dialog when the close button is clicked"""
        self.SetReturnCode(wx.ID_CLOSE)
        self.Close()

    def __do_layout(self):
        """centre the text and buttons in the dialog"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.bitmap, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 10)
        sizer.Add(self.app_name, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 10)
        sizer.Add(self.version, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 10)
        sizer.Add(self.description, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 10)
        sizer.Add(self.author, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 10)
        sizer.Add(self.close_button, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 10)
        self.panel.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
