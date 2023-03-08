import wx


class InstallProgressDlg(wx.Dialog):
    def __init__(self, parent: wx.Frame):
        from quest_cave_app import QuestCaveApp

        self.app: QuestCaveApp = wx.GetApp()
        super().__init__(
            parent,
            title="Installing",
            style=wx.BORDER_SIMPLE
            | wx.CAPTION
            | wx.RESIZE_BORDER
            | wx.MAXIMIZE_BOX
            | wx.MINIMIZE_BOX
            | wx.SYSTEM_MENU,
        )
        self._create_controls()
        self._do_layout()
        self._bind_events()
        self._do_properties()

    def _bind_events(self) -> None:
        self.Bind(wx.EVT_BUTTON, self._on_cancel_button, self.cancel_button)

    def _create_controls(self) -> None:
        self.text_ctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.cancel_button = wx.Button(self, label="Cancel")

    def _do_layout(self) -> None:
        BORDER = 10
        dlg_vbox = wx.BoxSizer(wx.VERTICAL)
        txtctrl_hbox = wx.BoxSizer(wx.HORIZONTAL)
        txtctrl_hbox.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, BORDER)
        button_hbox = wx.BoxSizer(wx.HORIZONTAL)
        button_hbox.Add(self.cancel_button, 0, wx.ALL, BORDER)
        dlg_vbox.Add(txtctrl_hbox, 1, wx.EXPAND | wx.ALL, BORDER)
        dlg_vbox.Add(button_hbox, 0, wx.ALIGN_CENTER_HORIZONTAL, BORDER)
        self.SetSizerAndFit(dlg_vbox)

    def _do_properties(self) -> None:
        # make the font larger in the textctrl
        font = self.text_ctrl.GetFont()
        # increment the pointsize by 2
        font.SetPointSize(font.GetPointSize() + 2)
        self.text_ctrl.SetFont(font)
        self.SetWindowStyleFlag(self.GetWindowStyleFlag() & ~wx.CLOSE_BOX)
        width, height = self.GetParent().GetSize()
        self.SetSize((int(width * 0.8), int(height * 0.8)))
        self.CenterOnParent()

    def write(self, text: str) -> None:
        text += "\n"
        wx.CallAfter(self.text_ctrl.AppendText, text=text)

    def _on_cancel_button(self, evt: wx.CommandEvent) -> None:
        """cancel the install and destroy the dialog

        Args:
            evt (wx.CommandEvent):
        """
        if self.IsModal():
            self.EndModal(wx.CANCEL)
        else:
            self.Destroy()
        self.app.install_dialog = None
