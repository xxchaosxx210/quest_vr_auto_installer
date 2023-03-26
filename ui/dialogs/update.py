# from typing import Tuple
from html import escape

import wx
import wx.html

import ui.utils
import api.schemas
import lib.config


class UpdateDetailsWindow(wx.html.HtmlWindow):
    def __init__(
        self, parent: wx.Window, update_details: api.schemas.AppVersionResponse
    ):
        super().__init__(parent, wx.ID_ANY)


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

    def _create_controls(self):
        self.logo_bmp = wx.StaticBitmap(self, -1, ui.utils.get_image("logo.png"))
        self.title = wx.StaticText(self, -1, "A new version of QuestCave is availible!")
        # set the title colour to dark blue
        self.title.SetForegroundColour(wx.Colour(0, 0, 128))
        # make the title bold
        font = self.title.GetFont()
        font.SetWeight(wx.BOLD)
        self.title.SetFont(font)

        self.version_header = wx.StaticText(
            self,
            -1,
            f"""
        QuestCave for Windows v{self.update_details.version} is now availible (You have v{lib.config.APP_VERSION}).
        Would you like to download it now?""",
        )

    def _bind_events(self):
        pass

    def _do_layout(self):
        pass
