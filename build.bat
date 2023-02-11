@echo off

rem Build executable
pyinstaller --clean ^
-n QuestVRAutoInstaller ^
-w ^
--exclude=pyinstaller --exclude=pyflakes --exclude=autopep8 --exclude=black --exclude pyinstaller-hooks-contrib --exclude pylint --exclude pytest --exclude pytest-asyncio ^
--add-data ".\adblib\win64;adblib\win64" ^
--add-data "images\*;images" ^
--add-data "deluge\bin\version-211\win64\;deluge\bin\version-211\win64" ^
--icon .\images\icon.ico ^
app.py
