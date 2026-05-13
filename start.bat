@echo off
chcp 65001 >nul

set PORT=8888
if not "%~1"=="" set PORT=%~1

echo.
echo === py_web_deploy 交付服务 ===
echo 端口: %PORT%
echo 访问地址: http://0.0.0.0:%PORT%/
echo 包装目录: %~dp0deploy\
echo 按 Ctrl+C 停止服务
echo.

python deploy.py %PORT%

if errorlevel 1 (
    echo.
    echo 启动失败，请检查：
    echo   1. 是否已运行 setup.bat 安装依赖
    echo   2. 端口 %PORT% 是否被占用
    echo.
    pause
)

