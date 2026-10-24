@echo off
REM Start the Campus Regulations Assistant (backend API + webpage) on Windows.
REM serve.py serves both POST /ask and campus_assistant_frontend-logo.html at http://localhost:8000
cd /d "%~dp0"

REM --- First run: create the virtual environment and install dependencies ---
if not exist ".venv\" (
  echo Creating virtual environment and installing dependencies ^(first run, a few minutes^)...
  python -m venv .venv || goto :error
  call ".venv\Scripts\activate.bat"
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt || goto :error
) else (
  call ".venv\Scripts\activate.bat"
)

REM --- Note if no API key: the app still runs, in demo mode ---
if not exist ".env" echo [note] No .env found - running in demo mode. Copy .env.example to .env and add GOOGLE_API_KEY for real answers.

REM --- Open the page once the server has had time to load the model ---
start "" cmd /c "timeout /t 25 >nul & start """" http://localhost:8000"

REM --- Run the server (Ctrl+C to stop). First launch downloads the embedding model. ---
echo Starting server on http://localhost:8000  (Ctrl+C to stop)
python serve.py
goto :eof

:error
echo.
echo Setup failed. Make sure Python 3 is installed and on your PATH.
pause
