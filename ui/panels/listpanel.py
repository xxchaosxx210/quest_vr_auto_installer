from typing import Dict, List, Union

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
    def __init__(
        self, title: str, columns: List[Dict[str, Union[int, str]]] = [], *args, **kw
    ):
        super().__init__(*args, **kw)

        self.listctrl = CustomListCtrl(self, -1, style=wx.LC_REPORT)
        self.listctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_listitem_selected)
        self.listctrl.Bind(wx.EVT_SIZE, self.on_size)
        self.listctrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_right_click)
        self.listctrl.Bind(wx.EVT_LIST_COL_CLICK, self.on_col_left_click)
        self.listctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_double_click)

        self._columns = columns
        self.bitmap_buttons: Dict[str, wx.BitmapButton] = {}

        staticbox = wx.StaticBox(self, label=title)
        sizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)

        for column in columns:
            self.listctrl.InsertColumn(
                col=column["col"], heading=column["heading"], width=column["width"]
            )

        sizer.Add(self.listctrl, proportion=1, flag=wx.EXPAND)
        self.SetSizer(sizer=sizer)

    def insert_button_panel(
        self,
        button_panel: wx.Panel,
        sizer_index: int = 0,
        proportion: int = 0,
        flag: int = wx.EXPAND,
        border: int = 0,
    ) -> bool:
        """Inserts a Panel into the StaticBoxSizer of ListPanel

        Args:
            button_panel (wx.Panel): the panel to insert
            sizer_index (int, optional): the index at which to insert to. Defaults to 0. can be 1 if after listctrl
            proportion (int, optional): see wxSizer. Defaults to 0.
            flag (int, optional): same as proportion wx.Sizer. Defaults to wx.EXPAND.
            border (int, optional): same as border wx.Sizer. Defaults to 0.

        Returns:
            bool: Returns True if added. False if no StaticBoxSizer found from the Super class
        """
        sizer: wx.Sizer = self.GetSizer()
        if sizer is None:
            return False
        sizer.Insert(sizer_index, button_panel, proportion, flag, border)
        self.Layout()
        return True

    @staticmethod
    def create_bitmap_button_sizer(
        bitmap_buttons: Dict[str, wx.BitmapButton]
    ) -> wx.BoxSizer:
        """creates a Horizontal sizer and adds the bitmap_buttons to it and returns to the calling
        function

        Args:
            bitmap_buttons (Dict[str, wx.BitmapButton]): a dict containing key name and value of BitmapButton.
                                                         Normally from self.bitmap_buttons

        Returns:
            wx.BoxSizer: the horizontal sizer that holds the layout of the bitmap buttons
        """
        hbox_btns = wx.BoxSizer(wx.HORIZONTAL)
        for button in bitmap_buttons.values():
            hbox_btns.Add(button, 0, wx.EXPAND, 0)
        return hbox_btns

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
        total_width: int = sum(int(column["width"]) for column in self._columns)

        # Set the width of each column based on the ratio of width to total width
        for column in self._columns:
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
