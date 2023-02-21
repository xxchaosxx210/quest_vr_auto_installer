import asyncio

from typing import Tuple, List
import aiohttp
import wx

from qvrapi.api import get_logs, ApiError
from qvrapi.schemas import ErrorLog
from lib.settings import Settings
from ui.utils import ListCtrlPanel, show_error_message
from ui.dialogs.log_info_dialog import LogInfoDialog
from lib.utils import format_timestamp

KEY_COLUMN = 0
TYPE_COLUMN = 1
UUID_COLUMN = 2
TRACEBACK_COLUMN = 3
EXCEPTION_COLUMN = 4
DATE_ADDED_COLUMN = 5


async def send_request_and_handle_exception(
    async_func: callable, *args, **kwargs
) -> any:
    try:
        result = None
        result = await async_func(*args, **kwargs)
    except ApiError as err:
        show_error_message(err.message, f"Code: {err.status_code}")
    except aiohttp.ClientConnectionError as err:
        show_error_message("".join(err.args))
    finally:
        return result


class LogsListCtrlPanel(ListCtrlPanel):
    def __init__(self, parent: wx.Window, title: str, columns: List[dict]):
        super().__init__(parent, title, columns)

        # store the logs
        self._logs: List[ErrorLog] = []

        self.Bind(
            wx.EVT_LIST_ITEM_ACTIVATED, self._on_list_item_activated, self.listctrl
        )

    def clear_logs(self) -> None:
        self._logs.clear()

    def set_item(self, index: int, log: ErrorLog) -> None:
        self._logs.append(log)
        self.listctrl.InsertItem(index, log.key)
        self.listctrl.SetItem(index, TYPE_COLUMN, str(log.type))
        self.listctrl.SetItem(index, UUID_COLUMN, str(log.uuid))
        self.listctrl.SetItem(index, TRACEBACK_COLUMN, log.traceback)
        self.listctrl.SetItem(index, EXCEPTION_COLUMN, log.exception)
        fmt_dt = format_timestamp(log.date_added)
        self.listctrl.SetItem(index, DATE_ADDED_COLUMN, fmt_dt)

    def _on_list_item_activated(self, evt: wx.ListEvent) -> None:
        index = evt.GetIndex()
        if index == -1:
            return
        dlg = LogInfoDialog(
            parent=self,
            log=self._logs[index],
            size=(640, 640),
            style=wx.DEFAULT_DIALOG_STYLE | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX,
        )
        dlg.ShowModal()
        dlg.Destroy()


class LogsFrame(wx.Frame):
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
        asyncio.get_event_loop().create_task(self.clear_log_request())

    async def clear_log_request(self) -> None:
        settings = Settings.load()
        pass

    async def load_list(self) -> None:
        settings = Settings.load()
        error_logs = await send_request_and_handle_exception(
            get_logs,
            token=settings.token,
            params={"sort_by": "date_added", "order_by": "desc"},
        )
        if not error_logs:
            self.Destroy()
            return
        for index, log in enumerate(error_logs):
            self.logslstctrl_panel.set_item(index, log)
