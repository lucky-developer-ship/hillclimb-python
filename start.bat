@echo off
REM Use Python 3.13 (installed via winget) if available
set "PY313=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"

if exist "%PY313%" (
    "%PY313%" main.py
) else (
    echo Python 3.13 not found at the expected winget install path.
    echo Falling back to "python" on PATH - make sure it resolves to 3.11, 3.12, or 3.13.
    echo Note: Python 3.14+ is not yet supported by pygame.
    python main.py
)

pause
