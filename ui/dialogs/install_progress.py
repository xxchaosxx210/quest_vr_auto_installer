import time

import wx

import lib.tasks


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
        self._do_properties()
        self._timer_setup()
        self._bind_events()
        self.CenterOnParent()

    def _bind_events(self) -> None:
        self.Bind(wx.EVT_BUTTON, self._on_cancel_button, self.cancel_button)
        self.Bind(wx.EVT_BUTTON, self._on_close_button, self.close_button)

    def _timer_setup(self) -> None:
        self._elapsed_time: float = 0.0
        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_timer, self._timer)
        self._timer.Start(1000)

    def _on_timer(self, event: wx.TimerEvent) -> None:
        """update the elapsed time every second

        Args:
            event (wx.TimerEvent):
        """
        self._elapsed_time += 1.0
        # format the elapsed time using the time module
        self.SetTitle(
            f"Elapsed Time: ({time.strftime('%H:%M:%S', time.gmtime(self._elapsed_time))})"
        )

    def _create_controls(self) -> None:
        self.text_ctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.cancel_button = wx.Button(self, id=wx.ID_CANCEL, label="Cancel")
        self.close_button = wx.Button(self, id=wx.ID_CLOSE, label="Close")

    def _do_layout(self) -> None:
        BORDER = 10
        dlg_vbox = wx.BoxSizer(wx.VERTICAL)
        txtctrl_hbox = wx.BoxSizer(wx.HORIZONTAL)
        txtctrl_hbox.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, BORDER)
        button_hbox = wx.BoxSizer(wx.HORIZONTAL)
        button_hbox.Add(self.cancel_button, 0, wx.ALL, BORDER)
        button_hbox.Add(self.close_button, 0, wx.ALL, BORDER)
        dlg_vbox.Add(txtctrl_hbox, 1, wx.EXPAND | wx.ALL, BORDER)
        dlg_vbox.Add(button_hbox, 0, wx.ALIGN_CENTER_HORIZONTAL, BORDER)
        self.SetSizerAndFit(dlg_vbox)
        # resize the dialog after the sizer is set
        width, height = self.GetParent().GetSize()
        self.SetSize((int(width * 0.8), int(height * 0.8)))

    def _do_properties(self) -> None:
        """set the textctrl font, remove the dialog close box"""
        # make the font larger in the textctrl
        font = self.text_ctrl.GetFont()
        # increment the pointsize by 1
        font.SetPointSize(font.GetPointSize() + 1)
        self.text_ctrl.SetFont(font)
        self.SetWindowStyleFlag(self.GetWindowStyleFlag() & ~wx.CLOSE_BOX)

    def writeline(self, text: str) -> None:
        """displays the text in the textctrl and adds a newline

        Args:
            text (str): the text to display
        """
        text += "\n"
        wx.CallAfter(self.text_ctrl.AppendText, text=text)

    def _on_cancel_button(self, evt: wx.CommandEvent) -> None:
        """cancel the install is an install task is running

        Args:
            evt (wx.CommandEvent):
        """
        try:
            lib.tasks.cancel_task(self.app.start_install_process)
        except KeyError:
            return
        else:
            # stop the timer
            if self._timer.IsRunning():
                self._timer.Stop()
            self.writeline("Cancelling installation please wait...")

    def _on_close_button(self, evt: wx.CommandEvent) -> None:
        """check if the install is running if it isnt then close the dialog

        Args:
            evt (wx.CommandEvent):
        """
        try:
            task = lib.tasks.get_task(self.app.start_install_process)
        except KeyError:
            # no task. ignore this exception and close dialog
            pass
        else:
            # task exists. Check if it is running
            if lib.tasks.is_task_running(task):
                self.writeline(
                    "Cannot Close while installing. You need to Cancel first."
                )
                return
        self.close()

    def complete(self) -> None:
        """stops the timer and sets the title to install complete"""
        self._timer.Stop()
        self.SetTitle(
            f"Install Complete. Total Elapsed Time: ({time.strftime('%H:%M:%S', time.gmtime(self._elapsed_time))})"
        )
        self._elapsed_time = 0.0

    def close(self) -> None:
        """check if dialog is modal and close or destroy the dialog"""
        self.app.install_dialog = None
        self.SetReturnCode(self.close_button.GetId())
        if self.IsModal():
            self.Close()
        else:
            self.Destroy()
