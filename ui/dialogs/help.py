from typing import Tuple

import wx
import wx.html2 as html2


_HTML = """<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QuestCave Help</title>
</head>

<body>
    <header>
        <h1>QuestCave version 1.0.0</h1>
        <h3>Developed by Paul Millar</h3>
    </header>
    <div class="description">
        <p>
            QuestCave is an App that downloads and installs Games (paid/free) to Meta Quest 2 devices
            Games will be added when they become availible. More futures updates will become availible too
            you can check for new Updates and bug fixes on the QuestCave website.
        </p>
        <a href="https://questcave.com/get-the-app">https://questcave.com/get-the-app</a>
    </div>
    <div class="nav-chapters">
        <h3>Table of Contents</h3>
        <ul>
            <li><a href="#chapter-one">Chapter 1- How to Setup the Quest 2 for Quest Cave App</a></li>
        </ul>
    </div>
    <div class="chapter-one" id="chapter-one">
        <h3>Chapter 1 - How to setup the Quest 2 for QuestCave</h3>
    </div>
    <footer>
    </footer>
</body>

</html>"""


def load_dialog(parent: wx.Window) -> None:
    dlg = HtmlHelpDlg(parent, wx.ID_ANY, "QuestCave Help", (600, 400))
    dlg.ShowModal()
    dlg.Destroy()


class HtmlHelpDlg(wx.Dialog):
    def __init__(
        self, parent: wx.Window, id: int, title: str, size: Tuple[int, int]
    ) -> None:
        super().__init__(
            parent,
            id,
            title,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )

        self._create_controls()
        self._bind_events()
        self._do_layout(size)

    def _create_controls(self) -> None:
        self.browser: html2.WebView = html2.WebView.New(self)
        self.browser.SetPage(_HTML, "")
        self.close_button = wx.Button(self, wx.ID_CLOSE, "Close")

    def _bind_events(self) -> None:
        self.Bind(wx.EVT_BUTTON, self._on_close_button, self.close_button)

    def _do_layout(self, size: Tuple[int, int]) -> None:
        BORDER = 5
        vbox = wx.BoxSizer(wx.VERTICAL)
        browser_hbox = wx.BoxSizer(wx.HORIZONTAL)
        browser_hbox.Add(self.browser, 1, wx.EXPAND | wx.ALL, BORDER)
        vbox.Add(browser_hbox, 1, wx.EXPAND | wx.ALL, BORDER)
        button_hbox = wx.BoxSizer(wx.HORIZONTAL)
        button_hbox.Add(self.close_button, 1, wx.ALL, BORDER)
        vbox.Add(button_hbox, 0, wx.ALIGN_CENTER_HORIZONTAL, BORDER)
        self.SetSizerAndFit(vbox)
        self.SetSize(size)

    def _on_close_button(self, event: wx.CommandEvent) -> None:
        self.EndModal(event.GetId())
