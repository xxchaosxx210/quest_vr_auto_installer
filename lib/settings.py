import os
import json
import logging
from uuid import uuid4, UUID

from pydantic import BaseModel, Field

from lib.config import APP_SETTINGS_PATH, APP_DOWNLOADS_PATH


_Log = logging.getLogger(__name__)


class Settings(BaseModel):
    download_path: str = APP_DOWNLOADS_PATH
    remove_files_after_install: bool = False
    close_dialog_after_install: bool = False
    download_only: bool = False
    uuid: UUID = Field(default_factory=uuid4)
    token: str = ""

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
