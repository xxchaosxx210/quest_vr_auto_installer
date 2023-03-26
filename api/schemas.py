import base64
import traceback

from pydantic import BaseModel, validator
from pydantic.fields import ModelField
from uuid import UUID


class Game(BaseModel):
    name: str
    display_name: str
    magnet: str
    version: float
    filesize: int
    date_added: float
    id: str
    key: str

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


class AddGameRequest(Game):
    @validator("display_name")
    def check_for_non_empty_string(
        cls: "AddGameRequest",
        value: str,
        values: dict,
        config: object,
        field: ModelField,
    ) -> str:
        if not value:
            raise ValueError(f"{field.name} cannot be empty")
        return value


class LogErrorRequest(BaseModel):
    type: str
    uuid: UUID
    exception: str
    traceback: str

    @staticmethod
    def format_error(err: Exception, _uuid: UUID) -> "LogErrorRequest":
        """format the exception into a LogErrorRequest

        Args:
            err (Exception): the exception that was raised and handled
            _uuid (UUID): the UUID of the user that raised the exception. This will be used to identify the user in the logs. Will change when user accounts impemented

        Returns:
            LogErrorRequest: the formatted log error request
        """
        if hasattr(err, "args"):
            exception = "".join(err.args)
        elif hasattr(err, "message"):
            exception = err.message
        else:
            exception = str(err)
        tb_string = "\n".join(traceback.format_exception(err))
        error_request = LogErrorRequest(
            type=str(err), uuid=_uuid, exception=exception, traceback=tb_string
        )
        return error_request


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


class AppVersionResponse(BaseModel):
    version: str
    url: str
    mirror_url: str
    description: str
