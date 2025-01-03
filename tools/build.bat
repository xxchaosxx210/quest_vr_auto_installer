@REM This will build the python project into an exe package using pyinstaller
@echo off

rem Build executable
pyinstaller --clean ^
-n QuestCave ^
-w ^
--exclude-module pyinstaller --exclude-module pyflakes --exclude-module autopep8 --exclude-module black --exclude-module pyinstaller-hooks-contrib --exclude-module pylint --exclude-module pytest --exclude-module pytest-asyncio --exclude-module mypy ^
--add-data ".\adblib\win64;adblib\win64" ^
--add-data "images\*;images" ^
--add-data "deluge\bin\version-211\win64\;deluge\bin\version-211\win64" ^
--icon .\images\icon.ico ^
main.py
