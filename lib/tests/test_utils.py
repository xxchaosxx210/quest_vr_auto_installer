import pdb
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import sys
import socket


import lib.utils


@patch("platform.system")
@patch("socket.gethostbyname")
def test_is_connected_to_internet_unix_fail(
    mock_system: Mock, mock_gethostbyname: Mock
):
    mock_system.return_value = "Linux"
    mock_gethostbyname.return_value = "127.0.0.1"

    def mock_connect_fail(__address):
        raise socket.gaierror("Unable to connect")

    mock_sock = Mock()
    mock_sock.close = Mock(return_value=None)
    mock_sock.connect = Mock(side_effect=mock_connect_fail)

    socket.socket = Mock(return_value=mock_sock)
    # mock_create_connection.return_value = mock_socket
    assert lib.utils.is_connected_to_internet() == False
    assert mock_sock.close.called == True
