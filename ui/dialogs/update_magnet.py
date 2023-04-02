"""
update_magnate.py

Defines a dialog window for updating or deleting a game magnet. 
It allows the user to view and modify the properties of a game magnet, 
such as its name, display name, magnet link, version, file size, and date added. 
The user can update the magnet by clicking the "Update" button, 
which sends a request to the API to update the magnet with the new values. 
The user can also delete the magnet by clicking the "Delete" button, 
which prompts the user to confirm the deletion and then sends a request to the API to delete the magnet. 
The dialog window is created using wxPython and is asynchronous using asyncio."""

import asyncio
import base64
from typing import Any, Tuple
import logging

import wx
import aiohttp
import wxasync

import api.client
from api.schemas import Game
from api.exceptions import ApiError
from ui.utils import (
    TextCtrlStaticBox,
    show_error_message,
    async_progress_dialog,
    BitmapButtonLabel,
)
from lib.settings import Settings
from lib.utils import format_timestamp_to_str, get_changed_properties


_Log = logging.getLogger()


async def load_dialog(parent: wx.Frame, title: str, magnet: Game | None) -> int:
    dlg = MagnetUpdateDlg(
        parent=parent,
        title=title,
        style=wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX,
        size=parent.GetSize(),
        magnet=magnet,
    )
    result = await wxasync.AsyncShowDialogModal(dlg)
    return result


@async_progress_dialog("Removing...", "Removing Game please wait...", timeout=5)
async def delete_game(dialog: wx.Dialog, token: str, key: str) -> bool:
    """sends a delete request to the backend and deletes the game

    Args:
        dialog (wx.Dialog): The dialog window to close
        key (str): the key related to the game in the database

    Returns:
        bool: returns True if the game was deleted successfully
    """
    try:
        # if 204 is returned then the game was deleted successfully
        await api.client.delete_game(token, key)
        return True
    except ApiError as err:
        show_error_message(err.message, f"Code: {err.status_code}")
    except Exception as err:
        show_error_message(err.__str__())
    return False


