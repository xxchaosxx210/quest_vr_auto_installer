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
        """
        Raises:
            err: Exception

        Returns:
            str: returns the decoded bas64 string otherwise the original magnet link if typeerror
        """
        try:
            uri = base64.b64decode(self.magnet).decode("utf-8")
        except TypeError:
            return self.magnet
        except Exception as err:
            raise err
        else:
            return uri

    @property
    def encoded_uri(self) -> str:
        """
        Raises:
            err: _description_

        Returns:
            str: encodes the uri back to base64 encoded string
        """
        try:
            # encode the decrpyted string back to bytes
            byte_string = self.magnet.encode("utf-8")
            # encode the encoded bytes back to base64 bytes
            byte_b64string = base64.b64encode(byte_string)
            # decode the base64 bytes back to a base64 readable str again
            uri = byte_b64string.decode("utf-8")
        except Exception as err:
            raise err
        else:
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
