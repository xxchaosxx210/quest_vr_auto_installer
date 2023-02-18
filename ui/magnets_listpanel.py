from typing import List
import logging
import asyncio

import wx
from aiohttp import ClientConnectionError

import deluge.utils as deluge_utils
from deluge.handler import MagnetData, QueueRequest

from ui.listpanel import ListPanel
import lib.api as api
import lib.config as config
import lib.utils
import lib.tasks
from lib.schemas import QuestMagnet
from lib.settings import Settings

from ui.dialogs.extra_game_info_dialog import ExtraGameInfoDialog


_Log = logging.getLogger()


COLUMN_NAME = 0
COLUMN_DATE_ADDED = 1
COLUMN_SIZE = 2
COLUMN_PROGRESS = 3
COLUMN_STATUS = 4
COLUMN_SPEED = 5
COLUMN_ETA = 6


class MagnetsListPanel(ListPanel):
    def __init__(self, *args, **kw):
        # store the magnet items state
        self.magnet_data_list: List[MagnetData] = []
        columns = [
            {"col": COLUMN_NAME, "heading": "Name", "width": 150},
            {"col": COLUMN_DATE_ADDED, "heading": "Date Added", "width": 70},
            {"col": COLUMN_SIZE, "heading": "Size (MB)", "width": 50},
            {"col": COLUMN_PROGRESS, "heading": "Progress", "width": 40},
            {"col": COLUMN_STATUS, "heading": "Status", "width": 80},
            {"col": COLUMN_SPEED, "heading": "Speed", "width": 50},
            {"col": COLUMN_ETA, "heading": "ETA", "width": 70},
        ]
        super().__init__(title="Games Availible", columns=columns, *args, **kw)

        wx.GetApp().magnets_listpanel = self

    def on_col_left_click(self, evt: wx.ListEvent) -> None:
        column = evt.GetColumn()
        items = self._get_list_items()
        if not self.sort_items_from_column(column, items):
            return
        # rebuild the listctrl and magnet data list
        self.clear_list()
        self._rebuild_list(items)

    def _get_list_items(self) -> List[dict]:
        """gets each item row from the listctrl and the magnet data associated with it
        adds them to a dict

        Returns:
            List[dict]: list of items returned
        """
        items = []
        for index in range(self.listctrl.GetItemCount()):
            # get the values from each row in the lisctrl
            name = self.listctrl.GetItem(index, COLUMN_NAME).GetText()
            date = self.listctrl.GetItem(index, COLUMN_DATE_ADDED).GetText()
            size = self.listctrl.GetItem(index, COLUMN_SIZE).GetText()
            progress = self.listctrl.GetItem(index, COLUMN_PROGRESS).GetText()
            status = self.listctrl.GetItem(index, COLUMN_STATUS).GetText()
            speed = self.listctrl.GetItem(index, COLUMN_SPEED).GetText()
            eta = self.listctrl.GetItem(index, COLUMN_ETA).GetText()
            # create a new instance of magnet data but keep the original properties
            magnet_data = MagnetData(**self.magnet_data_list[index].__dict__)
            # temporary store the data into a dict called item
            items.append(
                {
                    "name": name,
                    "date_added": date,
                    "size": size,
                    "progress": progress,
                    "status": status,
                    "speed": speed,
                    "eta": eta,
                    "magnet_data": magnet_data,
                }
            )
        return items

    def sort_items_from_column(self, column: int, items: dict) -> bool:
        """sorts the list items based on column

        Args:
            column (int): the index of the column to sort
            items (dict): the items to sort
        Returns:
            bool: True if items were sorted. False if no column match found
        """
        if column == COLUMN_NAME:
            items.sort(key=lambda x: x["name"])
        elif column == COLUMN_DATE_ADDED:
            items.sort(key=lambda x: x["date_added"], reverse=True)
        elif column == COLUMN_SIZE:
            items.sort(key=lambda x: x["size"])
        else:
            return False
        return True

    def _rebuild_list(self, items: dict) -> None:
        """change the magnet data index to the new index in the rebuilt listctrl
        creates a new row entry in the listctrl

        Args:
            items (dict):
        """
        for index, item in enumerate(items):
            # change the magnet data index to the new item index
            # this is important as when downloading it knows which
            # item in the listctrl to update to
            item["magnet_data"].index = index
            self.magnet_data_list.append(item["magnet_data"])
            self.set_all_items(index, item)

    def clear_list(self) -> None:
        """deletes all items in the listctrl and clears the magnet_data list associated with list items"""
        self.listctrl.DeleteAllItems()
        self.magnet_data_list.clear()

    def set_all_items(self, row_index: int, item: dict) -> None:
        """Inserts and Sets each column from listctrl row from item

        Args:
            row_index (int): the index of the row to add the item data to
            item (dict): item data returned from get_list_items
        """
        self.listctrl.InsertItem(row_index, item["name"])
        self.listctrl.SetItem(row_index, COLUMN_DATE_ADDED, item["date_added"])
        self.listctrl.SetItem(row_index, COLUMN_SIZE, item["size"])
        self.listctrl.SetItem(row_index, COLUMN_PROGRESS, item["progress"])
        self.listctrl.SetItem(row_index, COLUMN_STATUS, item["status"])
        self.listctrl.SetItem(row_index, COLUMN_SPEED, item["speed"])
        self.listctrl.SetItem(row_index, COLUMN_ETA, item["eta"])

    async def load_magnets_from_api(self):
        """makes a request to the Magnet API server and loads the response if successful
        into the listctrl
        """
        app = wx.GetApp()
        try:
            magnets: List[QuestMagnet] = await api.get_game_magnets()
        except ClientConnectionError:
            # try and load the list locally and go into offline mode
            return
        except Exception as err:
            app.exception_handler(err)
            return
        else:
            magnets = sorted(magnets, key=lambda item: item.display_name.lower())
            await self.load_magnets(magnets)

    async def load_magnets(self, magnets: List[QuestMagnet]) -> None:
        self.clear_list()
        for index, magnet in enumerate(magnets):
            magnet_data = MagnetData(
                uri=magnet.uri,
                download_path="",
                index=index,
                queue=asyncio.Queue(),
                timeout=1.0,
                name=magnet.name,
                torrent_id=magnet.id,
            )
            self.magnet_data_list.append(magnet_data)
            # set each item to the listctrl column
            wx.CallAfter(self.set_items, index=index, magnet=magnet)

    def set_items(self, index: int, magnet: QuestMagnet):
        """sets the game data from the magnet object

        Args:
            index (int): the offset of the ListCtrl row
            magnet (QuestMagnet): see QuestMagnet class for properties
        """
        formatted_date_added = lib.utils.format_timestamp(magnet.date_added)
        self.listctrl.InsertItem(index, magnet.display_name)
        self.listctrl.SetItem(index, COLUMN_DATE_ADDED, formatted_date_added)
        self.listctrl.SetItem(index, COLUMN_SIZE, str(magnet.filesize))

    def on_right_click(self, evt: wx.ListEvent) -> None:
        """creates a popup menu when user right clicks on item in listctrl

        Args:
            evt (wx.ListEvent): _description_
        """
        magnet_data = self.get_selected_torrent_item()
        if not magnet_data:
            return

        menu = wx.Menu()

        extra_info_item = menu.Append(wx.ID_ANY, "Game Info")
        self.Bind(wx.EVT_MENU, self._on_extra_info_item, extra_info_item)
        menu.AppendSeparator()

        dld_install_item = menu.Append(wx.ID_ANY, "Download and Install")
        self.Bind(wx.EVT_MENU, self.on_dld_and_install_item, dld_install_item)
        menu.AppendSeparator()
        if lib.utils.apk_exists(magnet_data):
            install_only_item = menu.Append(wx.ID_ANY, "Install")
            self.Bind(wx.EVT_MENU, self.on_install_only_item, install_only_item)
            menu.AppendSeparator()
        pause_item = menu.Append(wx.ID_ANY, "Pause")
        self.Bind(wx.EVT_MENU, self.on_pause_item_selected, pause_item)
        resume_item = menu.Append(wx.ID_ANY, "Resume")
        self.Bind(wx.EVT_MENU, self.on_resume_item_selected, resume_item)
        menu.AppendSeparator()
        cancel_item = menu.Append(wx.ID_ANY, "Cancel")
        self.Bind(wx.EVT_MENU, self.on_cancel_item_selected, cancel_item)

        menu.AppendSeparator()

        debug_menu = wx.Menu()
        install_apk = debug_menu.Append(wx.ID_ANY, "Install APK")
        self.Bind(wx.EVT_MENU, self.on_install_apk, install_apk)
        menu.AppendSubMenu(debug_menu, "Debug")

        self.listctrl.PopupMenu(menu)

    def _on_extra_info_item(self, evt: wx.MenuEvent) -> None:
        """get extra information on the torrent meta data. Show a dialog box with the meta data

        Args:
            evt (wx.MenuEvent): Not used
        """
        app = wx.GetApp()

        async def _get_extra_meta_data(uri: str) -> None:
            """retrieve the meta data from the deluge daemon

            Args:
                uri (str): the magnet uri to get meta data from
            """
            meta_data = await deluge_utils.get_magnet_info(uri)
            if not meta_data:
                app.exception_handler(
                    Exception("Could not get extra information. Read logs for errors")
                )
                return
            load_info_dialog(meta_data)

        def load_info_dialog(metadata: deluge_utils.MetaData) -> None:
            """displays the meta data about the requested magnet in the magnets listctrl

            Args:
                metadata (deluge_utils.MetaData): the meta data to display in the dialog box
            """
            dlg = ExtraGameInfoDialog(app.frame, size=(640, 480))
            dlg.set_name(metadata.name)
            dlg.set_paths(metadata.get_paths())
            dlg.ShowModal()
            dlg.Destroy()

        magnet_data = self.get_selected_torrent_item()
        if not magnet_data:
            return

        # create the coroutine for retrieving the meta data on the selected magnet link in the list
        loop = asyncio.get_event_loop()
        loop.create_task(_get_extra_meta_data(magnet_data.uri))

    def on_install_apk(self, evt: wx.MenuEvent):
        """debug menu item: skips download process and starts the install from local apk
        Note: that the files need to be downloaded first before install can work
        used for testing

        Args:
            evt (wx.MenuEvent):
        """

        magnet_data = self.get_selected_torrent_item()
        if not magnet_data:
            return
        try:
            lib.tasks.create_install_task(
                wx.GetApp().start_install_process, path=magnet_data.download_path
            )
        except lib.tasks.TaskIsRunning as err:
            wx.MessageBox(err.__str__(), "Cannot install")

    def on_pause_item_selected(self, evt: wx.MenuEvent):
        """puts a pause flag on the selected items queue

        Args:
            evt (wx.MenuEvent): _description_
        """
        item = self.get_selected_torrent_item()
        if not item:
            return
        item.queue.put_nowait({"request": QueueRequest.PAUSE})

    def on_resume_item_selected(self, evt: wx.MenuEvent):
        """puts a resume flag on the selected items queue

        Args:
            evt (wx.MenuEvent): _description_
        """
        item = self.get_selected_torrent_item()
        if not item:
            return
        item.queue.put_nowait({"request": QueueRequest.RESUME})

    def on_cancel_item_selected(self, evt: wx.MenuEvent):
        """puts a cancel flag on the running tasks queue

        Args:
            evt (wx.MenuEvent):
        """
        item = self.get_selected_torrent_item()
        if not item:
            return
        dlg = wx.MessageDialog(
            self,
            "Are you sure you want to cancel install?",
            "",
            wx.OK | wx.CANCEL | wx.ICON_STOP,
        )
        dlg.CenterOnParent()
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_CANCEL:
            return
        item.queue.put_nowait({"request": QueueRequest.CANCEL})

    def get_selected_torrent_item(self) -> MagnetData:
        """gets the magnet data connected to the selected item in the listctrl

        Returns:
            MagnetData: read the deluge.handler module for details or None of no item selected
        """
        index: int = self.listctrl.GetFirstSelected()
        if index == -1:
            return None
        item = self.magnet_data_list[index]
        return item

    def on_dld_and_install_item(self, evt: wx.MenuEvent):
        """gets the selected magnet in the list and starts the install process

        Args:
            evt (wx.MenuEvent):
        """
        # get the app instance and check if there is already an installation task running in the background
        app = wx.GetApp()
        index: int = self.listctrl.GetFirstSelected()
        if index == -1:
            return
        # create a new download path name using the display_name as a prefix
        display_name = self.listctrl.GetItem(index, 0).GetText()
        magnet_data = self.magnet_data_list[index]
        # create a pathname for the torrent files to be downloaded to
        magnet_data.download_path = config.create_path_from_name(
            Settings.load().download_path, display_name
        )
        app.create_download_task(magnet_data)

    def on_install_only_item(self, evt: wx.MenuEvent) -> None:
        """starts the install process and skips downloading
        if apk exists in game download directory

        Args:
            evt (wx.MenuEvent): not used
        """
        item = self.get_selected_torrent_item()
        if not item:
            return
        pass

    def update_list_item(self, torrent_status: dict):
        """updates the columns on the magnet that is being installed

        Args:
            torrent_status (dict): contains progress: float, state: str, eta: int, download_payload_rate: float
        """
        index = torrent_status["index"]
        progress = deluge_utils.format_progress(torrent_status.get("progress", 0.0))
        self.listctrl.SetItem(index, 3, f"{progress}%")
        self.listctrl.SetItem(index, 4, torrent_status.get("state"))
        formatted_speed = deluge_utils.format_download_speed(
            torrent_status.get("download_payload_rate", 0)
        )
        self.listctrl.SetItem(index, 5, formatted_speed)
        formatted_eta = deluge_utils.format_eta(torrent_status.get("eta"))
        self.listctrl.SetItem(index, 6, formatted_eta)
