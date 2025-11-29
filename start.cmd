@echo off
setlocal
set BASE=%~dp0
set PY=%BASE%python\python.exe
set APP=%BASE%app.py
set REQ=%BASE%requirements.txt

if not exist "%PY%" (
  echo [GeoPic] Portable Python not found at %PY%
  echo [GeoPic] Download Windows embeddable Python and unzip into: %BASE%python\
  echo [GeoPic] https://www.python.org/downloads/windows/
  pause
  exit /b 1
)

echo [GeoPic] Installing dependencies (first run only)...
"%PY%" -m pip install --upgrade pip
"%PY%" -m pip install -r "%REQ%"
if errorlevel 1 (
  echo [GeoPic] Dependency install failed.
  pause
  exit /b 1
)

echo [GeoPic] Starting server at http://127.0.0.1:5000
"%PY%" "%APP%"
endlocal
