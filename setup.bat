@echo off
chcp 65001 >nul
echo.
echo === py_web_deploy 环境搭建脚本（Windows） ===
echo.
echo [1/3] 检查 Python 版本...
python --version
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8 或更高版本
    pause
    exit /b 1
)
echo [2/3] 安装依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo 错误: 依赖安装失败，请检查 pip 是否可用
    pause
    exit /b 1
)
echo [3/3] 创建默认目录...
if not exist "deploy\android" mkdir "deploy\android"
if not exist "config" mkdir "config"
if not exist "sessions" mkdir "sessions"
echo.
echo 环境搭建完成！
echo.
echo 使用方式：
echo   1. 将 .apk / .aab / .obb / .ipa / .hap 文件放入 deploy\^<目录名^>\ 下
echo   2. 可选：编辑 config\dir_passwords.json 设置目录密码
echo   3. 运行: python deploy.py ^<端口号^>
echo   4. 访问: http://0.0.0.0:^<端口号^>/
echo.
echo 示例（端口 8888）：
echo   python deploy.py 8888
echo.
pause
