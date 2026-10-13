@echo off
cd /d "%~dp0"
py -3 -m pip install -r requirements.txt pyinstaller
py -3 -m PyInstaller --noconfirm --onefile --windowed --name CosmeticTo3DCreator app.py
pause
