@echo off
chcp 65001 >nul
cd /d "%~dp0"
py -m pip install --upgrade pyinstaller
py -m PyInstaller --noconfirm --onefile --windowed --name "DisenoMelaminaCAD" melamina_sketchup.py
echo.
echo Ejecutable creado en dist\DisenoMelaminaCAD.exe si no hubo errores.
pause
