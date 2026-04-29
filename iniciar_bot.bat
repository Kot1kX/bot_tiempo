@echo off
title Bot Tiempo
cd /d "%~dp0"

call C:\Users\Kot1kX\venv_tiempo\Scripts\activate.bat

echo Iniciando bot del tiempo...
python bot.py

pause