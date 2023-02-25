from typing import List

import aiohttp

import qvrapi.api as api
import qvrapi.schemas as schemas


async def get_magnets_from_torrent_id(
    token: str, torrent_id: str, exception_handler: callable
) -> List[schemas.QuestMagnet]:
    """gets the magnet using the torrent id and handles any exceptions

    Args:
        token (str): must be admin JWT
        torrent_id (str): torrent id to match in database

    Returns:
        List[QuestMagnet]: returns a list of magnets found
    """
    try:
        magnets = await api.search_for_games(token, params={"id": torrent_id})
    except (api.ApiError, aiohttp.ClientConnectionError) as err:
        exception_handler(err.__str__())
        return None
    else:
        return magnets
