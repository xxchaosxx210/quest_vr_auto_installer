from typing import Callable, List

import aiohttp

import qvrapi.api as api
import qvrapi.schemas as schemas


async def get_magnets_from_torrent_id(
    token: str, torrent_id: str, exception_handler: Callable[[str], None]
) -> List[schemas.QuestMagnetWithKey]:
    """gets the magnet using the torrent id and handles any exceptions

    Args:
        token (str): must be admin JWT
        torrent_id (str): torrent id to match in database

    Returns:
        List[QuestMagnetWithKey]: returns a list of magnets found
    """
    try:
        magnets = await api.search_for_games(token, params={"id": torrent_id})
    except (api.ApiError, aiohttp.ClientConnectionError) as err:
        exception_handler(err.__str__())
        return []
    else:
        return magnets
