import wx


class InstallProgressDlg(wx.Dialog):
    def __init__(self, parent: wx.Frame):
        from quest_cave_app import QuestCaveApp

        self.app: QuestCaveApp = wx.GetApp()
        super().__init__(
            parent,
            title="Installing",
            style=wx.DEFAULT_DIALOG_STYLE | wx.CLOSE_BOX | wx.CAPTION,
        )

        self.text_ctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.cancel_button = wx.Button(self, label="Cancel")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text_ctrl, 1, wx.EXPAND)
        sizer.Add(self.cancel_button, 0, wx.ALIGN_CENTER)

        self.SetSizerAndFit(sizer)
        self.SetWindowStyleFlag(self.GetWindowStyleFlag() & ~wx.CLOSE_BOX)
        width, height = parent.GetSize()
        self.SetSize((width, 300))
        self.CenterOnParent()

        self.Bind(wx.EVT_BUTTON, self._on_cancel_button, self.cancel_button)

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
