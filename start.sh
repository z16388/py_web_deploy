#!/usr/bin/env bash
# py_web_deploy 启动脚本（Linux / macOS）

PORT=${1:-8888}

echo "==> 启动交付服务，端口: $PORT"
echo "==> 访问地址: http://0.0.0.0:$PORT/"
echo "==> 包装根目录: $(pwd)/deploy/"
echo "==> 按 Ctrl+C 停止服务"
echo ""

python3 deploy.py "$PORT"
