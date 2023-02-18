from typing import List

import wx


class CustomListCtrl(wx.ListCtrl):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._cols_toggle_state = []

    def InsertColumn(self, *args, **kw):
        """keep track of toggle press events by appending new column to the toggle state array

        Returns:
            method back to super class
        """
        self._cols_toggle_state.append(True)
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
