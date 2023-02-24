from html.parser import HTMLParser
from typing import List, Tuple
import re

from aiohttp import ClientSession


class ParserConnectionError(Exception):
    def __init__(self, message: str, code: int, *args) -> None:
        super().__init__(*args)
        self.message = message
        self.code = code


MAG_LINK_PATTERN = re.compile(r"magnet:\?xt=urn:btih:\w+")


class MagnetParser(HTMLParser):
    def __init__(self, *, convert_charrefs: bool = True) -> None:
        super().__init__(convert_charrefs=convert_charrefs)

        self.magnet_urls: List[str] = []

    def handle_starttag(self, tag: str, attrs: Tuple) -> None:
        if tag == "a":
            for attr in attrs:
                if attr[0] == "href" and MAG_LINK_PATTERN.search(attr[1]):
                    self.magnet_urls.append(attr[1])

    @staticmethod
    async def get_html(uri: str, params: dict = {}, headers: dict = {}) -> str | None:
        async with ClientSession() as session:
            async with session.get(uri, params=params, headers=headers) as response:
                if "text/html" not in response.content_type:
                    raise ParserConnectionError(
                        "Response Content Type was not HTML unable to Parse the response"
                    )
                if response.status != 200:
                    response_text = await response.text()
                    raise ParserConnectionError(response_text, response.status)
                html = await response.text()
                return html
