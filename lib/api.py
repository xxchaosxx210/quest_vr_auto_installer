"""connecting to the magnet database API
"""

import logging
from typing import List
import base64
import functools
import aiohttp

from lib.schemas import QuestMagnet

from lib.config import (
    QUEST_MAGNETS_PATH,
    save_local_quest_magnets,
    load_local_quest_magnets,
)

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
# MAGNET_ENDPOINT = "https://6vppvi.deta.dev/games"


def catch_connection_error(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            _Log.info("Online: Saving Magnets to Local Database")
            save_local_quest_magnets(QUEST_MAGNETS_PATH, result)
            return result
        except aiohttp.ClientConnectionError:
            _Log.warning("Offline: Loading Magnets from Local Database")
            return load_local_quest_magnets(QUEST_MAGNETS_PATH)

    return wrapper


@catch_connection_error
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
            if response.content_type != "application/json":
                text_response = await response.read()
                raise ApiError(response.status, text_response.decode("utf-8"))
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

            def process_magnet_dict(magnet_dict: dict) -> QuestMagnet:
                """valid response json and decode base64 magnet link and return

                Args:
                    magnet_dict (dict): response json

                Returns:
                    QuestMagnet: _description_
                """
                magnet = QuestMagnet(**magnet_dict)
                bstring = base64.b64decode(magnet.uri)
                magnet.magnet = bstring.decode("utf-8")
                return magnet

            magnets = list(map(process_magnet_dict, games))
    return magnets