"""connecting to the magnet database API
"""

import logging
from typing import List

import aiohttp

from schemas import QuestMagnet

_Log = logging.getLogger(__name__)


class ApiError(Exception):
    """basic API error

    Args:
        Exception (_type_): status_code and message
    """

    def __init__(self, status_code: int, message: str, *args: object) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(*args)


MAGNET_ENDPOINT = "http://localhost:8000/games"


async def get_game_magnets(url: str = MAGNET_ENDPOINT) -> List[QuestMagnet]:
    """gets the Quest 2 magnet links from the q2g server

    Args:
        url (str, optional): change the endpoint when migrating online. Defaults to MAGNET_ENDPOINT.

    Raises:
        ApiError:

    Returns:
        List[QuestAppMagnet]: list of magnet objects
    """
    magnets: List[QuestMagnet] = []
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data_response = await response.json()
            if not isinstance(data_response, dict):
                error_message = "JSON Response from API was of not type dict"
                _Log.error(error_message)
                raise TypeError(error_message)
            if response.status != 200:
                raise ApiError(
                    status_code=response.status,
                    message=str(data_response.get("detail", "")),
                )
            games = data_response.get("games", [])
            if list(games) == 0:
                raise ValueError("No games exist")
            magnets = list(map(lambda magnet_dict: QuestMagnet(**magnet_dict), games))
    return magnets
