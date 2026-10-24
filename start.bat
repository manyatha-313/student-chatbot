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

REM --- Open the page only once the server actually responds (it embeds the
REM     documents before it starts listening; the first run also downloads the model) ---
start "" powershell -NoProfile -WindowStyle Hidden -Command "for($i=0;$i -lt 150;$i++){try{$null=Invoke-WebRequest -UseBasicParsing http://localhost:8000 -TimeoutSec 2;Start-Process 'http://localhost:8000';break}catch{Start-Sleep -Seconds 2}}"

REM --- Run the server (Ctrl+C to stop). ---
echo Starting server... the browser opens automatically when it is ready (http://localhost:8000, Ctrl+C to stop)
python serve.py
goto :eof

:error
echo.
echo Setup failed. Make sure Python 3 is installed and on your PATH.
pause
