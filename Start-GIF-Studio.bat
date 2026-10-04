@echo off
setlocal
cd /d "%~dp0"
if exist .venv\ready-v0.6.1.txt goto run
if exist .venv\Scripts\python.exe goto install
py -3 -m venv .venv
if errorlevel 1 goto fail
:install
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
echo ready > .venv\ready-v0.6.1.txt
:run
.venv\Scripts\python.exe app.py
if errorlevel 1 goto fail
exit /b 0
:fail
echo Setup or launch failed. Install Python 3.11 or newer from python.org with the Python launcher, then try again.
pause
exit /b 1
