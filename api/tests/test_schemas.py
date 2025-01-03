import binascii
import pytest
from api.schemas import Game, AddGameRequest


class TestGameSchema:
    def test_uri(self):
        qm = Game(
            name="test",
            display_name="Test Magnet",
            magnet="bWFnbmV0Oj94dD11cm46YnRpaDoxMjM0NTY3ODkwYWJjZGVm",
            version=1.0,
            filesize=1024,
            date_added=1645978000.0,
            id="12345",
            key="",
        )
        assert qm.uri == "bWFnbmV0Oj94dD11cm46YnRpaDoxMjM0NTY3ODkwYWJjZGVm"

    def test_decoded_uri(self):
        qm1 = Game(
            name="test",
            display_name="Test Magnet",
            magnet="bWFnbmV0Oj94dD11cm46YnRpaDoxMjM0NTY3ODkwYWJjZGVm",
            version=1.0,
            filesize=1024,
            date_added=1645978000.0,
            id="12345",
            key="",
        )
        assert qm1.decoded_uri == "magnet:?xt=urn:btih:1234567890abcdef"

    def test_encoded_uri(self):
        qm = Game(
            name="test",
            display_name="Test Magnet",
            magnet="magnet:?xt=urn:btih:1234567890abcdef",
            version=1.0,
            filesize=1024,
            date_added=1645978000.0,
            id="12345",
            key="",
        )
        result = qm.encoded_uri
        assert type(result) == str
        assert result == "bWFnbmV0Oj94dD11cm46YnRpaDoxMjM0NTY3ODkwYWJjZGVm"

    def test_decoded_uri_with_invalid_magnet(self):
        qm = Game(
            name="test",
            display_name="Test Magnet",
            magnet="invalid_base64_string",
            version=1.0,
            filesize=1024,
            date_added=1645978000.0,
            id="12345",
            key="",
        )
        with pytest.raises(binascii.Error):
            qm.decoded_uri()

    def test_empty_display_name_string(self):
        with pytest.raises(ValueError):
            AddGameRequest(
                name="test",
                display_name="",
                magnet="bWFnbmV0Oj94dD11cm46YnRpaDoxMjM0NTY3ODkwYWJjZGVm",
                version=1.0,
                filesize=1024,
                date_added=1645978000.0,
                id="12345",
                key="",
            )
