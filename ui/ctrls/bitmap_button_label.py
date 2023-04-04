from typing import Tuple

import wx


class BitmapButtonLabel(wx.Button):
    """defines a custom class called BitmapButtonLabel that inherits from wx.Button. It takes in parameters such as parent, id, label, bitmap, margin, min_size, size, pos, and style.

    When an instance of this class is created, it sets the bitmap of the button to the provided bitmap, sets the minimum size of the button to the provided min_size, and sets the bitmap margins to the provided margin.

    This class can be used to create a button with a bitmap image and custom margins.
    """

    def __init__(
        self,
        parent: wx.Window,
        id: int,
        label: str,
        bitmap: wx.Bitmap,
        margin: Tuple[int, int],
        min_size: Tuple[int, int],
        size: Tuple[int, int] = wx.DefaultSize,
        pos: Tuple[int, int] = wx.DefaultPosition,
        style: int = 0,
    ):
        """
        Initializes a new instance of the BitmapToggleButton class.

        Args:
            parent (wx.Window): The parent window.
            id (int): The identifier for the control.
            label (str): The label for the control.
            bitmap (wx.Bitmap): The bitmap to display on the button.
            margin (Tuple[int, int]): The margins around the bitmap.
            min_size (Tuple[int, int]): The minimum size of the button.
            size (Tuple[int, int], optional): The size of the button. Defaults to wx.DefaultSize.
            pos (Tuple[int, int], optional): The position of the button. Defaults to wx.DefaultPosition.
            style (int, optional): The style of the button. Defaults to 0.

        Returns:
            None
        """
        super().__init__(
            parent=parent, id=id, label=label, size=size, pos=pos, style=style
        )
        self.SetBitmap(bitmap=bitmap)
        self.SetMinSize(min_size)
        self.SetBitmapMargins(*margin)
