import logging
import asyncio
from typing import List

import wx
import aiohttp

import deluge.utils as deluge_utils
import qvrapi.api as api
import lib.config as config
import lib.utils
import lib.tasks
import ui.utils
import lib.api_handler
from deluge.handler import MagnetData, QueueRequest
from ui.dialogs.extra_game_info_dialog import ExtraGameInfoDialog
from ui.panels.listpanel import ListPanel, ColumnListType
from ui.dialogs.update_magnet_dialog import load_dialog as load_update_magnet_dialog
from qvrapi.schemas import QuestMagnet
from lib.settings import Settings


_Log = logging.getLogger()


COLUMN_NAME = 0
COLUMN_DATE_ADDED = 1
COLUMN_SIZE = 2
COLUMN_PROGRESS = 3
COLUMN_STATUS = 4
COLUMN_SPEED = 5
COLUMN_ETA = 6


class MagnetsListPanel(ListPanel):
    magnet_data_list: List[MagnetData] = []

    def __init__(self, parent: wx.Window):
        from q2gapp import QuestCaveApp

        self.app: QuestCaveApp = wx.GetApp()
        # store the magnet items state
        columns: ColumnListType = [
            {"col": COLUMN_NAME, "heading": "Name", "width": 150},
            {"col": COLUMN_DATE_ADDED, "heading": "Date Added", "width": 70},
            {"col": COLUMN_SIZE, "heading": "Size (MB)", "width": 50},
            {"col": COLUMN_PROGRESS, "heading": "Progress", "width": 40},
            {"col": COLUMN_STATUS, "heading": "Status", "width": 80},
            {"col": COLUMN_SPEED, "heading": "Speed", "width": 50},
            {"col": COLUMN_ETA, "heading": "ETA", "width": 70},
        ]
        super().__init__(parent=parent, title="Games Availible", columns=columns)
        self.app.magnets_listpanel = self
        self.insert_button_panel(self._create_button_panel())

    def _create_button_panel(self) -> wx.Panel:
        # create the button panel
        button_panel = wx.Panel(self, -1)

        # create the buttons and store them into the super classes bitmap_buttons dict
        self.bitmap_buttons["refresh"] = ui.utils.create_bitmap_button(
            "refresh.png", "Refresh Games List", button_panel, size=(24, 24)
        )
        self.Bind(wx.EVT_BUTTON, self.on_refresh_click, self.bitmap_buttons["refresh"])

        hbox_btns = ListPanel.create_bitmap_button_sizer(self.bitmap_buttons)
        button_panel.SetSizer(hbox_btns)
        return button_panel

    def on_refresh_click(self, evt: wx.CommandEvent) -> None:
        _Log.info("Hello from the Magnet ListPanel")

    def on_item_double_click(self, evt: wx.ListEvent) -> None:
        """when the user double clicks on a game in the list then
        check if user is admin before getting extra information on the game and loading the
        game edit dialog

        Args:
            evt (wx.ListEvent): not used

        Returns:
            None: returns None from the super class method
        """
        settings = Settings.load()
        magnet_data = self.get_selected_torrent_item()
        if not settings.is_user_admin() or not magnet_data:
            return super().on_item_double_click(evt)

        try:
            lib.tasks.check_task_and_create(
                self.find_and_launch_magnet_update_dialog,
                settings=settings,
                magnet_data=magnet_data,
            )
        except lib.tasks.TaskIsRunning as err:
            ui.utils.show_error_message(err.__str__())
        return super().on_item_double_click(evt)

    async def find_and_launch_magnet_update_dialog(
        self, settings: Settings, magnet_data: MagnetData
    ) -> None:
        """async function for launching the update magnet frame with the magnet to update

        Args:
            settings (Settings): _description_
            magnet_data (MagnetData): _description_
        """

        if settings.token is None:
            ui.utils.show_error_message("No token was found. Unable to Authenticate")
            return

        # find the magnet in the database by torrent ID

        magnets = await lib.api_handler.get_magnets_from_torrent_id(
            settings.token, magnet_data.torrent_id, ui.utils.show_error_message
        )

        if len(magnets) < 1:
            return

        # open the magnet dialog with the first magnet

        await load_update_magnet_dialog(
            parent=self.app.frame, title="Update Game", magnet=magnets[0]
        )

    def on_col_left_click(self, evt: wx.ListEvent) -> None:
        """sort the magnets by alphabetical order.

        Note: in this current version the sort wont work if install task is running
        this is because the install task holds the row index of the listitem that is being
        installed and updating. If the magnet list changes then the wrong listitem will be updated.
        I am going to change this by putting the new index on the listitems async Queue.
        For the time being just check if task is running if so then do not continue

        Args:
            evt (wx.ListEvent): contains the column index

        Returns:
            None: the return value from the super method
        """
        # check if install is running. I will change this later and send
        # a message to the install queue with the new index to update to
        # lib.tasks.is_task_running(lib.tasks.get_task())
        if lib.tasks.is_task_running(
            lib.tasks.get_task(self.app.start_download_process)
        ):
            _Log.info("ListCtrl sort has been disabled while install is in progress")
            return
        column = evt.GetColumn()
        if type(column) != int:
            return
        items = self._get_list_items()
        if not self.sort_items_from_column(column, items):
            return
        # rebuild the listctrl and magnet data list
        self.clear_list()
        self._rebuild_list(items)
        return super().on_col_left_click(evt)

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

    def sort_items_from_column(self, column: int, items: List[dict]) -> bool:
        """sorts the list items based on column

        Args:
            column (int): the index of the column to sort
            items (dict): the items to sort
        Returns:
            bool: True if items were sorted. False if no column match found
        """
        reverse = self.listctrl.get_toggle_state(column_index=column)
        if column == COLUMN_NAME:
            items.sort(key=lambda x: x["name"], reverse=reverse)
        elif column == COLUMN_DATE_ADDED:
            items.sort(key=lambda x: x["date_added"], reverse=reverse)
        elif column == COLUMN_SIZE:
            items.sort(key=lambda x: x["size"], reverse=reverse)
        else:
            return False
        return True

    def _rebuild_list(self, items: List[dict]) -> None:
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

    async def load_magnets_from_api(self) -> None:
        """
        retrieves the game links from the api. If connection issue then loads locally.
        If successful then stores those links to a local json file
        """
        try:
            magnets: List[QuestMagnet] = await api.get_game_magnets()
            # everything went ok save locallly
            config.save_local_quest_magnets(config.QUEST_MAGNETS_PATH, magnets)
            # enable Online mode
            self.app.set_mode(True)
        except (aiohttp.ClientConnectionError, api.ApiError) as err:
            if isinstance(err, api.ApiError):
                err.message = f"Error with status code: {err.status_code}. Reason: {err.message}.\n If this issue persits then send report"
                self.app.exception_handler(err)
            # Connection issue, try and load from local json file
            magnets = config.load_local_quest_magnets(lib.config.QUEST_MAGNETS_PATH)
            self.app.set_mode(False)
            await self.load_magnets_into_listctrl(magnets)
        except Exception as err:
            # something else went wrong notify the user and return. Skip loading
            self.app.exception_handler(err)
            return
        else:
            # sort the magnets in alphaebetical order and load into listctrl
            magnets = sorted(magnets, key=lambda item: item.display_name.lower())
            self.app.set_mode(True)
            await self.load_magnets_into_listctrl(magnets)
        finally:
            return

    async def load_magnets_into_listctrl(self, magnets: List[QuestMagnet]) -> None:
        self.clear_list()
        for index, magnet in enumerate(magnets):
            magnet_data = MagnetData(
                uri=magnet.decoded_uri,
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
        formatted_date_added = lib.utils.format_timestamp_to_str(magnet.date_added)
        if index == self.listctrl.GetItemCount():
            self.listctrl.InsertItem(index, magnet.display_name)
        else:
            self.listctrl.SetItem(index, COLUMN_NAME, magnet.display_name)
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

        # create the download and install menuitem

        dld_install_item = menu.Append(wx.ID_ANY, "Download and Install")
        self.Bind(wx.EVT_MENU, self.on_dld_and_install_item, dld_install_item)
        menu.AppendSeparator()

        # create the get extra games info menuitem

        extra_info_item = menu.Append(wx.ID_ANY, "Game Info")
        self.Bind(wx.EVT_MENU, self._on_extra_info_item, extra_info_item)
        menu.AppendSeparator()

        # check if there is an apk file already in the download directory

        if lib.utils.apk_exists(magnet_data) is not None:
            # create an install menuitem

            install_only_item = menu.Append(wx.ID_ANY, "Install")
            self.Bind(wx.EVT_MENU, self.on_install_only_item, install_only_item)
            menu.AppendSeparator()

        # download menu item options

        pause_item = menu.Append(wx.ID_ANY, "Pause")
        self.Bind(wx.EVT_MENU, self.on_pause_item_selected, pause_item)
        resume_item = menu.Append(wx.ID_ANY, "Resume")
        self.Bind(wx.EVT_MENU, self.on_resume_item_selected, resume_item)
        menu.AppendSeparator()
        cancel_item = menu.Append(wx.ID_ANY, "Cancel")
        self.Bind(wx.EVT_MENU, self.on_cancel_item_selected, cancel_item)

        menu.AppendSeparator()

        # if debugging enabled then create the debug sub menu
        if self.app.debug_mode:
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

        async def _get_extra_meta_data(uri: str) -> None:
            """retrieve the meta data from the deluge daemon

            Args:
                uri (str): the magnet uri to get meta data from
            """
            try:
                meta_data = await asyncio.wait_for(
                    deluge_utils.get_magnet_info(uri), timeout=5
                )
            except asyncio.TimeoutError:
                ui.utils.show_error_message("Fetching Game information took too long")
            except Exception as err:
                self.app.exception_handler(err)
            else:
                load_info_dialog(meta_data)

        def load_info_dialog(metadata: deluge_utils.MetaData) -> None:
            """displays the meta data about the requested magnet in the magnets listctrl

            Args:
                metadata (deluge_utils.MetaData): the meta data to display in the dialog box
            """
            dlg = ExtraGameInfoDialog(self.app.frame, size=(640, 480))
            dlg.set_name(metadata.name)
            dlg.set_paths(metadata.get_paths())
            dlg.ShowModal()
            dlg.Destroy()

        magnet_data = self.get_selected_torrent_item()
        if not magnet_data:
            return
        try:
            lib.tasks.check_task_and_create(_get_extra_meta_data, uri=magnet_data.uri)
        except lib.tasks.TaskIsRunning:
            pass

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
            lib.tasks.check_task_and_create(
                self.app.start_install_process, path=magnet_data.download_path
            )
        except lib.tasks.TaskIsRunning as err:
            wx.MessageBox(err.__str__(), "Cannot install")

    def on_pause_item_selected(self, evt: wx.MenuEvent) -> None:
        """puts a pause flag on the selected items queue

        Args:
            evt (wx.MenuEvent): _description_
        """
        item = self.get_selected_torrent_item()
        if not item:
            return
        if item.queue is not None:
            item.queue.put_nowait({"request": QueueRequest.PAUSE})

    def on_resume_item_selected(self, evt: wx.MenuEvent):
        """puts a resume flag on the selected items queue

        Args:
            evt (wx.MenuEvent): _description_
        """
        item = self.get_selected_torrent_item()
        if not item:
            return
        if item.queue is not None:
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
        if item.queue is not None:
            item.queue.put_nowait({"request": QueueRequest.CANCEL})

    def get_selected_torrent_item(self) -> MagnetData | None:
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
        # get the app instance and check if there is already
        # an installation task running in the background

        index: int = self.listctrl.GetFirstSelected()
        if index == -1:
            return

        # create a new download path name using the display_name as a prefix

        display_name = self.listctrl.GetItem(index, 0).GetText()
        magnet_data = self.magnet_data_list[index]
        magnet_data.download_path = config.create_path_from_name(
            Settings.load().download_path, display_name
        )
        self.app.create_download_task(magnet_data)

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

    def update_list_item(self, torrent_status: dict) -> None:
        """updates the columns on the magnet that is being installed

        Args:
            torrent_status (dict): contains progress: float, state: str, eta: int, download_payload_rate: float
        """
        index = torrent_status["index"]
        progress = deluge_utils.format_progress(torrent_status.get("progress", 0.0))
        self.listctrl.SetItem(index, 3, f"{progress}%")
        self.listctrl.SetItem(index, 4, torrent_status.get("state", ""))
        formatted_speed = deluge_utils.format_download_speed(
            torrent_status.get("download_payload_rate", 0)
        )
        self.listctrl.SetItem(index, 5, formatted_speed)
        formatted_eta = deluge_utils.format_eta(torrent_status.get("eta", 0))
        self.listctrl.SetItem(index, 6, formatted_eta)

    def search_game(self, text: str) -> None:
        """searches the list for a text match. If index of match returned
        then set the state of the list item in the listctrl

        Args:
            text (str): text to find in the listctrl
        """
        # basic search in the name column. Match with text value
        item_index = self.find_item(COLUMN_NAME, text)
        if item_index == -1:
            return
        # item_index found. Loop through each item and set each Item to zero. This deselects
        for i in range(self.listctrl.GetItemCount()):
            if (
                self.listctrl.GetItemState(i, wx.LIST_STATE_SELECTED)
                == wx.LIST_STATE_SELECTED
            ):
                self.listctrl.SetItemState(i, 0, wx.LIST_STATE_SELECTED)
        # now set the item in the index to a selected state
        self.listctrl.SetItemState(
            item_index, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED
        )
        # scroll the window down to the selected list item
        self.listctrl.EnsureVisible(item_index)

    def find_row_by_torrent_id(self, torrent_id: str) -> int:
        """loops through the magnet_data list and compares for torrent ID

        Args:
            torrent_id (str): id to look for

        Returns:
            int: returns the index of the row. -1 if none found
        """
        for row_index, magnet_data in enumerate(self.magnet_data_list):
            if magnet_data.torrent_id == torrent_id:
                return row_index
        return -1

    def update_row(self, index: int, quest_data: QuestMagnet) -> None:
        """Updates the row if any changes to the database. This is to prevent from reloading the
        entire list and listctrl. Called from The Admin Magnet Update Frame

        Args:
            index (int): row index to update
            quest_data (QuestMagnet): new data to update
        """
        if index > self.listctrl.GetItemCount():
            ui.utils.show_error_message(
                "Index is out of range could not Update Magnet ListCtrl Item Column"
            )
            return
        magnet: MagnetData = self.magnet_data_list[index]
        self.set_items(index, quest_data)
        if magnet.uri != quest_data.decoded_uri:
            self.magnet_data_list[index].uri = quest_data.decoded_uri
        if magnet.name != quest_data.name:
            self.magnet_data_list[index].name = quest_data.name
        if magnet.torrent_id != quest_data.id:
            self.magnet_data_list[index].torrent_id = quest_data.id
