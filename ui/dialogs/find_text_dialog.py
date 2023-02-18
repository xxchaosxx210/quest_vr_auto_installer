import wx


class FindTextDialog(wx.Dialog):
    def __init__(self, label: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.textctrl = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.textctrl, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)

        # create the static box
        staticbox = wx.StaticBox(parent=self, label=label)
        vbox = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
        vbox.Add(hbox, flag=wx.ALL | wx.EXPAND, border=5)

        # create the OK and Cancel buttons
        ok_button = wx.Button(self, id=wx.ID_OK, label="OK")
        cancel_button = wx.Button(self, id=wx.ID_CANCEL, label="Cancel")

        # add the buttons to a horizontal box
        button_box = wx.BoxSizer(wx.HORIZONTAL)
        button_box.Add(ok_button, flag=wx.ALL, border=5)
        button_box.Add(cancel_button, flag=wx.ALL, border=5)

        # add the vbox and button_box to a vertical box
        vbox_main = wx.BoxSizer(wx.VERTICAL)
        vbox_main.Add(vbox, flag=wx.ALL | wx.EXPAND, border=10)
        vbox_main.Add(button_box, flag=wx.ALL | wx.CENTER, border=10)

        # set the sizer for the dialog
        self.SetSizerAndFit(vbox_main)

        self.SetSize(kwargs["size"])
        self.CenterOnParent()

    def GetText(self) -> str:
        """Get the text entered in the textctrl."""
        return self.textctrl.GetValue()
