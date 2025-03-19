@echo off
echo Setting up virtual environment...

@REM IF EXIST venv (
@REM     echo Removing old virtual environment...
@REM     rmdir /s /q venv
@REM )

echo Creating fresh virtual environment...
python -m venv venv

call venv\Scripts\activate.bat

@REM echo Installing dependencies...
@REM pip install -r requirements.txt

echo Starting the local server...
python local_server.py

echo Server stopped. 