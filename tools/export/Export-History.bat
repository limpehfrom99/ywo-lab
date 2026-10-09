@echo off
cd /d "%~dp0"
title YWO price export
where py >nul 2>nul
if errorlevel 1 (
  echo Python is not installed on this PC.
  echo Fix: double-click Setup.bat in your lab folder, or install Python 3.12 from python.org with "Add python.exe to PATH" ticked.
  pause
  exit /b 1
)
py -3 -c "import MetaTrader5, numpy" >nul 2>nul
if errorlevel 1 (
  echo Installing the MetaTrader5 and numpy packages, one moment...
  py -3 -m pip install --quiet MetaTrader5 numpy
)
py -3 export_history.py %*
if errorlevel 1 pause
