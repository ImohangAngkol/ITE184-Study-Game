@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -B -m unittest discover -s ite184_study_game\tests -v
) else (
    py -B -m unittest discover -s ite184_study_game\tests -v
)
set "test_result=%errorlevel%"
pause
exit /b %test_result%
