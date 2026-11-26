@echo off
chcp 65001 >nul
setlocal

set ROOT_DIR=%~dp0

echo [1/4] 檢查與建立 Python 後端虛擬環境...
cd /d "%ROOT_DIR%backend"

:: 若舊的 .venv 裡沒有裝好 uvicorn，先清理掉避免卡住
if exist ".venv" (
    .venv\Scripts\python.exe -c "import uvicorn, fastapi, playwright" >nul 2>nul
    if %errorlevel% neq 0 (
        echo 偵測到先前虛擬環境未完整安裝，正在重置 .venv...
        rmdir /s /q .venv
    )
)

if not exist ".venv\Scripts\python.exe" (
    set PY_CMD=
    for %%V in (3.12 3.11 3.13 3.10) do (
        if not defined PY_CMD (
            py -%%V --version >nul 2>nul
            if not errorlevel 1 set PY_CMD=py -%%V
        )
    )
    if not defined PY_CMD (
        where python >nul 2>nul
        if not errorlevel 1 set PY_CMD=python
    )
    if not defined PY_CMD (
        echo [錯誤] 找不到 Python 3.10~3.13！請先安裝 Python 3.12 ^(64-bit^)。
        pause
        exit /b 1
    )

    echo 使用 %PY_CMD% 建立虛擬環境...
    %PY_CMD% -m venv .venv
    .venv\Scripts\python.exe --version
    .venv\Scripts\python.exe -m pip install --upgrade pip
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [錯誤] Python 套件安裝失敗！
        echo 原因：您目前的 Python 版本過新 ^(例如 3.14^) 或為 32 位元，缺少預編譯套件。
        echo 解法：請在 CMD 執行 winget install Python.Python.3.12 安裝 Python 3.12 后，再重跑 start.bat！
        rmdir /s /q .venv
        pause
        exit /b 1
    )
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
