from typing import List
import logging
import asyncio

import wx

import deluge.utils as deluge_utils
from deluge.handler import MagnetData, QueueRequest

from ui.listpanel import ListPanel
import api
import config
import quest_installer
from schemas import QuestMagnet


_Log = logging.getLogger()


class MagnetsListPanel(ListPanel):
    def __init__(self, *args, **kw):
        # store the magnet items state
        self.magnet_data_list: List[MagnetData] = []
        columns = [
            {"col": 0, "heading": "Name", "width": 120},
            {"col": 1, "heading": "Version", "width": 40},
            {"col": 2, "heading": "Size (MB)", "width": 50},
            {"col": 3, "heading": "Progress", "width": 40},
            {"col": 4, "heading": "Status", "width": 150},
            {"col": 5, "heading": "Speed", "width": 50},
            {"col": 6, "heading": "ETA", "width": 60},
        ]
        super().__init__(title="Games Availible", columns=columns, *args, **kw)

        wx.GetApp().magnets_listpanel = self

    async def load(self):
        """makes a request to the Magnet API server and loads the response if successful
        into the listctrl
        """
        magnets: List[QuestMagnet] = await api.get_game_magnets()
        self.listctrl.DeleteAllItems()
        self.magnet_data_list.clear()
        for index, magnet in enumerate(magnets):
            savepath = config.create_path_from_name(magnet.name)
            magnet_data = MagnetData(
                uri=magnet.uri,
                download_path=savepath,
                index=index,
                queue=asyncio.Queue(),
                timeout=1.0,
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
        self.listctrl.InsertItem(index, magnet.name)
        self.listctrl.SetItem(index, 1, str(magnet.version))
        self.listctrl.SetItem(index, 2, str(magnet.filesize))

    def on_right_click(self, evt: wx.ListEvent):
        """creates a popup menu when user right clicks on item in listctrl

        Args:
            evt (wx.ListEvent): _description_
        """
        menu = wx.Menu()
        install_item = menu.Append(wx.ID_ANY, "Download and Install")
        self.Bind(wx.EVT_MENU, self.on_download_item_selected, install_item)
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
        find_apk_item = debug_menu.Append(wx.ID_ANY, "Find APK Path")
        self.Bind(wx.EVT_MENU, self.on_find_apk_item, find_apk_item)
        install_apk = debug_menu.Append(wx.ID_ANY, "Install APK")
        self.Bind(wx.EVT_MENU, self.on_install_apk, install_apk)
        menu.AppendSubMenu(debug_menu, "Debug")

        self.listctrl.PopupMenu(menu)

    def on_install_apk(self, evt: wx.MenuEvent):
        """debug menu item: skips download process and starts the install from local apk
        Note: that the files need to be downloaded first before install can work
        used for testing

        Args:
            evt (wx.MenuEvent):
        """

        async def mimick_install(path: str):
            app = wx.GetApp()
            await app.start_install_process(path)

        magnet_data = self.get_selected_torrent_item()
        if not magnet_data:
            return
        asyncio.get_event_loop().create_task(mimick_install(magnet_data.download_path))

    def on_find_apk_item(self, evt: wx.MenuEvent):
        """debug item: finds the apk package and its data folder on local disk

        Args:
            evt (wx.MenuEvent): _description_
        """

        async def find_apk(magnet_data: MagnetData) -> None:
            root_dir = magnet_data.download_path
            apk_path, apk_dirs, apk_file = await magnet_data.find_apk_directory_async(
                root_dir
            )
            _Log.info(f"APK Path: {apk_path}, APK Filename: {apk_file}")

        loop = asyncio.get_event_loop()
        selected_item = self.get_selected_torrent_item()
        loop.create_task(find_apk(selected_item))

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
            MagnetData: read the deluge.handler module for details
        """
        index: int = self.listctrl.GetFirstSelected()
        if index == -1:
            return None
        item = self.magnet_data_list[index]
        return item

    def on_download_item_selected(self, evt: wx.MenuEvent):
        """gets the selected magnet in the list and starts the install process

        Args:
            evt (wx.MenuEvent):
        """
        index: int = self.listctrl.GetFirstSelected()
        if index == -1:
            return
        magnet_data = self.magnet_data_list[index]
        # CHECK IF TASK IS RUNNING HERE
        app = wx.GetApp()
        loop = asyncio.get_event_loop()
        loop.create_task(
            app.start_install_process(
                callback=app.on_torrent_update,
                error_callback=app.exception_handler,
                magnet_data=magnet_data,
            )
        )

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
