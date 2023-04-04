REM Runs mypy without the missing imports. Put this in your Project Folder
@ECHO OFF
cls
ECHO Checking Project Files...
mypy --ignore-missing-imports main.py