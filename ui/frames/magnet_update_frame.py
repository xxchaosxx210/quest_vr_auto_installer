import asyncio
import base64
from typing import Tuple

import wx
import aiohttp

from ui.utils import TextCtrlStaticBox, show_error_message
from lib.settings import Settings
from qvrapi.schemas import QuestMagnetWithKey
from qvrapi.api import ApiError, update_game_magnet
from lib.utils import format_timestamp_to_str


def get_changed_properties(original: dict, new: dict) -> dict:
    """compare the original dict with a new dict and check if any fields have changed

    Args:
        original (dict): original dict to compare with
        new (dict): the new dict

    Returns:
        dict: returns a dict with fields that have changed from the original
    """
    changed = {}
    for key in original:
        if key in new and original[key] != new[key]:
            changed[key] = new[key]
    return changed


class MagnetUpdateFrame(wx.Frame):
    def __init__(
        self,
        parent: wx.Frame,
        title: str,
        size: Tuple[int, int],
        magnet: QuestMagnetWithKey,
    ):
        from q2gapp import Q2GApp

        self.app: Q2GApp = wx.GetApp()
        super().__init__(parent=parent, title=title, size=size)

        self.original_magnet_data = magnet

        panel = wx.Panel(self, -1)

        self.static_txtctrls = self._create_static_text_ctrls(panel, magnet)

        panel_vbox = wx.BoxSizer(wx.VERTICAL)

        for st_txt_ctrl in self.static_txtctrls.values():
            panel_vbox.Add(st_txt_ctrl.sizer, 0, wx.EXPAND, 0)

        update_btn = wx.Button(panel, wx.ID_SAVE, "Update")
        delete_btn = wx.Button(panel, wx.ID_DELETE, "Delete")
        close_btn = wx.Button(panel, wx.ID_CLOSE, "Close")
        self.Bind(wx.EVT_BUTTON, lambda *args: self.Destroy(), close_btn)
        self.Bind(wx.EVT_BUTTON, self._on_update_button, update_btn)
        self.Bind(wx.EVT_BUTTON, self._on_delete_button, delete_btn)

        btn_hbox = wx.BoxSizer(wx.HORIZONTAL)
        btn_hbox.Add(update_btn, 0, wx.EXPAND, 0)
        btn_hbox.Add(delete_btn, 0, wx.EXPAND, 0)
        btn_hbox.Add(close_btn, 0, wx.EXPAND, 0)

        panel_vbox.Add(btn_hbox, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        panel.SetSizerAndFit(panel_vbox)

        gs = wx.GridSizer(cols=1)
        gs.Add(panel, 1, wx.EXPAND | wx.ALL, 0)
        self.SetSizerAndFit(gs)
        self.SetSize(size)

    def _create_static_text_ctrls(
        self, parent: wx.Panel, magnet: QuestMagnetWithKey
    ) -> dict:
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

        def _get_correct_value(_name, _value) -> any:
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

    def _on_update_button(self, evt: wx.CommandEvent) -> None:
        data = self._get_values_from_controls()
        original_data = self.original_magnet_data.dict(exclude={"date_added", "key"})
        data_update = get_changed_properties(original_data, data)
        if not data_update:
            return
        asyncio.get_event_loop().create_task(self.update_magnet(data_update))

    async def update_magnet(self, data_to_update: dict) -> None:
        settings = Settings.load()
        try:
            await update_game_magnet(
                settings.token, self.original_magnet_data.key, data_to_update
            )
        except ApiError as err:
            show_error_message(err.message, f"Code: {err.status_code}")
        except aiohttp.ClientConnectionError as err:
            show_error_message("".join(err.args))
        else:
            wx.MessageBox("Game has been updated", "", wx.OK | wx.ICON_EXCLAMATION)
        finally:
            return

    def _on_delete_button(self, evt: wx.CommandEvent) -> None:
        evt.Skip()