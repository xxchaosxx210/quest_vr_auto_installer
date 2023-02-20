import wx


def enable_menu_items(menu: wx.Menu, enable: bool = True) -> int:
    """enables or disables all of the menuitems within a menu

    Args:
        menu (wx.Menu): the menu object to iterate through
        enable (bool, optional): enable or disable the menuitems. Defaults to True.

    Returns:
        int: the amount of menuitems state changed
    """
    for index, menuitem in enumerate(menu.GetMenuItems()):
        menuitem.Enable(enable=enable)
    return index


class TextCtrlStaticBox(wx.StaticBox):
    def __init__(
        self, parent: wx.Window, texctrl_value: str, textctrl_style: int, label: str
    ):
        super().__init__(parent=parent, label=label)

        self.textctrl = wx.TextCtrl(
            self, id=-1, value=texctrl_value, style=textctrl_style
        )

        self.sizer = wx.StaticBoxSizer(self, wx.VERTICAL)
        self.sizer.Add(self.textctrl, flag=wx.EXPAND | wx.ALL, border=0)

    def get_text(self) -> str:
        return self.textctrl.GetValue()
