import lib.utils as utils


def test_is_connected_to_internet():
    assert utils.is_connected_to_internet() == True
