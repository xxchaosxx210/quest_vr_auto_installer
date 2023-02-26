import asyncio
import subprocess
from unittest.mock import MagicMock, AsyncMock

import pytest

import adblib.adb_interface as adb


def get_mock_stream_reader() -> MagicMock:
    st_reader = MagicMock(asyncio.StreamReader)
    st_reader.read = AsyncMock()
    return st_reader


def test__remove_showwindow_flag():
    stup_info = adb._remove_showwindow_flag()
    assert (stup_info.dwFlags & subprocess.STARTF_USESHOWWINDOW) == 1


class TestGetBytesFromStream:
    @pytest.mark.asyncio
    async def test_get_bytes_from_stream_equal_to_bytes(self):
        stream_reader = get_mock_stream_reader()
        stream_reader.read.return_value = b""
        v = await adb._get_bytes_from_stream(stream_reader=stream_reader)
        assert type(v) == bytes

    @pytest.mark.asyncio
    async def test_get_bytes_From_stream_is_none(self):
        v = await adb._get_bytes_from_stream(stream_reader=None)
        assert type(v) == bytes
