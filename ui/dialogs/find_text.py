import wx


class FindTextDlg(wx.Dialog):
    """Dialog for finding text in a textctrl."""

    def __init__(self, label: str, *args, **kwargs):
        """returns wx.ID_OK if the user clicks OK, wx.ID_CANCEL if the user clicks Cancel

        Args:
            label (str): label for the textctrl
        """
        super().__init__(*args, **kwargs)
        self._create_controls(label)
        self._do_layout()
        self._bind_events()
        self.SetSize(kwargs["size"])
        self.CenterOnParent()

    def _create_controls(self, label: str) -> None:
        self.staticbox = wx.StaticBox(parent=self, label=label)
        self.textctrl = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.ok_button = wx.Button(self, id=wx.ID_OK, label="OK")
        self.cancel_button = wx.Button(self, id=wx.ID_CANCEL, label="Cancel")

    def _do_layout(self) -> None:
        textctrl_hbox = wx.BoxSizer(wx.HORIZONTAL)
        textctrl_hbox.Add(
            self.textctrl, proportion=1, flag=wx.ALL | wx.EXPAND, border=5
        )

        static_vbox = wx.StaticBoxSizer(self.staticbox, wx.VERTICAL)
        static_vbox.Add(textctrl_hbox, flag=wx.ALL | wx.EXPAND, border=5)

        button_hbox = wx.BoxSizer(wx.HORIZONTAL)
        button_hbox.Add(self.ok_button, flag=wx.ALL, border=5)
        button_hbox.Add(self.cancel_button, flag=wx.ALL, border=5)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(static_vbox, proportion=1, flag=wx.ALL | wx.EXPAND, border=10)
        vbox.Add(button_hbox, proportion=0, flag=wx.ALL | wx.CENTER, border=10)

        self.SetSizerAndFit(vbox)

    def _bind_events(self) -> None:
        self.Bind(wx.EVT_BUTTON, self._on_close, self.ok_button)
        self.Bind(wx.EVT_BUTTON, self._on_close, self.cancel_button)

    def _on_close(self, evt: wx.CommandEvent) -> None:
        if self.IsModal():
            self.EndModal(evt.GetId())
        else:
            self.SetReturnCode(evt.GetId())
            self.Close()
        evt.Skip()

    def get_text(self) -> str:
        """Get the text entered in the textctrl."""
        return self.textctrl.GetValue()
