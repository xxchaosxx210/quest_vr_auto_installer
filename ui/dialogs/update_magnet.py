import asyncio
import base64
from typing import Any, Tuple
import logging

import wx
import wx.adv
import aiohttp
import wxasync

import api.client
from api.schemas import Game
from api.exceptions import ApiError
from ui.utils import TextCtrlStaticBox, show_error_message, async_progress_dialog
from lib.settings import Settings
from lib.utils import format_timestamp_to_str, get_changed_properties


_Log = logging.getLogger()


async def load_dialog(parent: wx.Frame, title: str, magnet: Game) -> int:
    dlg = MagnetUpdateDlg(
        parent=parent,
        title=title,
        style=wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX,
        size=parent.GetSize(),
        magnet=magnet,
    )
    result = await wxasync.AsyncShowDialogModal(dlg)
    return result


# @async_progress_dialog("Removing...", "Removing Game please wait...", timeout=5)
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
    except ApiError as e:
        show_error_message(e.message, f"Code: {e.status_code}")
    except Exception as err:
        show_error_message(e.__str__())
    else:
        return True
    finally:
        return False


class MagnetUpdateDlg(wx.Dialog):
    def __init__(
        self,
        parent: wx.Frame,
        title: str,
        size: Tuple[int, int],
        style: int,
        magnet: Game,
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
        self.update_btn = wx.Button(self.panel, wx.ID_SAVE, "Update")
        self.delete_btn = wx.Button(self.panel, wx.ID_DELETE, "Delete")
        self.close_btn = wx.Button(self.panel, wx.ID_CLOSE, "Close")

    def _do_layout(self):
        panel_vbox = wx.BoxSizer(wx.VERTICAL)

        # Game Panel Ctrl Sizer
        for st_txt_ctrl in self.static_txtctrls.values():
            panel_vbox.Add(st_txt_ctrl.sizer, 0, wx.EXPAND, 0)

        # Button Sizer
        btn_hbox = wx.BoxSizer(wx.HORIZONTAL)
        btn_hbox.Add(self.update_btn, 0, wx.EXPAND, 0)
        btn_hbox.Add(self.delete_btn, 0, wx.EXPAND, 0)
        btn_hbox.Add(self.close_btn, 0, wx.EXPAND, 0)

        # panel_vbox.AddStretchSpacer(1)
        panel_vbox.Add(btn_hbox, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        panel_vbox.AddSpacer(10)
        self.panel.SetSizer(panel_vbox)

        gs = wx.GridSizer(cols=1)
        gs.Add(self.panel, 1, wx.EXPAND | wx.ALL, 0)
        self.SetSizerAndFit(gs)

    def _do_events(self):
        wxasync.AsyncBind(wx.EVT_BUTTON, self._on_close_button, self.close_btn)
        wxasync.AsyncBind(wx.EVT_BUTTON, self._on_update_button, self.update_btn)
        wxasync.AsyncBind(wx.EVT_BUTTON, self._on_delete_button, self.delete_btn)

    def _create_static_text_ctrls(self, parent: wx.Panel, magnet: Game) -> dict:
        """create the static text controls in a dict for iterating and sorting

        Args:
            parent (wx.Panel): should be a panel
            magnet (QuestMagnetWithKey): the magnet to extra information from and add to the textctrls

        Returns:
            dict: returns the textctrlstatoxs stored within dict
        """
        ctrls = {}
        ctrls["key"] = TextCtrlStaticBox(
            parent, magnet.key, wx.TE_READONLY | wx.TE_NO_VSCROLL, "Key"
        )
        ctrls["name"] = TextCtrlStaticBox(parent, magnet.name, wx.TE_NO_VSCROLL, "Name")
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

    async def _on_close_button(self, evt: wx.CommandEvent) -> None:
        self.SetReturnCode(wx.CLOSE)
        self.Close()

    async def _on_update_button(self, evt: wx.CommandEvent) -> None:
        """update button pressed check if any data has been changed in the textctrls
        update if change has been made and send to api

        Args:
            evt (wx.CommandEvent): button event not used
        """
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
        finally:
            return

    async def _on_delete_button(self, evt: wx.CommandEvent) -> None:
        with wx.MessageDialog(
            self,
            "Are you sure you want to delete this magnet?",
            "Delete Magnet",
            wx.OK | wx.CANCEL | wx.ICON_EXCLAMATION,
        ) as dlg:
            return_code = dlg.ShowModal()

        if return_code == wx.ID_OK:
            settings = Settings.load()
            task = asyncio.create_task(
                delete_game(self, settings.token, self.original_magnet_data.key)
            )
            result = await asyncio.wait_for(task, None)
            if result:
                wx.adv.NotificationMessage(
                    "Magnet Deleted", "Magnet has been deleted", self.GetParent()
                ).Show(timeout=3)
                self.SetReturnCode(wx.CLOSE)
                self.Close()
        evt.Skip()
