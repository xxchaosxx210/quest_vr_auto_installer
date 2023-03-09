import asyncio

from typing import Tuple, List
import aiohttp
import wx

import api.client
from api.exceptions import ApiError
from api.schemas import ErrorLog
from lib.settings import Settings
from ui.utils import show_error_message
from ui.dialogs.log_info import LogInfoDlg
from ui.panels.listctrl_panel import ListCtrlPanel
from lib.utils import format_timestamp_to_str

KEY_COLUMN = 0
TYPE_COLUMN = 1
UUID_COLUMN = 2
TRACEBACK_COLUMN = 3
EXCEPTION_COLUMN = 4
DATE_ADDED_COLUMN = 5


class LogsListCtrlPanel(ListCtrlPanel):
    """main panel for the LogsFrame

    Args:
        ListCtrlPanel (_type_): inherits from this class
    """

    def __init__(self, parent: wx.Window, title: str, columns: List[dict]):
        super().__init__(parent, title, columns)

        # store the logs
        self._logs: List[ErrorLog] = []
        self._bind_events()

    def _bind_events(self) -> None:
        self.Bind(
            wx.EVT_LIST_ITEM_ACTIVATED, self._on_list_item_activated, self.listctrl
        )
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_right_click, self.listctrl)

    def clear_logs(self) -> None:
        """clear the internal logs list and lisctrl items"""
        self._logs.clear()
        self.listctrl.DeleteAllItems()

    def set_item(self, index: int, log: ErrorLog) -> None:
        """set the column entry with the ErrorLog instance

        Args:
            index (int): index row to add columns to
            log (ErrorLog): Log object
        """
        self._logs.append(log)
        self.listctrl.InsertItem(index, log.key)
        self.listctrl.SetItem(index, TYPE_COLUMN, str(log.type))
        self.listctrl.SetItem(index, UUID_COLUMN, str(log.uuid))
        self.listctrl.SetItem(index, TRACEBACK_COLUMN, log.traceback)
        self.listctrl.SetItem(index, EXCEPTION_COLUMN, log.exception)
        fmt_dt = format_timestamp_to_str(log.date_added)
        self.listctrl.SetItem(index, DATE_ADDED_COLUMN, fmt_dt)

    def _on_list_item_activated(self, evt: wx.ListEvent) -> None:
        """when the user double clicks then open up the extra Log information Dialog

        Args:
            evt (wx.ListEvent): ignored
        """
        index = evt.GetIndex()
        if index == -1:
            return
        with LogInfoDlg(
            parent=self,
            log=self._logs[index],
            size=(640, 640),
            style=wx.DEFAULT_DIALOG_STYLE | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX,
        ) as dlg:
            dlg.ShowModal()

    def on_right_click(self, evt: wx.ListEvent) -> None:
        """load the popupmenu for extra options for selected log

        Args:
            evt (wx.ListEvent): gets the index from the selected item
        """
        index = evt.GetIndex()
        if index == -1:
            return
        self.listctrl.PopupMenu(self._create_popup_menu())

    def _create_popup_menu(self) -> wx.Menu:
        popup_menu = wx.Menu()
        delete_m_item = popup_menu.Append(wx.ID_ANY, "Delete")
        self.Bind(wx.EVT_MENU, self._on_delete_log, delete_m_item)
        return popup_menu

    def _on_delete_log(self, evt: wx.MenuEvent) -> None:
        """when the user selects the delete log menuitem get the key from the selected row
        and delete the log from the database

        Args:
            evt (wx.MenuEvent): _description_
        """
        index = self.listctrl.GetFirstSelected()
        if index == -1:
            return
        settings = Settings.load()

        async def delete_log(token: str, key: str) -> None:
            try:
                await api.client.delete_logs(token=token, key=key)
            except (aiohttp.ClientConnectionError, ApiError) as err:
                show_error_message(err.__str__())
            else:
                wx.CallAfter(self.delete_item, index=index)

        if settings.token is not None:
            asyncio.get_event_loop().create_task(
                delete_log(settings.token, self._logs[index].key)
            )

    def delete_item(self, index: int) -> bool:
        self._logs.pop(index)
        return self.listctrl.DeleteItem(item=index)

    def populate_listctrl(self, logs: List[ErrorLog]) -> None:
        self.clear_logs()
        for index, log in enumerate(logs):
            self.set_item(index=index, log=log)


