from typing import Set

import wx
import wxasync

import ui.utils
import lib.utils
from api.schemas import Game
from ui.panels.listctrl_panel import ListCtrlPanel


async def load_dialog(games: Set[Game], *args, **kwargs) -> None:
    """load the new games update dialog

    Args:
        games (Set[Game]): the list of games that are new
    """
    dialog = NewGamesUpdateDialog(games, *args, **kwargs)
    await wxasync.AsyncShowDialogModal(dialog)


class NewGamesUpdateDialog(wx.Dialog):
    def __init__(self, games: Set[Game], *args, **kw):
        super().__init__(*args, **kw)

        self._games = games
        self._create_controls()
        self._bind_events()
        self._do_layout()
        self._do_properties()

    def _create_controls(self) -> None:
        # Logo Bitmap
        self.logo_stcbmp = wx.StaticBitmap(self, -1, ui.utils.get_image("logo.png"))

        self.title_ctrl = wx.StaticText(self, -1, "New Games Available!")
        self.title_ctrl.SetForegroundColour(wx.Colour(0, 0, 128))
        font = self.title_ctrl.GetFont()
        font.SetPointSize(font.GetPointSize() + 2)
        font.SetWeight(wx.BOLD)
        self.title_ctrl.SetFont(font)

        self.games_lstpnl = ListCtrlPanel(
            self,
            "Games",
            [
                {"col": 0, "heading": "Name", "width": 200},
                {"col": 1, "heading": "Version", "width": 100},
                {"col": 2, "heading": "Date Added", "width": 100},
            ],
        )

        btn_min_size = (150, 40)
        self.close_btn = wx.Button(self, wx.ID_CLOSE, "Close")
        self.close_btn.SetMinSize(btn_min_size)

    def _load_new_games_into_listctrl(self) -> None:
        self.games_lstpnl.listctrl.DeleteAllItems()
        for index, game in enumerate(self._games):
            self.games_lstpnl.listctrl.InsertItem(index, game.display_name)
            self.games_lstpnl.listctrl.SetItem(index, 1, game.version_str)
            self.games_lstpnl.listctrl.SetItem(
                index, 2, lib.utils.format_timestamp_to_str(game.date_added)
            )

    def _bind_events(self) -> None:
        # close event
        wxasync.AsyncBind(wx.EVT_BUTTON, self._on_close, self.close_btn)

    def _do_layout(self) -> None:
        BORDER = 5
        text_vbox = wx.BoxSizer(wx.VERTICAL)
        text_vbox.Add(self.title_ctrl, 0, wx.ALL, BORDER)
        text_vbox.Add(self.games_lstpnl, 1, wx.ALL | wx.EXPAND, BORDER)
        # create the bottom button sizer hbox
        btns_hbox = wx.BoxSizer(wx.HORIZONTAL)
        btns_hbox.AddStretchSpacer(1)
        btns_hbox.Add(self.close_btn, 0, wx.ALL, BORDER)
        text_vbox.Add(btns_hbox, 0, wx.ALL | wx.EXPAND, BORDER)

        # create the logo vertical sizer
        logo_vbox = wx.BoxSizer(wx.VERTICAL)
        logo_vbox.Add(self.logo_stcbmp, 0, wx.ALL | wx.EXPAND, BORDER)

        # logo to the left and the text sizer to the right
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(logo_vbox, 0, wx.ALL | wx.EXPAND, BORDER)
        hbox.Add(text_vbox, 1, wx.ALL | wx.EXPAND, BORDER)

        # create a vbox sizer
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(hbox, 1, wx.ALL | wx.EXPAND, BORDER)

        self.SetSizerAndFit(vbox)

    def _do_properties(self) -> None:
        self._load_new_games_into_listctrl()
        self.CenterOnParent()

    async def _on_close(self, event: wx.CommandEvent) -> None:
        self.SetReturnCode(wx.ID_CLOSE)
        self.Close()
