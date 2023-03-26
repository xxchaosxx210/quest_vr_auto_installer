# from typing import Tuple
from html import escape

import wx
import wx.html
import wxasync

import ui.utils
import api.schemas
import lib.config


ID_SKIP_VERSION = wx.NewIdRef()
ID_REMIND_LATER = wx.NewIdRef()
ID_DOWNLOAD = wx.NewIdRef()


class UpdateDialog(wx.Dialog):
    def __init__(
        self,
        update_details: api.schemas.AppVersionResponse,
        *args,
        **kwargs
        # parent: wx.Window,
        # id: int,
        # title: str,
        # size: Tuple[int, int],
        # style: int = wx.DEFAULT_DIALOG_STYLE,
    ):
        super().__init__(*args, **kwargs)

        self.update_details = update_details
        self._create_controls()
        self._bind_events()
        self._do_layout()
        self._do_properties()

    def _do_properties(self):
        self.SetSize((-1, 600))
        # self.CenterOnParent()

    def _create_controls(self):
        self.logo_bmp = wx.StaticBitmap(self, -1, ui.utils.get_image("logo.png"))
        self.title = wx.StaticText(self, -1, "A new version of QuestCave is availible!")
        # set the title colour to dark blue
        self.title.SetForegroundColour(wx.Colour(0, 0, 128))
        # make the title bold
        font: wx.Font = self.title.GetFont()
        font.SetPointSize(font.GetPointSize() + 2)
        font.SetWeight(wx.BOLD)
        self.title.SetFont(font)

        self.version_header = wx.StaticText(
            self,
            -1,
            f"QuestCave for Windows v{self.update_details.version} is now availible (You have v{lib.config.APP_VERSION}). Would you like to download it now?",
        )
        self.release_title = wx.StaticText(self, -1, "Release Notes:")
        font = self.release_title.GetFont()
        font.SetWeight(wx.BOLD)
        self.release_title.SetFont(font)

        self.html_win = wx.html.HtmlWindow(self, -1, style=wx.html.HW_SCROLLBAR_AUTO)
        self.html_win.SetPage(self.update_details.description)

        btn_min_size = (150, 40)
        self.skip_version_btn = wx.Button(self, ID_SKIP_VERSION, "Skip this version")
        self.skip_version_btn.SetMinSize(btn_min_size)
        self.remind_later_btn = wx.Button(self, ID_REMIND_LATER, "Remind me later")
        self.remind_later_btn.SetMinSize(btn_min_size)
        self.download_btn = wx.Button(self, ID_DOWNLOAD, "Download")
        self.download_btn.SetMinSize(btn_min_size)

    def _bind_events(self):
        wxasync.AsyncBind(wx.EVT_BUTTON, self._on_button_click, self.skip_version_btn)
        wxasync.AsyncBind(wx.EVT_BUTTON, self._on_button_click, self.remind_later_btn)
        wxasync.AsyncBind(wx.EVT_BUTTON, self._on_button_click, self.download_btn)

    def _do_layout(self):
        BORDER = 5
        # create the textctrl and html window vertical box sizer
        text_vbox = wx.BoxSizer(wx.VERTICAL)
        text_vbox.Add(self.title, 0, wx.ALL | wx.EXPAND, BORDER)
        text_vbox.Add(self.version_header, 0, wx.ALL | wx.EXPAND, BORDER)
        text_vbox.Add(self.release_title, 0, wx.ALL | wx.EXPAND, BORDER)
        text_vbox.Add(self.html_win, 1, wx.ALL | wx.EXPAND, BORDER)
        # create the bottom buttons and add to the text vertical box sizer
        btns_hbox = wx.BoxSizer(wx.HORIZONTAL)
        btns_hbox.Add(self.skip_version_btn, 0, wx.ALL, BORDER)
        btns_hbox.AddStretchSpacer(1)
        btns_hbox.Add(self.remind_later_btn, 0, wx.ALL, BORDER)
        btns_hbox.Add(self.download_btn, 0, wx.ALL | wx.EXPAND, BORDER)
        text_vbox.Add(btns_hbox, 0, wx.ALL | wx.EXPAND, BORDER)

        # create the logo box sizer
        logo_vbox = wx.BoxSizer(wx.VERTICAL)
        logo_vbox.Add(self.logo_bmp, 0, wx.ALL | wx.EXPAND, BORDER)

        # logo to the left and update text and html window with buttons to the right
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(logo_vbox, 0, wx.ALL | wx.EXPAND, BORDER)
        hbox.Add(text_vbox, 1, wx.ALL | wx.EXPAND, BORDER)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(hbox, 1, wx.ALL | wx.EXPAND, BORDER)

        self.SetSizerAndFit(vbox)

    async def _on_button_click(self, event: wx.CommandEvent):
        self.SetReturnCode(event.GetId())
        self.Close()
