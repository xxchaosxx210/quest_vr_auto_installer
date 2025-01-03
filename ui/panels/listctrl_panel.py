from typing import Dict, List, Union

import wx


ColumnListType = List[Dict[str, Union[int, str]]]


class CustomListCtrl(wx.ListCtrl):
    _COLUMN_ASCENDING_DEFAULT_TOGGLE_STATE = False

    def __init__(
        self,
        parent: wx.Window,
        id: int,
        columns: ColumnListType,
        toggle_col: bool,
        style: int,
    ):
        """custom listctrl that allows for column resizing and column header toggle events

        Args:
            parent (wx.Window): the parent window
            id (int): the id of the listctrl
            columns (ColumnListType): the column headers to add to the listctrl
            toggle_col (bool): if set to true then the list_col_click event will be bound and
            toggling will be enabled
            style (int): the style of the listctrl
        """
        super().__init__(parent=parent, id=id, style=style)
        self._toggle_col = toggle_col
        self._cols_toggle_state: List[bool] = []
        self._columns = columns
        self._bind_events()

    def _bind_events(self) -> None:
        self.Bind(wx.EVT_SIZE, self._on_size)
        if self._toggle_col:
            self.Bind(wx.EVT_LIST_COL_CLICK, self.on_col_left_click)

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

    def _on_size(self, evt: wx.SizeEvent):
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


class ListCtrlPanel(wx.Panel):
    def __init__(
        self,
        parent: wx.Window,
        title: str | None,
        columns: ColumnListType = [],
        toggle_col: bool = True,
        border: int = 0,
    ):
        """contains a CustomListCtrl and a StaticBoxSizer (Optional)
        CustomListCtrl has alphabetical sorting by default

        Args:
            parent (wx.Window): the parent window
            title (str | None): the title of the label static box. If none, no static box is created
            columns (ColumnListType, optional): the column headers. Defaults to []. {"col": int, "heading": str, "width": int}
            toggle_col (bool): if set to true then the list_col_click event will ...
                    be bound and toggling will be enabled. Defaults to True.
            border (int, optional): the border for the sizer. Defaults to 0.
        """
        super().__init__(parent=parent)

        self.__title = title
        self.__columns = columns
        self.__toggle_col = toggle_col
        # border sizer
        self.__border = border

        self.__do_create_controls()
        self.__do_bind_events()
        self.__do_layout()

    def __do_create_controls(self) -> None:
        self.listctrl = CustomListCtrl(
            parent=self,
            id=-1,
            columns=self.__columns,
            toggle_col=self.__toggle_col,
            style=wx.LC_REPORT,
        )

        self.bitmap_buttons: Dict[str, wx.BitmapButton] = {}
        if self.__title is not None:
            # create a static box with a sizer
            self._staticbox = wx.StaticBox(self, label=self.__title)
            self._staticbox_sizer = wx.StaticBoxSizer(self._staticbox, wx.HORIZONTAL)

        # setup the listctrl headers
        for column in self.__columns:
            self.listctrl.InsertColumn(
                col=column["col"], heading=column["heading"], width=column["width"]
            )

    def __do_bind_events(self) -> None:
        self.listctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_listitem_selected)
        self.listctrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_right_click)
        self.listctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_double_click)

    def __do_layout(self) -> None:
        # main boxsizer to fit controls into
        vbox = wx.BoxSizer(wx.VERTICAL)
        if self.__title is not None:
            # put the listctrl in the static box sizer
            self._staticbox_sizer.Add(
                self.listctrl,
                proportion=1,
                flag=wx.EXPAND | wx.ALL,
                border=self.__border,
            )
            vbox.Add(
                self._staticbox_sizer,
                proportion=1,
                flag=wx.EXPAND | wx.ALL,
                border=self.__border,
            )
        else:
            # put the listctrl in a horizontal box sizer
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            hbox.Add(
                self.listctrl,
                proportion=1,
                flag=wx.EXPAND | wx.ALL,
                border=self.__border,
            )
            vbox.Add(hbox, proportion=1, flag=wx.EXPAND | wx.ALL, border=self.__border)
        self.SetSizer(vbox)

    def disable_list(self) -> bool:
        return self.listctrl.Enable(False)

    def enable_list(self) -> bool:
        return self.listctrl.Enable(True)

    def is_list_enabled(self) -> bool:
        return self.listctrl.IsEnabled()

    def set_label(self, label: str) -> None:
        self._staticbox.SetLabel(label=label)

    def insert_button_panel(
        self,
        button_panel: wx.Panel,
        sizer_index: int = 0,
        proportion: int = 0,
        flag: int = wx.EXPAND,
        border: int = 0,
        spacer: int = 0,
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
        if spacer > 0:
            sizer.AddSpacer(spacer)
        self.Layout()
        return True

    @staticmethod
    def create_bitmap_button_sizer(
        bitmap_buttons: Dict[str, wx.BitmapButton], border: int = 0
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
            hbox_btns.AddSpacer(border)
        return hbox_btns

    # Override methods

    def on_item_double_click(self, evt: wx.ListEvent) -> None:
        evt.Skip()

    def on_right_click(self, evt: wx.ListEvent):
        evt.Skip()

    def on_listitem_selected(self, evt: wx.ListEvent):
        evt.Skip()

    def reset(self) -> None:
        self.listctrl.reset_ascending_toggle_states()

    def find_item(self, column: int, pattern: str) -> int:
        """iterates through each row in the listctrl and compares the
        string contained within the column index given
        Note: (No MatchCasing) finds the first match and returns the index
        of that listitem row

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

    def deselect_each_row(self) -> None:
        """
        loops through each row in the listctrl and checks for LIST_STATE_SELECTED
        if matches then sets the row state to 0
        """
        for i in range(self.listctrl.GetItemCount()):
            if (
                self.listctrl.GetItemState(i, wx.LIST_STATE_SELECTED)
                == wx.LIST_STATE_SELECTED
            ):
                self.listctrl.SetItemState(i, 0, wx.LIST_STATE_SELECTED)

    def select_row(self, index: int, ensure_visible: bool) -> None:
        """sets the row state to wx.LIST_STATE_SELECTED

        Args:
            index (int): the index of the listctrl to select
            ensure_visible (bool): if set to True then the listctrl will scroll to the selected row
        """
        self.listctrl.SetItemState(
            index, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED
        )
        if ensure_visible:
            self.listctrl.EnsureVisible(index)

    def find_text_and_select_column(self, column: int, text: str) -> bool:
        """selects the row that contains the text in the column index given

        Args:
            column (int): the column index to search for
            text (str): the text to search for (Non MatchCasing)

        Returns:
            bool: True if found, False if not found
        """
        index = self.find_item(column, text)
        if index == -1:
            return False
        self.deselect_each_row()
        self.select_row(index, True)
        return True
