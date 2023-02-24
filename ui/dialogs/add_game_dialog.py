import logging
from typing import List, Tuple

import aiohttp
import wx
import wxasync


from ui.utils import TextCtrlStaticBox, show_error_message
import lib.magnet_parser as mparser


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


class AddGameDialog(wx.Dialog):
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
            self, "", wx.TE_NO_VSCROLL, "Web URL", "Grab"
        )
        wxasync.AsyncBind(
            wx.EVT_BUTTON, self._on_weburlctrl_btn_click, self.web_url_ctrl.button
        )

        save_btn = wx.Button(self, wx.ID_SAVE, "Save")
        close_btn = wx.Button(self, wx.ID_CLOSE, "Close")

        wxasync.AsyncBind(wx.EVT_BUTTON, self._on_close_or_save_button, save_btn)
        wxasync.AsyncBind(wx.EVT_BUTTON, self._on_close_or_save_button, close_btn)

        hbox_btns = wx.BoxSizer(wx.HORIZONTAL)
        hbox_btns.Add(save_btn, 0, wx.EXPAND, 0)
        hbox_btns.Add(close_btn, 0, wx.EXPAND, 0)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.web_url_ctrl.sizer, 0, wx.EXPAND, 0)
        vbox.Add(hbox_btns, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        vbox.AddSpacer(10)
        self.SetSizerAndFit(vbox)

        self.SetSize(size)
        self.CenterOnParent()

    async def _on_close_or_save_button(self, evt: wx.CommandEvent) -> None:
        btn_id = evt.GetId()
        if self.IsModal():
            self.EndModal(btn_id)
        else:
            self.Destroy()

    async def _on_weburlctrl_btn_click(self, evt: wx.CommandEvent) -> None:
        url = self.web_url_ctrl.get_text()
        magnets = await self.get_magnets(url)
        _Log.info(magnets.__str__())

    async def get_magnets(self, url: str) -> List[str]:
        try:
            html = await mparser.MagnetParser.get_html(url)
            parser = mparser.MagnetParser()
            parser.feed(html)
            return parser.magnet_urls
        except mparser.ParserConnectionError as err:
            show_error_message(err.message)
        except aiohttp.ClientConnectionError as err:
            show_error_message(err.__str__())
        except Exception as err:
            raise err