class LogsFrame(wx.Frame):

    """LogsFrame: has a listctrl that contains all the Log entries found on the database"""

    def __init__(self, parent: wx.Window, size: Tuple[int, int] = wx.DefaultSize):
        super().__init__(parent=parent, id=-1, title="")

        self.SetBackgroundColour(wx.WHITE)

        self.SetMenuBar(self._create_menubar())

        columns = [
            {"col": TYPE_COLUMN, "heading": "Key", "width": 50},
            {"col": TYPE_COLUMN, "heading": "Type", "width": 50},
            {"col": UUID_COLUMN, "heading": "UUID", "width": 120},
            {"col": TRACEBACK_COLUMN, "heading": "Traceback", "width": 120},
            {"col": EXCEPTION_COLUMN, "heading": "Exception", "width": 120},
            {"col": DATE_ADDED_COLUMN, "heading": "Date Added", "width": 50},
        ]
        self.logslstctrl_panel = LogsListCtrlPanel(
            parent=self, columns=columns, title="Errors"
        )
        close_btn = wx.Button(self, wx.ID_CLOSE, "Close")

        self.Bind(wx.EVT_BUTTON, lambda *args: self.Destroy(), close_btn)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.logslstctrl_panel, 1, wx.ALL | wx.EXPAND, 20)
        vbox.Add(close_btn, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)
        vbox.AddSpacer(10)
        self.SetSizerAndFit(vbox)
        self.SetSize(parent.GetSize())
        self.CenterOnParent()

        asyncio.get_event_loop().create_task(self.load_list())

    def _create_menubar(self) -> wx.MenuBar:
        menubar = wx.MenuBar()
        menubar.Append(self._create_file_menu(), "File")
        return menubar

    def _create_file_menu(self) -> wx.Menu:
        menu = wx.Menu()
        clear_logs_m_item = menu.Append(wx.ID_ANY, "Clear Logs")
        self.Bind(wx.EVT_MENU, self._on_clear_logs, clear_logs_m_item)
        return menu

    def _on_clear_logs(self, evt: wx.MenuEvent) -> None:
        """clear logs menu item selected start a new task to clear and delete the logs on the database

        Args:
            evt (wx.MenuEvent): _description_
        """
        asyncio.get_event_loop().create_task(self.clear_logs_request())

    async def clear_logs_request(self) -> None:
        """deletes all the log entries in the database"""
        settings = Settings.load()
        if settings.token is None:
            return
        try:
            logs = await api.client.delete_logs(settings.token, "all")
        except (ApiError, aiohttp.ClientConnectionError) as err:
            show_error_message(err.__str__())
        else:
            self.logslstctrl_panel.populate_listctrl(logs=logs)
        finally:
            return

    async def load_list(self) -> None:
        """gets the logs from the server and loads into listctrl

        Raises:
            err: unhandled exception
        """
        settings = Settings.load()
        if settings.token is None:
            return
        try:
            error_logs = await api.client.get_logs(
                settings.token, params={"sort_by": "date_added", "order_by": "desc"}
            )
        except aiohttp.ClientConnectionError as err:
            show_error_message(err.__str__())
        except ApiError as err:
            if err.status_code == 401:
                # invalid credentials remove any token and save the settings
                settings.remove_auth()
            show_error_message(err.__str__())
        except Exception as err:
            raise err
        else:
            if not error_logs:
                return
            for index, log in enumerate(error_logs):
                self.logslstctrl_panel.set_item(index, log)
