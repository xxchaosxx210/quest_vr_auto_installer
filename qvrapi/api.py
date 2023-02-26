"""connecting to the magnet database API
"""

import logging
from typing import Any, Dict, Iterator, List
from urllib.parse import urljoin
from enum import Enum, auto as auto_enum

import aiohttp

import qvrapi.schemas as schemas


_Log = logging.getLogger(__name__)


class RequestType(Enum):
    GET = auto_enum()
    POST = auto_enum()
    DELETE = auto_enum()
    PUT = auto_enum()


class ApiError(Exception):
    """basic API error

    Args:
        Exception (_type_): status_code and message
    """

    def __init__(self, status_code: int, message: str, *args: object) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(*args)

    def __str__(self) -> str:
        return f"{self.message}. Status Code: {self.status_code}"


URI_LOCAL_HOST = "http://127.0.0.1:8000"
URI_DETA_MICRO = "https://6vppvi.deta.dev"

# change this to one of the above hosts
URI_HOST = URI_LOCAL_HOST

URI_GAMES = urljoin(URI_HOST, "/games")
URI_SEARCH_GAME = URI_GAMES + "/search"
URI_UPDATE_GAME = URI_GAMES + "/update"
URI_USERS = urljoin(URI_HOST, "/users")
URI_LOGS = urljoin(URI_HOST, "/logs")
URI_USERS_LOGIN = URI_USERS + "/token"
URI_USER_INFO = URI_USERS + "/info"


def get_account_type(user: schemas.User) -> str:
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


async def get_game_magnets() -> List[schemas.QuestMagnet]:
    """gets the Quest 2 magnet links from the q2g server

    Raises:
        ApiError:
        aiohttp.ClientConnectionError:
        TypeError:

    Returns:
        List[QuestMagnet]: list of magnet objects
    """
    try:
        response_data = await send_json_request(URI_GAMES)
        if not isinstance(response_data, list):
            raise TypeError("Returned value was of not type List")
        magnets = list(
            map(lambda magnet_dict: schemas.QuestMagnet(**magnet_dict), response_data)
        )
        return magnets
    except Exception as err:
        raise err


async def search_for_games(
    token: str, params: dict
) -> List[schemas.QuestMagnetWithKey]:
    """get the game including the key this is for admin use updating and deleting etc.

    Args:
        token (str): admin token
        params (dict): look at QuestMagnet class in qvrapi.schemas for query names to add in search

    Raises:
        err: Exception

    Returns:
        list: [schemas.QuestMagnetWithKey]
    """
    try:
        data = await send_json_request(uri=URI_SEARCH_GAME, token=token, _json=params)
        if not isinstance(data, list):
            raise TypeError("data returned from game search is not a list")
        games = list(map(lambda game: schemas.QuestMagnetWithKey(**game), data))
        return games
    except Exception as err:
        raise err


async def update_game_magnet(
    token: str, key: str, params: dict
) -> schemas.QuestMagnetWithKey:
    try:
        uri = URI_UPDATE_GAME + f"/{key}"
        data = await send_json_request(
            uri, token, _json=params, request_type=RequestType.PUT
        )
        gamewithkey = schemas.QuestMagnetWithKey(**data)
        return gamewithkey
    except Exception as err:
        raise err


async def post_error(error_request: schemas.LogErrorRequest) -> bool:
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
                error_response = await response.text()
                raise ApiError(status_code=response.status, message=error_response)
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
                err_message = await response.json()
                raise ApiError(
                    status_code=response.status, message=err_message["detail"]
                )
            resp_json = await response.json()
            return resp_json


async def get_user_info(token: str) -> schemas.User:
    """get the user information using the token

    Args:
        token (str):

    Raises:
        err: Exception

    Returns:
        User: the user information
    """
    try:
        data = await send_json_request(URI_USER_INFO, token=token, params={})
        user = schemas.User(**data)
        return user
    except Exception as err:
        raise err


async def get_logs(token: str, params: dict = {}) -> Iterator:
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

    try:
        data = await send_json_request(URI_LOGS, token=token, params=params)
        err_logs = map(lambda _log: schemas.ErrorLog(**_log), data["logs"])
        return err_logs
    except Exception as err:
        _Log.error(err.__str__())
        raise err


async def delete_logs(token: str, key: str) -> List[schemas.ErrorLog]:
    headers = create_auth_token_header(token=token)
    headers["Content-Type"] = "application/json"
    params = {"key": key}
    async with aiohttp.ClientSession() as session:
        async with session.delete(URI_LOGS, params=params, headers=headers) as response:
            if response.content_type == "text/plain":
                byte_error_response = await response.content.read()
                raise ApiError(
                    status_code=response.status,
                    message=byte_error_response.decode("utf-8"),
                )
            if response.status != 200:
                json_error_data: Dict[str, str] = await response.json()
                raise ApiError(
                    status_code=response.status, message=json_error_data["detail"]
                )
            json_data: Dict[str, Any] = await response.json()
            error_logs = list(
                map(lambda _log_dict: schemas.ErrorLog(**_log_dict), json_data["logs"])
            )
            return error_logs


async def send_json_request(
    uri: str,
    token: str | None = None,
    params: dict = {},
    _json: dict = {},
    request_type: RequestType = RequestType.GET,
    timeout: float = 5.0,
) -> dict:
    """abstract function for connecting and handling json api requests and responses

    Args:
        uri (str): the endpoint to connect to
        token (str | None, optional): the JWT token to auth None of no oauth required. Defaults to None.
        params (dict, optional): query. Defaults to {}.
        _json (dict, optional): json query. Defaults to {}.
        request_type (RequestType, optional): check the RequestType Enum class for details. Defaults to RequestType.GET.
        timeout (float, optional): timeout until the connection drops. Defaults to 5.0.

    Raises:
        TypeError: if the RequestType Enum is not found
        ApiError: if return code is not 200
        ApiError: if the content type is not a json response

    Returns:
        dict: json object
    """
    if token is None:
        headers = {}
    else:
        headers = create_auth_token_header(token=token)
    headers["Content-Type"] = "application/json"
    timeout_total = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=timeout_total) as session:
        # find out what request is being sent
        if request_type == RequestType.GET:
            request_ctxmgr = session.get
        elif request_type == RequestType.POST:
            request_ctxmgr = session.post
        elif request_type == RequestType.DELETE:
            request_ctxmgr = session.delete
        elif request_type == RequestType.PUT:
            request_ctxmgr = session.put
        else:
            raise TypeError("RequestType is unknown")

        async with request_ctxmgr(
            url=uri, params=params, headers=headers, json=_json
        ) as response:
            if response.content_type != "application/json":
                bytes_error_resp = await response.content.read()
                raise ApiError(
                    status_code=response.status,
                    message=bytes_error_resp.decode("utf-8"),
                )
            if response.status != 200:
                json_error_data: Dict[str, str] = await response.json()
                raise ApiError(
                    status_code=response.status, message=json_error_data["detail"]
                )
            json_data: Dict[str, Any] = await response.json()
            return json_data
