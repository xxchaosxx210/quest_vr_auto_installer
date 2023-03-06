from urllib.parse import urljoin


URI_LOCAL_HOST = "http://127.0.0.1:8000"
URI_DETA_MICRO = "https://6vppvi.deta.dev"

# change this to one of the above hosts
URI_HOST = URI_LOCAL_HOST
# URI_HOST = URI_DETA_MICRO

URI_GAMES = urljoin(URI_HOST, "/games")
URI_SEARCH_GAME = URI_GAMES + "/search"
URI_UPDATE_GAME = URI_GAMES + "/update"
URI_ADD_GAME = URI_GAMES + "/add"
URI_USERS = urljoin(URI_HOST, "/users")
URI_LOGS = urljoin(URI_HOST, "/logs")
URI_USERS_LOGIN = URI_USERS + "/token"
URI_USER_INFO = URI_USERS + "/info"
