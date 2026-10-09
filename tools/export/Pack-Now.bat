@echo off
cd /d "%~dp0"
py -3 pack_now.py
if errorlevel 1 pause
