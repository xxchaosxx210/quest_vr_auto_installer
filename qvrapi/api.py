"""connecting to the magnet database API
"""

import logging
import base64
from typing import List
from urllib.parse import urljoin

import aiohttp

from qvrapi.schemas import QuestMagnet, LogErrorRequest, User


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


URI_LOCAL_HOST = "http://127.0.0.1:8000"
URI_DETA_MICRO = "https://6vppvi.deta.dev"

# change this to one of the above hosts
URI_HOST = URI_LOCAL_HOST

URI_GAMES = urljoin(URI_HOST, "/games")
URI_USERS = urljoin(URI_HOST, "/users")
URI_LOGS = urljoin(URI_HOST, "/logs")
URI_USERS_LOGIN = URI_USERS + "/token"
URI_USER_INFO = URI_USERS + "/info"


def get_account_type(user: User) -> str:
    """determines the account type as a string

    Args:
        user (User):

    Returns:
        str:
    """
    if user.is_admin:
        t = "Administrator"
    if not user.is_admin and user.is_user:
        t = "User"
    return t


def create_auth_token_header(token: str) -> dict:
    """

    Args:
        token (str): the authenticating token to add

    Returns:
        dict: returns the constructed Authorization header dict
    """
    return {"Authorization": f"Bearer {token}"}


async def get_game_magnets(url: str = URI_GAMES) -> List[QuestMagnet]:
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


async def post_error(error_request: LogErrorRequest) -> bool:
    """post an error log to the database

    Args:
        url (str): the logs endpoint
        error_request (LogErrorRequest):

    Raises:
        ApiError: if status is not 200

    Returns:
        bool: True if entry added
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(
            URI_LOGS,
            data=error_request.json(),
            headers={"Content-Type": "application/json"},
        ) as response:
            if response.status != 200:
                error_response = await response.content.read()
                raise ApiError(error_response)
            return True


async def login(email: str, password: str) -> dict:
    """login into the API

    Args:
        email (str): User email address
        password (str): User password

    Raises:
        ApiError: if status not 200

    Returns:
        dict: keys contain the access_token: str, token_type: str, and the user: User
    """
    async with aiohttp.ClientSession() as session:
        frm_data = aiohttp.FormData()
        frm_data.add_field("username", email)
        frm_data.add_field("password", password)
        async with session.post(URI_USERS_LOGIN, data=frm_data) as response:
            if response.status != 200:
                err_message = await response.json()["detail"]
                raise ApiError(status_code=response.status, message=err_message)
            resp_json = await response.json()
            return resp_json


async def get_user_info(token: str) -> User:
    headers = create_auth_token_header(token)
    headers["Content-Type"] = "application/json"
    async with aiohttp.ClientSession() as session:
        async with session.get(URI_USER_INFO, headers=headers) as response:
            if response.status != 200:
                error_data = await response.json()
                raise ApiError(
                    status_code=response.status, message=error_data["detail"]
                )
            data = await response.json()
            user = User(**data)
            return user
