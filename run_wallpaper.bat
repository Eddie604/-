@echo off
chcp 65001 >nul
echo ========================================
echo   二次元壁纸生成器 - 自动运行
echo ========================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM ===== 关键修改1：检查本地Python =====
if not exist "python.exe" (
    echo ❌ 未找到python.exe
    echo 💡 请确保已解压正确的Python嵌入包
    echo    正确文件: python-3.11.4-embed-amd64.zip
    echo    必须包含: python.exe
    pause
    exit /b 1
)

REM ===== 关键修改2：使用本地Python =====
echo ✅ 检测到本地Python
set PYTHON="python.exe"

REM 检查依赖库
%PYTHON% -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo 📦 检测到缺少依赖库，正在安装...
    %PYTHON% -m pip install requests pillow
    if errorlevel 1 (
        echo ❌ 依赖库安装失败，请检查网络
        pause
        exit /b 1
    )
    echo ✅ 依赖库安装完成
)

REM 运行Python脚本
echo 🚀 正在运行壁纸生成器...
%PYTHON% "每日一句成品版.py"

echo.
echo ========================================
echo   执行完成！按任意键退出...
echo ========================================
pause >nul