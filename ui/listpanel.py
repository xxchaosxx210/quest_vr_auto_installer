import wx
from typing import List


class ListPanel(wx.Panel):

    def __init__(self, title: str, columns=List[dict], *args, **kw):
        super().__init__(*args, **kw)

        self.listctrl = wx.ListCtrl(self, -1, style=wx.LC_REPORT)
        self.listctrl.Bind(wx.EVT_LIST_ITEM_SELECTED,
                           self.on_listitem_selected)
        self.listctrl.Bind(wx.EVT_SIZE, self.on_size)
        self.listctrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_right_click)

        self.columns = columns

        staticbox = wx.StaticBox(self, label=title)
        sizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)

        for column in columns:
            self.listctrl.InsertColumn(
                col=column["col"], heading=column["heading"], width=column["width"])

        sizer.Add(self.listctrl, proportion=1, flag=wx.EXPAND)
        self.SetSizer(sizer=sizer)

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
            self.listctrl.SetColumnWidth(column["col"], int(
                width * column["width"] / total_width))
