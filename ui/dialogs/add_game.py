import asyncio
import logging
from typing import List, Tuple

import aiohttp
import wx
import wx.adv
import wxasync
from pydantic.error_wrappers import ValidationError

import lib.magnet_parser as mparser
import lib.utils
import lib.api_handler
import deluge.utils as du
import api.schemas as schemas
import api.client as client
from ui.utils import show_error_message, async_progress_dialog
from ui.ctrls.textctrl_staticbox import TextCtrlStaticBox
from ui.panels.listctrl_panel import ListCtrlPanel
from ui.panels.magnets_listpanel import MagnetsListPanel
from lib.settings import Settings
from api.exceptions import ApiError


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
    """listctrl containing torrent files within a staticbox"""

    def __init__(self, parent: wx.Window, label: str):
        """
        Args:
            parent (wx.Window): the parent window
            label (str): the staticbox label
        """
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
        self.search_url_sbox = ButtonTextCtrlStaticBox(
            self.panel,
            "",
            wx.TE_NO_VSCROLL | wx.TE_PROCESS_ENTER,
            "Search for Magnet Links from Web Url",
            "Search",
        )

        # Magnet links list
        self.magnet_listpanel = ListCtrlPanel(
            self.panel,
            None,
            [{"col": 0, "heading": "Magnet", "width": 100}],
            toggle_col=False,
        )

        # Add a magnet manually textctrl and button
        self.magnet_url_sbox = ButtonTextCtrlStaticBox(
            self.panel, "", wx.TE_NO_VSCROLL | wx.TE_PROCESS_ENTER, "Add Magnet", "Get"
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
        ctrl_vbox.Add(self.search_url_sbox.sizer, 0, wx.EXPAND, CTRL_VBOX_BORDER)
        ctrl_vbox.Add(self.magnet_url_sbox.sizer, 0, wx.EXPAND, CTRL_VBOX_BORDER)

        hbox_mag_listpanel = wx.BoxSizer(wx.HORIZONTAL)
        hbox_mag_listpanel.Add(self.magnet_listpanel, 1, wx.ALL | wx.EXPAND, 0)

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
            wx.EVT_BUTTON, self._on_search_button_click, self.search_url_sbox.button
        )
        wxasync.AsyncBind(
            wx.EVT_LIST_ITEM_ACTIVATED,
            self._on_magnet_double_click,
            self.magnet_listpanel.listctrl,
        )
        wxasync.AsyncBind(
            wx.EVT_BUTTON,
            self._on_get_torrent_button_click,
            self.magnet_url_sbox.button,
        )
        wxasync.AsyncBind(
            wx.EVT_TEXT_ENTER,
            self._on_magnet_text_return_key_pressed,
            self.magnet_url_sbox.textctrl,
        )
        wxasync.AsyncBind(
            wx.EVT_TEXT_ENTER,
            self._on_search_textctrl_return_key_pressed,
            self.search_url_sbox.textctrl,
        )

    async def get_values_from_ui(self) -> schemas.AddGameRequest:
        """gets and parses the variables from the wxControls and returns a Request Object ready to be sent to the server

        Returns:
            schemas.AddGameRequest: check the api/schemas.py for more information on this class
        """
        b64str = lib.utils.encode_str2b64(self.magnet_url_box.get_text())
        game_request = schemas.AddGameRequest(
            name=self.torrent_name_box.get_text(),
            display_name=self.display_name_box.get_text(),
            magnet=b64str,
            version=float(self.version_box.get_float()),
            id=self.torrent_id_box.get_text(),
            filesize=int(self.filesize_box.get_int()),
            date_added=0.0,
            key="",
        )
        return game_request

    async def _on_get_torrent_button_click(self, evt: wx.CommandEvent) -> None:
        """
        user clicked on the get button in the magnet url control

        Args:
            evt (wx.CommandEvent): event is never used
        """
        url = self.magnet_url_sbox.get_text()
        await self.parse_and_check_url(url)

    async def _on_magnet_text_return_key_pressed(self, evt: wx.CommandEvent) -> None:
        """the magnet_url_sbox.textctrl Enter key pressed

        Args:
            evt (wx.CommandEvent): textctrl
        """
        await self.parse_and_check_url(evt.String)

    async def parse_and_check_url(self, url: str) -> None:
        """Validates the url as a magnet link. Checks if the Magnet matches in the list of games.
        if not then the magnet link gets processed for extra info and added to the listctrl

        Args:
            url (str): the url to validate and add
        """
        # make sure the url is a valid magnet link
        match = mparser.MAG_LINK_PATTERN.match(url)
        if match is None:
            show_error_message("Invalid Magnet. Please a correct Magnet link")
            return
        # make sure the magnet link is not already in the database.
        # use the MagnetListPanel list to check instead of requesting from the server
        if self.does_magnet_already_exist(url):
            notify = wx.adv.NotificationMessage(
                "Already exists",
                "Game already exists in the database",
                self.GetParent(),
                wx.ICON_INFORMATION,
            )
            notify.Show(2)
            return
        await self.process_metadata_from_magnet(magnet_link=url)

    async def _on_magnet_double_click(self, evt: wx.ListEvent) -> None:
        """user double clicked on a magnet link in the magnet list control"""
        index = evt.GetIndex()
        if index < 0:
            return
        magnet_link = self.magnet_listpanel.listctrl.GetItem(index, 0).GetText()
        await self.process_metadata_from_magnet(magnet_link=magnet_link)

    @async_progress_dialog(
        "QuestCave Loading", "Getting Magnet Info, Please wait...10 second timeout", 10
    )
    async def process_metadata_from_magnet(self, magnet_link: str) -> None:
        """process the magnet link and get the metadata. Handle any errors

        this function uses a shielded task to prevent the task from being cancelled.
        so no timeout set. However the timeout is set in the get_magnet_info function

        Args:
            magnet_link (str): the magnet link to get the meta data from
        """
        try:
            # get the magnet info on the torrent file
            magnet_info_task = asyncio.create_task(
                du.get_magnet_info(magnet_link, AddGameDlg.MAGNET_INFO_TIMEOUT)
            )
            meta_data = await asyncio.shield(magnet_info_task)
            self.magnet_url_sbox.set_text(magnet_link)
            self.add_magnet_data_to_ui(magnet_link, meta_data)
        except asyncio.CancelledError:
            _Log.info("Magnet Info Task timed out")
        except Exception as err:
            show_error_message("".join(err.args))

    async def _on_close_button(self, evt: wx.CommandEvent) -> None:
        """this is an async bound dialog so no need to call EndModal or Destroy
        just set the return code and call Close

        Args:
            evt (wx.CommandEvent): not used
        """
        btn_id = evt.GetId()
        self.SetReturnCode(btn_id)
        self.Close()

    @async_progress_dialog(
        "Sending", "Adding Game Data to API server, Please wait...", 1000
    )
    async def add_game_to_database(self, game_request: schemas.AddGameRequest) -> None:
        """adds the game to the database handles any exceptions

        Args:
            game_request (schemas.AddGameRequest): the game request to add to the database
        """
        settings = Settings.load()
        if settings.token is None:
            _Log.error("Token was not found. Exiting _on_save_button")
            return
        task = asyncio.create_task(client.add_game(settings.token, game_request))
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            pass
        except ApiError as err:
            show_error_message(err.__str__())
        except Exception as err:
            show_error_message("".join(err.args))
        else:
            wx.MessageBox("Magnet Saved", "QuestCave", wx.OK | wx.ICON_INFORMATION)

    async def _on_save_button(self, evt: wx.CommandEvent) -> None:
        """save button pressed. Get the values from the controls and validate them before
        sending new game request to the api

        Args:
            evt (wx.CommandEvent): not used
        """
        try:
            game_request = await self.get_values_from_ui()
        except ValidationError as err:
            errors = err.errors()
            show_error_message(errors[-1]["msg"])
            return
        except TypeError as err:
            show_error_message(err.__str__())
            return
        await self.add_game_to_database(game_request)

    async def _on_search_button_click(self, evt: wx.CommandEvent) -> None:
        # get the button that was clicked and disable it initially.
        btn: wx.Button = evt.GetEventObject()
        wx.CallAfter(btn.Enable, enable=False)
        url = self.search_url_sbox.get_text()
        try:
            magnets = await self.search_for_magnet_links(url)
            if magnets:
                await self.check_and_add_magnet_links(magnets)
            wx.CallAfter(btn.Enable, enable=True)
        except Exception as err:
            show_error_message(err.__str__())
            _Log.error(err.__str__())

    async def _on_search_textctrl_return_key_pressed(
        self, evt: wx.CommandEvent
    ) -> None:
        wx.CallAfter(self.search_url_sbox.button.Enable, enable=False)
        url = evt.String
        try:
            magnets = await self.search_for_magnet_links(url)
            if magnets:
                await self.check_and_add_magnet_links(magnets)
        except Exception as err:
            show_error_message(err.__str__())
            _Log.error(err.__str__())
        wx.CallAfter(self.search_url_sbox.button.Enable, enable=True)

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

    def does_magnet_already_exist(self, magnet_link: str) -> bool:
        """iterates through the magnet list in the global MagnetsListPanel and looks
        for a match

        Args:
            magnet_link (str): the magnet link to search for

        Returns:
            bool: Returns True if match found
        """
        for magnet in MagnetsListPanel.magnet_data_list:
            if magnet.uri in magnet_link:
                return True
        return False

    async def check_and_add_magnet_links(self, magnet_urls: List[str]) -> None:
        """iterate through the magnet urls and check if there is a match.
        If not then add the magnet link to the listctrl for editing

        Args:
            magnet_urls List[str]: List of urls
        """
        self.magnet_listpanel.listctrl.DeleteAllItems()
        for index, magnet in enumerate(magnet_urls):
            if not self.does_magnet_already_exist(magnet):
                wx.CallAfter(
                    self.magnet_listpanel.listctrl.InsertItem, index=index, label=magnet
                )
            else:
                notify = wx.adv.NotificationMessage(
                    "Already exists",
                    "Games already exist in the database",
                    self.GetParent(),
                    wx.ICON_INFORMATION,
                )
                wx.CallAfter(notify.Show, timeout=3)

    async def search_for_magnet_links(self, url: str) -> List[str]:
        """gets the html document from the url, parses the HTML and searches for valid magnet links

        Args:
            url (str): the url to scrape

        raises:
            Exception: unhandled exceptions

        Returns:
            List[str]: a list of magnet links
        """
        try:
            html = await mparser.MagnetParser.get_html(url)
            parser = mparser.MagnetParser()
            parser.feed(html)
        except (aiohttp.ClientConnectionError, mparser.ParserConnectionError) as err:
            show_error_message(err.__str__())
            return []
        except aiohttp.InvalidURL:
            show_error_message("Url given was invalid")
            return []
        except Exception as err:
            raise err
        else:
            return parser.magnet_urls
