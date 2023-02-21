from typing import List, Tuple

import wx


class CustomListCtrl(wx.ListCtrl):
    _COLUMN_ASCENDING_DEFAULT_TOGGLE_STATE = True

    def __init__(self, parent: wx.Window, columns: List[dict], style: int):
        """
        Args:
            columns (List[dict]): {
                "col":   int (Column Index),
                "heading": str (Label header),
                "format": int, ()
                "width": int (starting width and will fill based on size)
            }
        """
        super().__init__(parent=parent, style=style)

        self._columns = []
        self._cols_toggle_state = []
        self._insert_columns(columns)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.on_col_left_click)

    def _insert_columns(self, columns: List[dict]) -> None:
        for column in columns:
            self.InsertColumn(**column)

    def on_col_left_click(self, evt: wx.ListEvent) -> None:
        """flip the toggle state of the column when the column header has been pressed by the user

        Args:
            evt (wx.ListEvent):
        """
        col_index = evt.GetColumn()
        toggle_state = self.get_toggle_state(col_index)
        toggle_state = not toggle_state
        self.set_toggle_state(col_index, toggle_state)
        evt.Skip()

    def on_size(self, evt: wx.SizeEvent):
        """resize the columns according to the specified width ratio

        Args:
            evt (wx.SizeEvent):
        """
        # Get the width of the listctrl
        width = self.GetSize()[0]

        # Get the total width of all columns
        total_width = sum(column["width"] for column in self._columns)

        # Set the width of each column based on the ratio of width to total width
        for column in self._columns:
            self.SetColumnWidth(
                column["col"], int(width * column["width"] / total_width)
            )
        evt.Skip()

    def DeleteAllColumns(self):
        self._columns.clear()
        return super().DeleteAllColumns()

    def InsertColumn(self, *args, **kw) -> int:
        """keep track of toggle press events by appending new column to the toggle state array

        Args:
            col (int):
            heading (str):
            format (int): default = wx.LIST_FORMAT_LEFT
            width (int): default = wx.LIST_AUTOSIZE

        Returns:
            int: the long integer from the super method
        """
        self._columns.append(kw)
        self._cols_toggle_state.append(self._COLUMN_ASCENDING_DEFAULT_TOGGLE_STATE)
        return super().InsertColumn(*args, **kw)

    def reset_ascending_toggle_states(self) -> None:
        """reset the cols toggle list back to default"""
        for index in range(len(self._cols_toggle_state)):
            self._cols_toggle_state[index] = self._COLUMN_ASCENDING_DEFAULT_TOGGLE_STATE

    def get_toggle_state(self, column_index: int) -> bool:
        """

        Args:
            column_index (int): the column index of the toggle state to get
        Returns:
            bool: returns the toggle state of the column header
        """
        return self._cols_toggle_state[column_index]

    def set_toggle_state(self, column_index: int, state: bool) -> None:
        """sets the toggle state of the column

        Args:
            column_index (int): the index of the column to set the state to
            state (bool):
        """
        self._cols_toggle_state[column_index] = state


class ListCtrlPanel(wx.Panel):
    def __init__(self, parent: wx.Window, title: str, columns: List[dict]):
        super().__init__(parent=parent)
        self.listctrl = CustomListCtrl(parent=self, columns=columns, style=wx.LC_REPORT)

        staticbox = wx.StaticBox(self, label=title)
        sizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
        sizer.Add(self.listctrl, 1, wx.ALL | wx.EXPAND, 0)
        self.SetSizer(sizer)


class LogsListCtrlPanel(ListCtrlPanel):
    pass


class LogsDialog(wx.Dialog):
    def __init__(self, parent: wx.Window, size: Tuple[int, int] = wx.DefaultSize):
        super().__init__(
            parent=parent,
            style=wx.DEFAULT_DIALOG_STYLE | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX,
        )

        columns = [
            {"col": 0, "heading": "Type", "width": 50},
            {"col": 1, "heading": "UUID", "width": 120},
            {"col": 2, "heading": "Traceback", "width": 120},
            {"col": 3, "heading": "Exception", "width": 120},
            {"col": 4, "heading": "Date Added", "width": 50},
        ]
        self.logslstctrl_panel = LogsListCtrlPanel(
            parent=self, columns=columns, title="Errors"
        )
        close_btn = wx.Button(self, wx.ID_CLOSE, "Close")

        self.Bind(wx.EVT_BUTTON, self._on_close_button, close_btn)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.logslstctrl_panel, 1, wx.ALL | wx.EXPAND, 10)
        vbox.Add(close_btn, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)
        vbox.AddSpacer(10)
        self.SetSizerAndFit(vbox)
        self.SetSize(size)
        self.CenterOnParent()

    def _on_close_button(self, evt: wx.CommandEvent) -> None:
        if self.IsModal():
            self.EndModal(wx.ID_CLOSE)
            return
        self.Destroy()
