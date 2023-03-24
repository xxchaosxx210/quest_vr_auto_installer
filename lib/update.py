import re
from time import perf_counter
from html.parser import HTMLParser

import aiohttp
from typing import AsyncGenerator, Dict, List, Tuple

from api.exceptions import ApiError


class MediaFireLinkParser(HTMLParser):
    def __init__(self, *, convert_charrefs: bool = True) -> None:
        super().__init__(convert_charrefs=convert_charrefs)
        self.mediafire_url = ""
        self.a_tags: List[dict] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str | None]]) -> None:
        if tag == "a":
            group = {}
            for name, value in attrs:
                group[name] = value
            self.a_tags.append(group)

        return super().handle_starttag(tag, attrs)


def is_mediafire_url(url: str) -> bool:
    pattern = r"https?://(www\.)?mediafire\.com/.+"
    return bool(re.match(pattern, url))


async def get_download_url_from_mediafire(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200 and response.content_type != "text/html":
                raise ApiError(
                    status_code=response.status, message=response.reason.__str__()
                )

            data = await response.text()
            parser = MediaFireLinkParser()
            parser.feed(data)
            return parser.mediafire_url


async def download(
    url: str,
) -> AsyncGenerator[Tuple[bytes, int, int, float], None]:
    """downloads the update from the server

    Args:
        url (str): the url to download the update from

    Raises:
        ApiError: raises if status code is not 200

    Yields:
        Iterator[AsyncGenerator[Tuple[bytes, int, int, float], None]]: chunk: bytes, total_bytes: int, content_length: int, speed: float
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if not response.status == 200:
                raise ApiError(
                    status_code=response.status,
                    message=f"Failed to download update: {response.reason}",
                )
            content_length = int(response.headers.get("Content-Length", 0))
            total_bytes = 0
            start_time: float | None = None

            async for chunk in response.content.iter_chunked(1024):
                if not start_time:
                    start_time = perf_counter()

                total_bytes += len(chunk)
                elapsed_time = perf_counter() - start_time
                speed = total_bytes / elapsed_time if elapsed_time else 0.0
                yield chunk, total_bytes, content_length, speed
