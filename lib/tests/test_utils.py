import ctypes
from unittest.mock import Mock, patch
import socket


import lib.utils
import lib.config


@patch("platform.system")
def test_win32_is_connected_to_internet_fail(mock_system: Mock):
    ctypes.windll.wininet.InternetGetConnectedState = Mock(return_value=0)
    mock_system.return_value = "Windows"
    assert lib.utils.is_connected_to_internet() == False
    # with unittest.TestCase().assertRaises(OSError) as cm:
    #     mock_win32_function()


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
