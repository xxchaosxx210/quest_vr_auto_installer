import asyncio
import pdb
from unittest.mock import Mock, patch

import pytest

import deluge.handler


@patch("deluge_client.LocalDelugeRPCClient")
@pytest.mark.asyncio
async def test_add_magnet_on_session_return_torrent_id(mock_client: Mock) -> None:
    torrent_id = "thisisamockid"
    mock_client.call = Mock(return_value=torrent_id)
    result = await deluge.handler.add_magnet_to_session(mock_client, "ndjncdnjnc", {})
    assert result == torrent_id


@patch("deluge_client.LocalDelugeRPCClient")
@pytest.mark.asyncio
async def test_add_magnet_on_session_already_in_session(
    mock_client: Mock,
) -> None:
    def raise_exception(*args, **kwargs):
        raise Exception(
            "deluge.error.AddTorrentError: Torrent already in session (hxnjn73636bhbdh)"
        )

    mock_client.call = Mock(side_effect=raise_exception, return_value=None)
    torrent_id = await deluge.handler.add_magnet_to_session(
        mock_client, "kdcmdjmckdm", {}
    )
    assert torrent_id != None


@patch("deluge_client.LocalDelugeRPCClient")
@pytest.mark.asyncio
async def test_add_magnet_on_session_already_in_session_re_pattern_fail(
    mock_client: Mock,
) -> None:
    def raise_exception(*args, **kwargs):
        raise Exception(
            "deluge.error.AddTorrentError: Torrent already in session (hxnjn73:¬6bhbdh)"
        )

    mock_client.call = Mock(side_effect=raise_exception, return_value=None)
    torrent_id = await deluge.handler.add_magnet_to_session(
        mock_client, "kdcmdjmckdm", {}
    )
    assert torrent_id == None
