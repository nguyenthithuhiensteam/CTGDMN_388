@echo off
cd /d "%~dp0"

set "PYTHON_CMD=python"
python --version >nul 2>&1
if errorlevel 1 (
    set "PYTHON_CMD=py"
    py --version >nul 2>&1
    if errorlevel 1 (
        echo Khong tim thay Python. Vui long cai Python 3.11+ roi chay lai.
        pause
        exit /b 1
    )
)

%PYTHON_CMD% -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo Dang cai thu vien backend tu requirements.txt ...
    %PYTHON_CMD% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Cai thu vien that bai. Vui long kiem tra Python/pip/mang Internet.
        pause
        exit /b 1
    )
)

%PYTHON_CMD% -m backend.init_db
%PYTHON_CMD% -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
