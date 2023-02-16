import os
import json

from pydantic import BaseModel

from config import APP_DOWNLOADS_PATH, APP_SETTINGS_PATH


class Settings(BaseModel):
    download_path: str = APP_DOWNLOADS_PATH
    remove_files_after_install: bool = False
    close_dialog_after_install: bool = False
    download_only: bool = False

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
    def load(path: str = APP_SETTINGS_PATH) -> "Settings":
        """load the settings.json and return a class instance of Settings

        Args:
            path (str, optional): _description_. Defaults to APP_SETTINGS_PATH.

        Returns:
            Settings:
        """
        try:
            with open(path, "r") as fp:
                data = json.load(fp)
            settings = Settings(**data)
            return settings
        except FileNotFoundError:
            settings = Settings()
            return settings

    def save(self, path: str = APP_SETTINGS_PATH) -> None:
        """save the settings to path

        Args:
            path (str, optional): _description_. Defaults to APP_SETTINGS_PATH.
        """
        with open(path, "w") as fp:
            text = self.json()
            fp.write(text)
