@echo off
py -3.13 -c "" >nul 2>&1
if errorlevel 1 (
    echo Python 3.13 not found via the "py" launcher.
    echo Falling back to "python" on PATH - make sure it resolves to 3.11, 3.12, or 3.13.
    python main.py
) else (
    py -3.13 main.py
)
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Failed to start. Make sure Python 3.11-3.13 is installed with:
    echo   pip install pygame pymunk
    pause
)
