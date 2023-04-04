import wx


class TextCtrlStaticBox(wx.StaticBox):
    """
    This Class defines a custom wxPython widget called TextCtrlStaticBox,
    which is a combination of a wx.StaticBox and a wx.TextCtrl.
    It allows the user to input text or numeric values in a box with a label.
    The widget has methods to get and set the text value,
    as well as methods to get the value as an integer or float,
    with error handling if the input is not a valid number.
    """

    def __init__(
        self, parent: wx.Window, texctrl_value: str, textctrl_style: int, label: str
    ):
        """
        Args:
            parent (wx.Window): the parent window
            texctrl_value (str): the initial value of the textctrl
            textctrl_style (int): the style of the textctrl
            label (str): the wxStaticBox label
        """
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

    def get_int(self) -> int:
        """gets integer value from textctrl

        Raises:
            TypeError: if the value is not a integer

        Returns:
            int: the converted integer value
        """
        text: str = self.textctrl.GetValue()
        if not text.isdigit():
            raise TypeError(f"{self.GetLabel()} field must be a Numeric Value")
        return int(text)

    def get_float(self) -> float:
        """gets float value from textctrl

        Raises:
            TypeError: if the value is not a float

        Returns:
            float: the converted float value
        """
        text = self.textctrl.GetValue()
        try:
            value = float(text)
        except ValueError:
            raise TypeError(f"{self.GetLabel()} field must a Float value")
        else:
            return value
