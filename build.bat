@echo off

rem Build executable
pyinstaller --clean ^
-n QuestVRAutoInstaller ^
-w ^
--exclude=pyinstaller --exclude=pyflakes --exclude=autopep8 --exclude=black --exclude pyinstaller-hooks-contrib --exclude pylint ^
--add-data ".\adblib\win64;adblib\win64" ^
app.py
@REM --icon .\images\SPBackup_icon.ico app.py
