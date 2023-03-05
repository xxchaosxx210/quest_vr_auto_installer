import asyncio
import logging
from typing import Any, Dict, List, Tuple

import aiohttp
import wx
import wxasync

import lib.magnet_parser as mparser
from ui.utils import TextCtrlStaticBox, show_error_message
from ui.panels.listctrl_panel import ListCtrlPanel
import deluge.utils as du


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


class TorrentFilesStaticBox(wx.StaticBox):
    def __init__(self, parent: wx.Window, label: str):
        super().__init__(parent, -1, label)
        self.treectrl = wx.TreeCtrl(
            self, -1, style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT
        )
        self.sizer = wx.StaticBoxSizer(self, wx.HORIZONTAL)
        self.sizer.Add(self.treectrl, 1, wx.EXPAND | wx.ALL, 0)


class AddGameDlg(wx.Dialog):
    MAGNET_INFO_TIMEOUT: int = 10

    def __init__(
        self,
        parent: wx.Frame,
        id: int,
        title: str,
        size: Tuple[int, int],
        style: int = wx.DEFAULT_DIALOG_STYLE,
    ):
        super().__init__(parent=parent, id=id, title=title, style=style)

        self._do_controls()
        self._do_laylout()
        self._do_events()
        self.SetSize(size)
        self._do_scrolled_properties()
        self.CenterOnParent()

    def _do_scrolled_properties(self):
        """set the scrolled window scrollbars and virtual size"""
        panel_width, panel_height = self.panel.GetSize()
        self.scrolled_win.SetVirtualSize(panel_width, panel_height)
        self.scrolled_win.SetScrollbars(
            10, 10, int(panel_width / 10), int(panel_height / 10)
        )
        self.scrolled_win.SetScrollRate(10, 10)

    def _do_controls(self) -> None:
        # dialog->scrolled window->panel->controls
        self.scrolled_win = wx.ScrolledWindow(self, -1)
        self.panel = wx.Panel(self.scrolled_win, -1)
        # Random URL magnet link search textbox
        self.web_url_ctrl = ButtonTextCtrlStaticBox(
            self.panel,
            "",
            wx.TE_NO_VSCROLL,
            "Search for Magnet Links from Web Url",
            "Search",
        )

        # Magnet links list
        self.mag_list_pnl = ListCtrlPanel(
            self.panel,
            None,
            [{"col": 0, "heading": "Magnet", "width": 100}],
            toggle_col=False,
        )

        # Add a magnet manually textctrl and button
        self.mag_url_ctrl = ButtonTextCtrlStaticBox(
            self.panel, "", wx.TE_NO_VSCROLL, "Add Magnet", "Get"
        )

        # Torrent files found from magnet link lookup
        self.torrent_files_box = TorrentFilesStaticBox(self.panel, "Torrent Files")
        self.torrent_name_box = TextCtrlStaticBox(
            self.panel, "", wx.TE_NO_VSCROLL, "Torrent Name"
        )
        self.display_name_box = TextCtrlStaticBox(
            self.panel, "", wx.TE_NO_VSCROLL, "Display Name"
        )
        self.magnet_url_box = TextCtrlStaticBox(
            self.panel, "", wx.TE_NO_VSCROLL, "Magnet Link"
        )
        self.version_box = TextCtrlStaticBox(
            self.panel, "1.0", wx.TE_NO_VSCROLL, "Version"
        )
        self.filesize_box = TextCtrlStaticBox(
            self.panel, "", wx.TE_NO_VSCROLL | wx.TE_READONLY, "File Size"
        )
        self.torrent_id_box = TextCtrlStaticBox(
            self.panel, "", wx.TE_NO_VSCROLL | wx.TE_READONLY, "Torrent ID"
        )
        self.save_btn = wx.Button(self, wx.ID_SAVE, "Save")
        self.close_btn = wx.Button(self, wx.ID_CLOSE, "Close")

    def _do_laylout(self) -> None:
        ctrl_vbox = wx.BoxSizer(wx.VERTICAL)
        CTRL_VBOX_BORDER = 10
        ctrl_vbox.Add(self.web_url_ctrl.sizer, 0, wx.EXPAND, CTRL_VBOX_BORDER)
        ctrl_vbox.Add(self.mag_url_ctrl.sizer, 0, wx.EXPAND, CTRL_VBOX_BORDER)

        hbox_mag_listpanel = wx.BoxSizer(wx.HORIZONTAL)
        hbox_mag_listpanel.Add(self.mag_list_pnl, 1, wx.ALL | wx.EXPAND, 0)

        ctrl_vbox.Add(hbox_mag_listpanel, 1, wx.EXPAND, CTRL_VBOX_BORDER)
        ctrl_vbox.Add(self.torrent_files_box.sizer, 1, wx.EXPAND | wx.ALL, 0)
        ctrl_vbox.Add(self.torrent_name_box.sizer, 0, wx.EXPAND, CTRL_VBOX_BORDER)
        ctrl_vbox.Add(self.display_name_box.sizer, 0, wx.EXPAND, CTRL_VBOX_BORDER)
        ctrl_vbox.Add(self.magnet_url_box.sizer, 0, wx.EXPAND, CTRL_VBOX_BORDER)
        ctrl_vbox.Add(self.version_box.sizer, 0, wx.EXPAND, CTRL_VBOX_BORDER)
        ctrl_vbox.Add(self.filesize_box.sizer, 0, wx.EXPAND, CTRL_VBOX_BORDER)
        ctrl_vbox.Add(self.torrent_id_box.sizer, 0, wx.EXPAND, CTRL_VBOX_BORDER)

        panel_gs = wx.GridSizer(cols=1)
        panel_gs.Add(ctrl_vbox, 1, wx.ALL | wx.EXPAND, 20)
        self.panel.SetSizer(panel_gs)

        # # add the panel to the scrolled window sizer
        scrolled_win_gs = wx.GridSizer(cols=1)
        scrolled_win_gs.Add(self.panel, 1, wx.ALL | wx.EXPAND, 0)
        self.scrolled_win.SetSizer(scrolled_win_gs)

        hbox_btns = wx.BoxSizer(wx.HORIZONTAL)
        hbox_btns.Add(self.save_btn, 0, wx.EXPAND, 0)
        hbox_btns.Add(self.close_btn, 0, wx.EXPAND, 0)

        # add the scrolled window and hbox button to the dialog sizer
        dialog_vbox = wx.BoxSizer(wx.VERTICAL)
        dialog_vbox.Add(self.scrolled_win, 1, wx.ALL | wx.EXPAND, 0)
        dialog_vbox.AddSpacer(10)
        dialog_vbox.Add(hbox_btns, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        dialog_vbox.AddSpacer(10)
        self.SetSizerAndFit(dialog_vbox)

    def _do_events(self) -> None:
        wxasync.AsyncBind(wx.EVT_BUTTON, self._on_save_button, self.save_btn)
        wxasync.AsyncBind(wx.EVT_BUTTON, self._on_close_button, self.close_btn)
        wxasync.AsyncBind(
            wx.EVT_BUTTON, self._on_weburlctrl_btn_click, self.web_url_ctrl.button
        )
        wxasync.AsyncBind(
            wx.EVT_LIST_ITEM_ACTIVATED,
            self._on_double_click_magnet,
            self.mag_list_pnl.listctrl,
        )
        wxasync.AsyncBind(
            wx.EVT_BUTTON, self._on_magnet_get_click, self.mag_url_ctrl.button
        )

    async def _on_magnet_get_click(self, evt: wx.CommandEvent) -> None:
        """
        user clicked on the get button in the magnet url control

        Args:
            evt (wx.CommandEvent): event is never used
        """
        url = self.mag_url_ctrl.get_text()
        # make sure the url is a valid magnet link
        match = mparser.MAG_LINK_PATTERN.match(url)
        if match is None:
            show_error_message("Invalid Magnet. Please a correct Magnet link")
            return
        await self.process_metadata_from_magnet(magnet_link=url)

    async def _on_double_click_magnet(self, evt: wx.ListEvent) -> None:
        """user double clicked on a magnet link in the magnet list control"""
        index = evt.GetIndex()
        if index < 0:
            return
        magnet_link = self.mag_list_pnl.listctrl.GetItem(index, 0).GetText()
        await self.process_metadata_from_magnet(magnet_link=magnet_link)

    async def process_metadata_from_magnet(self, magnet_link: str) -> None:
        """process the magnet link and get the metadata. Handle any errors

        this function uses a shielded task to prevent the task from being cancelled.
        so no timeout set. However the timeout is set in the get_magnet_info function

        Args:
            magnet_link (str): the magnet link to get the meta data from
        """
        progress = wx.ProgressDialog(
            "QuestCave Loading",
            f"Getting Magnet Info, Please wait...{AddGameDlg.MAGNET_INFO_TIMEOUT} second timeout",
            100,
            self,
            wx.PD_APP_MODAL | wx.PD_AUTO_HIDE,
        )
        progress.Pulse()
        task = asyncio.create_task(
            du.get_magnet_info(magnet_link, AddGameDlg.MAGNET_INFO_TIMEOUT)
        )
        # wait for the task to complete
        # handle any errors
        try:
            meta_data = await asyncio.shield(task)
        except asyncio.CancelledError:
            pass
        except Exception as err:
            show_error_message("".join(err.args))
        else:
            self.mag_url_ctrl.set_text(magnet_link)
            self.add_magnet_data_to_ui(magnet_link, meta_data)
        finally:
            progress.Destroy()

    async def _on_close_button(self, evt: wx.CommandEvent) -> None:
        btn_id = evt.GetId()
        if self.IsModal():
            self.EndModal(btn_id)
        else:
            self.Destroy()

    async def _on_save_button(self, evt: wx.CommandEvent) -> None:
        """user clicked on the save button"""
        props = await self.get_values_from_ui()

    async def get_values_from_ui(self) -> Dict[str, Any]:
        """get the values from the UI controls and return them as a dict"""
        props: Dict[str, Any] = {}
        return props

    async def _on_weburlctrl_btn_click(self, evt: wx.CommandEvent) -> None:
        """
        Search for magnet links from a web url
        This is just a simple 1 page web scrape
        """
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
        """simple web request and parse the HTML looking for magnet links

        Args:
            url (str): the url to search for magnet links

        Raises:
            Exception: any exception that is not handled

        Returns:
            List[str]: list of magnet links
        """
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

    def add_magnet_data_to_ui(self, magnet_uri: str, meta: du.MetaData) -> None:
        """add the magnet data to the UI controls

        Args:
            magnet_uri (str): the magnet uri
            meta (du.MetaData): the magnet metadata
        """
        self.torrent_name_box.set_text(meta.name)
        self.display_name_box.set_text("")
        self.magnet_url_box.set_text(magnet_uri)
        self.version_box.set_text("1.0")
        self.filesize_box.set_text(str(meta.piece_length))
        self.torrent_id_box.set_text(meta.torrent_id)
        self.torrent_files_box.treectrl.DeleteAllItems()
        if meta.files is None:
            return
        # insert the files into the TreeCtrl
        root_item_id = self.torrent_files_box.treectrl.AddRoot(meta.name)
        for index, root_item in enumerate(meta.files):
            path_item = root_item.path[0]
            sub_tree_item_id = self.torrent_files_box.treectrl.AppendItem(
                root_item_id, path_item
            )
            root_item.path.pop(root_item.path.index(path_item))
            for sub_index, sub_item in enumerate(root_item.path):
                self.torrent_files_box.treectrl.AppendItem(sub_tree_item_id, sub_item)
