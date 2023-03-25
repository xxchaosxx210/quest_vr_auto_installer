from time import perf_counter

import aiohttp
from typing import AsyncGenerator, Tuple

from api.exceptions import ApiError


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
