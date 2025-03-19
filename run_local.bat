@echo off
echo Setting up virtual environment...

@REM Use these lines to reset the venv if needed
@REM IF EXIST venv (
@REM     echo Removing old virtual environment...
@REM     rmdir /s /q venv
@REM )

IF NOT EXIST venv (
    echo Creating fresh virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo Starting the local server...
python local_server.py

echo Server stopped. 