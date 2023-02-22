import base64

from pydantic import BaseModel
from uuid import UUID


class QuestMagnet(BaseModel):
    name: str
    display_name: str
    magnet: str
    version: float
    filesize: int
    date_added: float
    id: str

    @property
    def uri(self) -> str:
        return self.magnet

    @property
    def decoded_uri(self) -> str:
        try:
            uri = base64.b64decode(self.magnet).decode("utf-8")
        except TypeError:
            uri = self.magnet
        finally:
            return uri

    @property
    def encoded_uri(self) -> bytes:
        try:
            uri = base64.b64encode(self.magnet)
        except TypeError:
            uri = self.magnet
        finally:
            return uri


class QuestMagnetWithKey(QuestMagnet):
    key: str


class LogErrorRequest(BaseModel):
    type: str
    uuid: UUID
    exception: str
    traceback: str


class User(BaseModel):
    email: str
    date_created: float | None = None
    is_admin: bool = False
    is_user: bool = True
    disabled: bool | None = None


class ErrorLog(BaseModel):
    key: str
    type: str
    uuid: UUID
    exception: str
    traceback: str
    date_added: float
