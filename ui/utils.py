import os
from typing import Tuple

import wx


def load_progress_dialog(
    parent: wx.Window, title: str, message: str, maximum: int = 100
) -> wx.ProgressDialog:
    return wx.ProgressDialog(
        title=title,
        message=message,
        maximum=maximum,
        parent=parent,
        style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_SMOOTH,
    )


def create_bitmap_button(
    filename: str,
    tooltip: str | None,
    parent: wx.Window,
    id: int = wx.ID_ANY,
    size: Tuple[int, int] = (24, 24),
) -> wx.BitmapButton:
    """loads the bitmap from specified file and returns a BitmapButton control

    Args:
        filename (str): the image file to convert to bitmap
        tooltip (str | None): sets a tooltip. Set None as it can be annoying
        parent (wx.Window): the parent window to attach the bitmapbutton to
        id (int, optional): the ID of the bitmapbutton. Defaults to wx.ID_ANY.
        size (Tuple[int, int], optional): the size of the bitmap. Defaults to (24, 24).

    Returns:
        wx.BitmapButton: returns a BitmapButton
    """
    bmp = get_image(filename).ConvertToBitmap()
    bmp_btn = wx.BitmapButton(parent, id, bmp, size=size)
    if tooltip is not None:
        bmp_btn.SetToolTip(tooltip)
    return bmp_btn


def show_error_message(message: str, caption: str = "Error") -> None:
    """show a messagebox with an error icon and error caption

    Args:
        message (str):
        caption (str, optional): _description_. Defaults to "Error".
    """
    wx.MessageBox(message=message, caption="Error", style=wx.OK | wx.ICON_ERROR)


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

        self.sizer = wx.StaticBoxSizer(self, wx.HORIZONTAL)
        self.sizer.Add(self.textctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=0)

    def get_text(self) -> str:
        return self.textctrl.GetValue()

    def set_text(self, text: str) -> None:
        self.textctrl.SetValue(text)


def get_image(filename: str) -> wx.Image:
    """loads an image from file and converts to bitmap

    Args:
        filename (str): name of the file to load from the image directory

    Raises: FileNotFoundError if no file found

    Returns:
        wx.Image: the converted bitmap
    """
    full_path = os.path.join("images", filename)
    if not os.path.exists(full_path):
        raise FileNotFoundError(
            f"{full_path} does not exist. Please check the image location"
        )
    image = wx.Image(full_path, wx.BITMAP_TYPE_ANY)
    return image
