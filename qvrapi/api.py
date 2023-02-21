"""connecting to the magnet database API
"""

import logging
import base64
from typing import List
from urllib.parse import urljoin

import aiohttp

from qvrapi.schemas import QuestMagnet, LogErrorRequest, User, ErrorLog


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

    try:
        data = await get_json_response(URI_GAMES)
        games = data.get("games", [])
        if not games:
            raise ValueError("No games exist")
        magnets = list(map(process_magnet_dict, games))
        return magnets
    except Exception as err:
        raise err


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
    """get the user information using the token

    Args:
        token (str):

    Raises:
        err: Exception

    Returns:
        User: the user information
    """
    try:
        data = await get_json_response(URI_USER_INFO, token=token, params={})
        user = User(**data)
        return user
    except Exception as err:
        raise err


async def get_logs(token: str, params: dict = None) -> List[ErrorLog]:
    """gets the error logs from the api server

    Args:
        token (str): must be admin
        params (dict, optional): params can contain
            sort_by: str = "date_added",
            order_by: str = "asc" | "desc",
            limit: int = 1000

    Returns:
        List: returns a list of ErrorLog
    """

    def log_handler(_log: dict):
        _error_log = ErrorLog(**_log)
        return _error_log

    try:
        data = await get_json_response(URI_LOGS, token=token, params=params)
        err_logs = list(map(log_handler, data["logs"]))
        return err_logs
    except Exception as err:
        raise err


async def get_json_response(uri: str, token: str = None, params: dict = {}) -> dict:
    if not token:
        headers = {}
    else:
        headers = create_auth_token_header(token=token)
    headers["Content-Type"] = "application/json"
    async with aiohttp.ClientSession() as session:
        async with session.get(uri, params=params, headers=headers) as response:
            if response.content_type != "application/json":
                data = await response.content.read()
                raise ApiError(
                    status_code=response.status, message=data.decode("utf-8")
                )
            if response.status != 200:
                error_message = await response.json()
                raise ApiError(
                    status_code=response.status, message=error_message["detail"]
                )
            data = await response.json()
            return data
