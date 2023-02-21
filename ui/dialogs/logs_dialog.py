from typing import List

import wx


class CustomListCtrl(wx.ListCtrl):
    _COLUMN_ASCENDING_DEFAULT_TOGGLE_STATE = True

    def __init__(self, columns: List[dict], *args, **kw):
        super().__init__(*args, **kw)
        # columns = [
        #     {"col": 0, "label": "Type", "width": 50},
        #     {"col": 1, "label": "UUID", "width": 120},
        #     {"col": 2, "label": "Traceback", "width": 120},
        #     {"col": 3, "label": "Exception", "width": 120},
        #     {"col": 4, "label": "Date Added", "width": 50},
        # ]

    def InsertColumn(self, *args, **kw) -> int:
        """keep track of toggle press events by appending new column to the toggle state array

        Returns:
            int: the long integer from the super method
        """
        self._cols_toggle_state.append(self._COLUMN_ASCENDING_DEFAULT_TOGGLE_STATE)
        return super().InsertColumn(*args, **kw)


class LogsDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
