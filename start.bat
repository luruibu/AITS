@echo off
echo   启动 AI Image Tree System...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo   Python 未安装或未添加到PATH
    echo   请先安装 Python 3.8+ 并添加到系统PATH
    pause
    exit /b 1
)

REM 检查配置文件
if not exist "config.json" (
    echo   配置文件不存在，运行安装脚本...
    python setup.py
    if errorlevel 1 (
        echo   安装失败
        pause
        exit /b 1
    )
)

REM 启动应用
echo   启动应用...
python app.py

pause