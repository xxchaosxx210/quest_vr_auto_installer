import socket
import urllib.parse


def test_host(url: str, timeout: float = 0.2) -> bool:
    """checks if a host is reachable.

    Args:
        url (str): should have "http://host:port" url format
        timeout (float): connection timeout. Should small amount if testing on localhost. Defaults: 0.2

    Raises:
        TypeError: raised if hostname or port is None

    Returns:
        bool: True if connected successfully, False if exception raised
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.settimeout(timeout)
            sp_result = urllib.parse.urlsplit(url)
            if isinstance(sp_result.hostname, str) and isinstance(sp_result.port, int):
                s.connect((sp_result.hostname, sp_result.port))
                return True
            else:
                raise TypeError("Hostname and Port address cannot be of Nonetype")
        except (socket.error, TypeError) as err:
            if not isinstance(err, socket.error):
                print(
                    f"Exception not socket related raised trying to connect to the test server {err.__str__()}"
                )
    return False
