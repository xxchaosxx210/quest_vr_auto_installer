"""Url paths for the API Backend"""

from urllib.parse import urljoin


import api.utils


URI_LOCAL_HOST = "http://127.0.0.1:8000"
URI_DETA_MICRO = "https://6vppvi.deta.dev"

# change this to one of the above hosts
if api.utils.test_host(URI_LOCAL_HOST):
    URI_HOST = URI_LOCAL_HOST
else:
    URI_HOST = URI_DETA_MICRO

URI_GAMES = urljoin(URI_HOST, "/games")
URI_SEARCH_GAME = URI_GAMES + "/search"
URI_UPDATE_GAME = URI_GAMES + "/update"
URI_DELETE_GAME = URI_GAMES
URI_ADD_GAME = URI_GAMES + "/add"
URI_USERS = urljoin(URI_HOST, "/users")
URI_LOGS = urljoin(URI_HOST, "/logs")
URI_USERS_LOGIN = URI_USERS + "/token"
URI_USER_INFO = URI_USERS + "/info"

# Website Urls
URI_INDEX = URI_HOST + "/index"
URI_HELP = URI_HOST + "/help"

# APP Version
URI_APP_DETAILS = URI_HOST + "/app-details"
