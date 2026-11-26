@echo off
chcp 65001 >nul
setlocal

set ROOT_DIR=%~dp0

echo [1/4] 檢查與建立 Python 後端虛擬環境...
cd /d "%ROOT_DIR%backend"

if not exist ".venv\Scripts\uvicorn.exe" (
    where py >nul 2>nul
    if %errorlevel%==0 (
        set PY_CMD=py -3
    ) else (
        set PY_CMD=python
    )
    echo 使用 %PY_CMD% 建立虛擬環境與安裝套件，請稍候...
    %PY_CMD% -m venv .venv
    if not exist ".venv\Scripts\python.exe" (
        echo [錯誤] 找不到 Python 3！請先安裝 Python 3.10+ 並勾選 Add Python to PATH。
        pause
        exit /b 1
    )
    .venv\Scripts\python.exe -m pip install --upgrade pip
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    .venv\Scripts\playwright.exe install chromium
)

echo [2/4] 檢查與安裝前端套件...
cd /d "%ROOT_DIR%frontend"
if not exist "node_modules" (
    call npm install
)

echo [3/4] 啟動 FastAPI 後端 (Port 8000)...
start "Teacher-Manage Backend" cmd /k "cd /d "%ROOT_DIR%backend" && .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [4/4] 啟動 Next.js 前端 (Port 3000)...
start "Teacher-Manage Frontend" cmd /k "cd /d "%ROOT_DIR%frontend" && npm run dev -- -p 3000"

echo.
echo ======================================================
echo 系統啟動中！請稍候幾秒後於瀏覽器開啟：
echo   前端介面：http://localhost:3000
echo   API 文件：http://localhost:8000/docs
echo.
echo 預設測試帳號：
echo   管理員：admin / admin123
echo   講師  ：teacher_lin / teacher123
echo ======================================================
pause
