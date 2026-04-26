@echo off
REM Sandy's Treedome Lab - Windows Startup Script

echo.
echo ========================================
echo Sandy's Treedome Lab - Startup
echo ========================================
echo.

REM Load .env file if it exists
if exist .env (
    echo Loading .env file...
    for /f "delims== tokens=1,2" %%A in (.env) do (
        set %%A=%%B
    )
) else (
    echo Warning: .env file not found. Copy .env.example to .env and fill in values.
    echo.
)

REM Check if virtual environment exists
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
    echo.
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -q -r requirements.txt
echo.

REM Determine mode
if "%1"=="prod" (
    echo Starting in PRODUCTION mode (gunicorn)...
    echo.
    gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
) else (
    echo Starting in DEVELOPMENT mode (with auto-reload)...
    echo Dashboard: http://localhost:8000/ui
    echo API Docs: http://localhost:8000/docs
    echo.
    python -m uvicorn main:app --reload
)
