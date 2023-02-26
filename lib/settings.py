import os
import json
import logging
from uuid import uuid4, UUID

from pydantic import BaseModel, Field

from lib.config import APP_SETTINGS_PATH, APP_DOWNLOADS_PATH


_Log = logging.getLogger(__name__)


class UserData(BaseModel):
    email: str
    is_admin: bool
    is_user: bool
    date_created: float


class Auth(BaseModel):
    access_token: str
    token_type: str
    user: UserData


class Settings(BaseModel):
    download_path: str = APP_DOWNLOADS_PATH
    remove_files_after_install: bool = False
    close_dialog_after_install: bool = False
    download_only: bool = False
    uuid: UUID = Field(default_factory=uuid4)
    auth: Auth | None = None

    def remove_auth(self) -> bool:
        """Sets the auth property to None and saves to file

        Returns:
            bool: returns True if successful or False if no auth was removed
        """
        if self.auth is None:
            return False
        self.auth = None
        self.save()

    @property
    def token(self) -> str | None:
        """get the access_token

        Returns:
            str | None:
        """
        if isinstance(self.auth, Auth) and self.auth.access_token:
            return self.auth.access_token
        return None

    def get_user_email(self) -> str:
        """get the email address that is stored

        Returns:
            str:
        """
        try:
            return self.auth.user.email
        except AttributeError:
            return ""

    def is_user_admin(self) -> bool:
        """check if the user stored to settings is an admin
        even if the user changes this the api still requires an access token to authorize
        this function is used for disdabling controls to the user that is required for admin access
        like adding and removing game torrents to the database

        Returns:
            bool:
        """
        if isinstance(self.auth, Auth) and hasattr(self.auth.user, "is_admin"):
            return self.auth.user.is_admin
        return False

    def set_auth(self, auth: dict) -> None:
        """set the auth object to the settings auth property

        Args:
            auth (dict): stores as Auth class instance
        """
        self.auth = Auth(**auth)

    def set_download_path(self, path: str) -> None:
        """create the download path directory

        Args:
            path (str): the path to create
        """
        try:
            os.makedirs(path)
        except OSError:
            pass
        finally:
            self.download_path = path

    @staticmethod
    def load() -> "Settings":
        """load the settings.json and return a class instance of Settings

        Args:
            path (str, optional): _description_. Defaults to lib.config.APP_SETTINGS_PATH.

        Returns:
            Settings:
        """

        try:
            with open(APP_SETTINGS_PATH, "r") as fp:
                data = json.load(fp)
            settings = Settings(**data)
        except FileNotFoundError:
            settings = Settings()
        finally:
            _Log.info(f"Loaded UUID {settings.uuid}")
            return settings

    def save(self) -> None:
        """save the settings to path

        Args:
            path (str, optional): _description_. Defaults to lib.config.APP_SETTINGS_PATH.
        """

        with open(APP_SETTINGS_PATH, "w") as fp:
            text = self.json()
            fp.write(text)
            _Log.info(f"Saved UUID {self.uuid} to file")
