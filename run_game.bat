@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe ite184_study_game\pygame_main.py
) else (
    py ite184_study_game\pygame_main.py
)
if errorlevel 1 pause
