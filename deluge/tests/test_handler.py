from unittest.mock import Mock, patch

from deluge.handler import add_magnet_to_session


@patch("deluge_client.LocalDelugeRPCClient")
def test_add_magnet_on_session_return_torrent_id(mock_client: Mock) -> None:
    torrent_id = "thisisamockid"
    mock_client.call = Mock(return_value=torrent_id)
    assert add_magnet_to_session(mock_client, "ndjncdnjnc", {}) == torrent_id
