from typing import List

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
