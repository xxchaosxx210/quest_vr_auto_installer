REM runs mypy without the missing imports
@ECHO OFF
cls
ECHO Checking Project Files...
mypy --ignore-missing-imports main.py