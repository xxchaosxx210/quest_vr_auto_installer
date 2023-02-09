import lib.utils as utils
import pytest

from deluge.handler import MagnetData


def test_is_connected_to_internet():
    assert utils.is_connected_to_internet() == True


def test_apk_exists_with_attribute_error():
    md = MagnetData(
        "this is a test of magnet uri", ".\\downloads\\mock.apk", 0, None, 5, None
    )
    with pytest.raises(AttributeError):
        utils.apk_exists(md)
