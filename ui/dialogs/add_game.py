import logging
from typing import List, Tuple

import aiohttp
import wx
import wxasync

import lib.magnet_parser as mparser
from ui.utils import TextCtrlStaticBox, show_error_message
from ui.panels.listctrl_panel import ListCtrlPanel


_Log = logging.getLogger()


class ButtonTextCtrlStaticBox(TextCtrlStaticBox):
    def __init__(
        self,
        parent: wx.Window,
        texctrl_value: str,
        textctrl_style: int,
        label: str,
        btn_label: str,
    ):
        super().__init__(parent, texctrl_value, textctrl_style, label)

        self.button = wx.Button(self, -1, btn_label)

        self.sizer.Add(self.button, 0, wx.EXPAND | wx.ALL, 0)


class AddGameDlg(wx.Dialog):
    def __init__(
        self,
        parent: wx.Frame,
        id: int,
        title: str,
        size: Tuple[int, int],
        style: int = wx.DEFAULT_DIALOG_STYLE,
    ):
        super().__init__(parent=parent, id=id, title=title, style=style)

        self.web_url_ctrl = ButtonTextCtrlStaticBox(
            self, "", wx.TE_NO_VSCROLL, "Search for Magnet Links from Web Url", "Search"
        )
        wxasync.AsyncBind(
            wx.EVT_BUTTON, self._on_weburlctrl_btn_click, self.web_url_ctrl.button
        )

        self.mag_list_pnl = ListCtrlPanel(
            self,
            None,
            [{"col": 0, "heading": "Magnet", "width": 100}],
            toggle_col=False,
        )
        wxasync.AsyncBind(
            wx.EVT_LIST_ITEM_ACTIVATED,
            self._on_double_click_magnet,
            self.mag_list_pnl.listctrl,
        )

        self.mag_url_ctrl = ButtonTextCtrlStaticBox(
            self, "", wx.TE_NO_VSCROLL, "Add Magnet", "Get"
        )

        self.file_paths_lst_pnl = ListCtrlPanel(
            self,
            "Torrent File Paths",
            [{"col": 0, "heading": "Path", "width": 100}],
            toggle_col=False,
        )

        save_btn = wx.Button(self, wx.ID_SAVE, "Save")
        close_btn = wx.Button(self, wx.ID_CLOSE, "Close")

        wxasync.AsyncBind(wx.EVT_BUTTON, self._on_close_or_save_button, save_btn)
        wxasync.AsyncBind(wx.EVT_BUTTON, self._on_close_or_save_button, close_btn)

        hbox_btns = wx.BoxSizer(wx.HORIZONTAL)
        hbox_btns.Add(save_btn, 0, wx.EXPAND, 0)
        hbox_btns.Add(close_btn, 0, wx.EXPAND, 0)

        hbox_mag_listpanel = wx.BoxSizer(wx.HORIZONTAL)
        hbox_mag_listpanel.Add(self.mag_list_pnl, 1, wx.ALL | wx.EXPAND, 0)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.web_url_ctrl.sizer, 0, wx.EXPAND, 0)
        vbox.Add(self.mag_url_ctrl.sizer, 0, wx.EXPAND, 0)
        vbox.Add(hbox_mag_listpanel, 1, wx.EXPAND, 0)
        vbox.AddStretchSpacer(1)
        vbox.Add(hbox_btns, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        vbox.AddSpacer(10)
        self.SetSizerAndFit(vbox)

        self.SetSize(size)
        self.CenterOnParent()

    async def _on_double_click_magnet(self, evt: wx.ListEvent) -> None:
        _Log.info("List Item Double Clicked")

    async def _on_close_or_save_button(self, evt: wx.CommandEvent) -> None:
        btn_id = evt.GetId()
        if self.IsModal():
            self.EndModal(btn_id)
        else:
            self.Destroy()

    async def _on_weburlctrl_btn_click(self, evt: wx.CommandEvent) -> None:
        btn: wx.Button = evt.GetEventObject()
        wx.CallAfter(btn.Enable, enable=False)
        url = self.web_url_ctrl.get_text()
        magnets = await self.get_magnets(url)
        self.mag_list_pnl.listctrl.DeleteAllItems()
        for index, magnet in enumerate(magnets):
            wx.CallAfter(
                self.mag_list_pnl.listctrl.InsertItem, index=index, label=magnet
            )
        wx.CallAfter(btn.Enable, enable=True)

    async def get_magnets(self, url: str) -> List[str]:
        try:
            html = await mparser.MagnetParser.get_html(url)
            parser = mparser.MagnetParser()
            parser.feed(html)
        except (aiohttp.ClientConnectionError, mparser.ParserConnectionError) as err:
            show_error_message(err.__str__())
            return []
        except Exception as err:
            raise err
        else:
            return parser.magnet_urls