class MagnetUpdateDlg(wx.Dialog):
    def __init__(
        self,
        parent: wx.Frame,
        title: str,
        size: Tuple[int, int],
        style: int,
        magnet: Game | None,
    ):
        from quest_cave_app import QuestCaveApp

        self.app: QuestCaveApp = wx.GetApp()
        super().__init__(parent=parent, title=title, size=size, style=style)

        self.original_magnet_data = magnet

        self._do_controls()
        self._do_layout()
        self._do_events()
        self._do_properties(size)

    def _do_properties(self, size: Tuple[int, int]):
        self.SetSize(size)
        self.CenterOnParent()

    def _do_controls(self):
        self.panel = wx.Panel(self, -1)

        self.static_txtctrls = self._create_static_text_ctrls(
            self.panel, self.original_magnet_data
        )
        MIN_BUTTON_SIZE = (100, 30)
        self.update_btn = BitmapButtonLabel(
            self.panel,
            wx.ID_SAVE,
            "Update",
            wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_BUTTON),
            (10, 10),
            MIN_BUTTON_SIZE,
        )
        self.delete_btn = BitmapButtonLabel(
            self.panel,
            wx.ID_DELETE,
            "Delete",
            wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_BUTTON),
            (10, 10),
            MIN_BUTTON_SIZE,
        )
        self.close_btn = BitmapButtonLabel(
            self.panel,
            wx.ID_CLOSE,
            "Close",
            wx.ArtProvider.GetBitmap(wx.ART_CLOSE, wx.ART_BUTTON),
            (10, 10),
            MIN_BUTTON_SIZE,
        )

    def _do_layout(self):
        BORDER = 5
        panel_vbox = wx.BoxSizer(wx.VERTICAL)

        # Game Panel Ctrl Sizer
        for st_txt_ctrl in self.static_txtctrls.values():
            txtctrl_hbox = wx.BoxSizer(wx.HORIZONTAL)
            txtctrl_hbox.Add(st_txt_ctrl.sizer, 1, wx.EXPAND, BORDER)
            panel_vbox.Add(txtctrl_hbox, 0, wx.EXPAND, 0)
            panel_vbox.AddSpacer(BORDER * 2)

        panel_vbox.AddStretchSpacer(1)

        # Button Sizer
        btn_hbox = wx.BoxSizer(wx.HORIZONTAL)
        btn_hbox.Add(self.delete_btn, 0, wx.EXPAND, 0)
        btn_hbox.AddSpacer(BORDER * 2)
        btn_hbox.Add(self.update_btn, 0, wx.EXPAND, 0)
        btn_hbox.AddSpacer(BORDER * 2)
        btn_hbox.Add(self.close_btn, 0, wx.EXPAND, 0)

        panel_vbox.Add(btn_hbox, 0, wx.ALIGN_RIGHT, 0)
        panel_vbox.AddSpacer(10)
        self.panel.SetSizer(panel_vbox)

        gs = wx.GridSizer(cols=1)
        gs.Add(self.panel, 1, wx.EXPAND | wx.ALL, 20)
        self.SetSizerAndFit(gs)

    def _do_events(self):
        wxasync.AsyncBind(wx.EVT_BUTTON, self.__on_close_event, self.close_btn)
        wxasync.AsyncBind(wx.EVT_BUTTON, self._on_update_button, self.update_btn)
        wxasync.AsyncBind(wx.EVT_BUTTON, self._on_delete_button, self.delete_btn)

    def _create_static_text_ctrls(self, parent: wx.Panel, magnet: Game | None) -> dict:
        """create the static text controls in a dict for iterating and sorting

        Args:
            parent (wx.Panel): should be a panel
            magnet (QuestMagnetWithKey): the magnet to extra information from and add to the textctrls

        Returns:
            dict: returns the textctrlstatoxs stored within dict
        """
        ctrls = {}
        if magnet is not None:
            ctrls["key"] = TextCtrlStaticBox(
                parent, magnet.key, wx.TE_READONLY | wx.TE_NO_VSCROLL, "Key"
            )
            ctrls["name"] = TextCtrlStaticBox(
                parent, magnet.name, wx.TE_NO_VSCROLL, "Name"
            )
            ctrls["display_name"] = TextCtrlStaticBox(
                parent, magnet.display_name, wx.TE_NO_VSCROLL, "Display Name"
            )
            ctrls["magnet"] = TextCtrlStaticBox(
                parent, magnet.decoded_uri, wx.TE_MULTILINE, "Magnet Link"
            )
            ctrls["version"] = TextCtrlStaticBox(
                parent, str(magnet.version), wx.TE_NO_VSCROLL, "Version"
            )
            ctrls["filesize"] = TextCtrlStaticBox(
                parent, f"{magnet.filesize}", wx.TE_READONLY, "FileSize (Bytes)"
            )
            ctrls["date_added"] = TextCtrlStaticBox(
                parent,
                format_timestamp_to_str(magnet.date_added, True),
                wx.TE_READONLY,
                "Date Added",
            )
            ctrls["id"] = TextCtrlStaticBox(
                parent, magnet.id, wx.TE_NO_VSCROLL, "Torrent ID"
            )
        else:
            ctrls["key"] = TextCtrlStaticBox(
                parent, "", wx.TE_READONLY | wx.TE_NO_VSCROLL, "Key"
            )
            ctrls["name"] = TextCtrlStaticBox(parent, "", wx.TE_NO_VSCROLL, "Name")
            ctrls["display_name"] = TextCtrlStaticBox(
                parent, "", wx.TE_NO_VSCROLL, "Display Name"
            )
            ctrls["magnet"] = TextCtrlStaticBox(
                parent, "", wx.TE_MULTILINE, "Magnet Link"
            )
            ctrls["version"] = TextCtrlStaticBox(
                parent, "", wx.TE_NO_VSCROLL, "Version"
            )
            ctrls["filesize"] = TextCtrlStaticBox(
                parent, "", wx.TE_READONLY, "FileSize (Bytes)"
            )
            ctrls["date_added"] = TextCtrlStaticBox(
                parent, "", wx.TE_READONLY, "Date Added"
            )
            ctrls["id"] = TextCtrlStaticBox(parent, "", wx.TE_NO_VSCROLL, "Torrent ID")

        return ctrls

    def _get_values_from_controls(self) -> dict:
        """gets the values from textctrls and returns as dict

        Returns:
            dict:
        """

        def _get_correct_value(_name: str, _value: Any) -> Any:
            """checks for correct value types and does extra encoding if needed depending on
            the name

            Args:
                _name (_type_): the name of the key
                _value (_type_): the text value to be changed

            Returns:
                any: new value
            """
            if _name == "magnet":
                # rencode the string back to base64
                _value = base64.b64encode(_value.encode("utf-8")).decode("utf-8")
            elif _name == "version":
                # convert the value to a float type
                _value = float(_value)
            elif _name == "filesize":
                # convert the filesize string to an integer
                _value = int(_value)
            return _value

        return {
            name: _get_correct_value(name, ctrl.get_text())
            for name, ctrl in self.static_txtctrls.items()
        }

    async def _on_update_button(self, evt: wx.CommandEvent) -> None:
        """update button pressed check if any data has been changed in the textctrls
        update if change has been made and send to api

        Args:
            evt (wx.CommandEvent): button event not used
        """
        if self.original_magnet_data is None:
            # ignore
            return
        # get the string values from the textctrls and convert back to a dict
        data = self._get_values_from_controls()
        # get the original magnet object and convert into a dict exclude the date_added and key fields
        original_data = self.original_magnet_data.dict(exclude={"date_added", "key"})
        # now compare the original saved magnet with the data extracted from the controls
        data_update = get_changed_properties(original_data, data)
        if not data_update:
            return
        # there have been changes update the fields only that have changed
        await self.update_magnet(data_update)

    async def update_magnet(self, data_to_update: dict) -> None:
        """update the magnet data to the API

        Args:
            data_to_update (dict):
        """
        if self.original_magnet_data is None:
            return
        settings = Settings.load()
        if settings.token is None:
            return
        try:
            updated_magnet = await api.client.update_game_magnet(
                settings.token, self.original_magnet_data.key, data_to_update
            )
        except ApiError as err:
            show_error_message(err.message, f"Code: {err.status_code}")
        except aiohttp.ClientConnectionError as err:
            show_error_message(err.__str__())
        else:
            wx.MessageBox("Game has been updated", "", wx.OK | wx.ICON_EXCLAMATION)
            # get the game from the database and update the game in the magnet_listpanel
            # Ill do this tomorrow!!
            if self.app.magnets_listpanel is not None:
                index = self.app.magnets_listpanel.find_row_by_torrent_id(
                    self.original_magnet_data.id
                )
                wx.CallAfter(
                    self.app.magnets_listpanel.update_row,
                    index=index,
                    quest_data=updated_magnet,
                )
            # self.original_magnet_data = updated_magnet
            # Need to update the original_magnet_data here
            self.original_magnet_data = updated_magnet

    async def _on_delete_button(self, evt: wx.CommandEvent) -> None:
        """handles the event of clicking on a delete button. It first checks if there is any original magnet data, and if not, it returns.
        If there is original magnet data, it displays a message dialog asking the user if they are sure they want to delete the magnet.
        If the user clicks OK, it loads the user's settings, creates an asynchronous task to delete the game using the user's token and the magnet's key,
        and waits for the task to complete. If the task is successful, it displays a notification message indicating that the magnet has been deleted, sets the return code to CLOSE,
        and closes the dialog. Finally, it skips the event.

        Args:
            evt (wx.CommandEvent): Not used
        """
        if self.original_magnet_data is None:
            return
        # prompt before deleting
        with wx.MessageDialog(
            self,
            "Are you sure you want to delete this magnet?",
            "Delete Magnet",
            wx.OK | wx.CANCEL | wx.ICON_EXCLAMATION,
        ) as dlg:
            return_code = dlg.ShowModal()

        if return_code == wx.ID_OK:
            # send a delete request within a task for the entry and notify if successful
            settings = Settings.load()
            task = asyncio.create_task(
                delete_game(self, settings.token, self.original_magnet_data.key)
            )
            result = await asyncio.wait_for(task, None)
            if result:
                await self.__on_close_event(evt)
        evt.Skip()

    async def __on_close_event(self, evt: wx.CommandEvent) -> None:
        """universal close handler sets the correct return code and closes the dialog

        Args:
            evt (wx.CommandEvent): used to obtain the button id which was clicked from
        """
        btn_id = evt.GetId()
        if self.IsModal():
            # modal dialog
            self.EndModal(btn_id)
            self.Destroy()
        else:
            # async dialog
            self.SetReturnCode(btn_id)
            self.Close()
