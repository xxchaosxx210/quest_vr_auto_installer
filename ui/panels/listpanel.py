from typing import List

import wx


class CustomListCtrl(wx.ListCtrl):
    _COLUMN_ASCENDING_DEFAULT_TOGGLE_STATE = True

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._cols_toggle_state = []

    def reset_ascending_toggle_states(self) -> None:
        """reset the cols toggle list back to default"""
        for index in range(len(self._cols_toggle_state)):
            self._cols_toggle_state[index] = self._COLUMN_ASCENDING_DEFAULT_TOGGLE_STATE

    def InsertColumn(self, *args, **kw) -> int:
        """keep track of toggle press events by appending new column to the toggle state array

        Returns:
            int: the long integer from the super method
        """
        self._cols_toggle_state.append(self._COLUMN_ASCENDING_DEFAULT_TOGGLE_STATE)
        return super().InsertColumn(*args, **kw)

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


class ListPanel(wx.Panel):
    def __init__(self, title: str, columns=List[dict], *args, **kw):
        super().__init__(*args, **kw)

        self.listctrl = CustomListCtrl(self, -1, style=wx.LC_REPORT)
        self.listctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_listitem_selected)
        self.listctrl.Bind(wx.EVT_SIZE, self.on_size)
        self.listctrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_right_click)
        self.listctrl.Bind(wx.EVT_LIST_COL_CLICK, self.on_col_left_click)
        self.listctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_double_click)

        self.columns = columns

        staticbox = wx.StaticBox(self, label=title)
        sizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)

        for column in columns:
            self.listctrl.InsertColumn(
                col=column["col"], heading=column["heading"], width=column["width"]
            )

        sizer.Add(self.listctrl, proportion=1, flag=wx.EXPAND)
        self.SetSizer(sizer=sizer)

    def on_col_left_click(self, evt: wx.ListEvent) -> None:
        """flip the toggle state of the column when the column header has been pressed by the user

        Args:
            evt (wx.ListEvent):
        """
        col_index = evt.GetColumn()
        toggle_state = self.listctrl.get_toggle_state(col_index)
        toggle_state = not toggle_state
        self.listctrl.set_toggle_state(col_index, toggle_state)

    def on_item_double_click(self, evt: wx.ListEvent) -> None:
        pass

    def on_right_click(self, evt: wx.ListEvent):
        pass

    def on_listitem_selected(self, evt: wx.ListEvent):
        pass

    def on_size(self, evt: wx.SizeEvent):
        # Get the width of the listctrl
        width = self.listctrl.GetSize()[0]

        # Get the total width of all columns
        total_width = sum(column["width"] for column in self.columns)

        # Set the width of each column based on the ratio of width to total width
        for column in self.columns:
            self.listctrl.SetColumnWidth(
                column["col"], int(width * column["width"] / total_width)
            )

    def reset(self) -> None:
        self.listctrl.reset_ascending_toggle_states()

    def find_item(self, column: int, pattern: str) -> int:
        """looks for a pattern in each wx.ListItem

        Args:
            column (int): the column index to search for
            pattern (str): the pattern to match with

        Returns:
            int: returns the first match found, -1 if no match found
        """
        found_index = -1
        for index in range(self.listctrl.GetItemCount()):
            value = self.listctrl.GetItem(index, column).GetText()
            if pattern.lower() in value.lower():
                found_index = index
                break
        return found_index
