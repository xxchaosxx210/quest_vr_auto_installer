from typing import List, Dict, Union

import wx


class ListCtrlPanel(wx.Panel):
    def __init__(self, parent: wx.Window, title: str, columns: List[dict]):
        super().__init__(parent=parent)
        self.listctrl = CustomListCtrl(parent=self, columns=columns, style=wx.LC_REPORT)

        staticbox = wx.StaticBox(self, label=title)
        sizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
        sizer.Add(self.listctrl, 1, wx.ALL | wx.EXPAND, 0)
        self.SetSizer(sizer)


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

        self._columns: List[Dict[str, Union[int, str]]] = []
        self._cols_toggle_state: List[bool] = []
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
        total_width: int = sum(int(column["width"]) for column in self._columns)

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
