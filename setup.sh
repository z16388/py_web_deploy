#!/usr/bin/env bash
# py_web_deploy 环境搭建脚本（Linux / macOS）

set -e

echo "==> 检查 Python 版本..."
python3 --version

echo "==> 安装依赖..."
pip3 install -r requirements.txt

echo "==> 创建 APK 存放目录..."
mkdir -p deploy/android

echo ""
echo "✓ 环境搭建完成！"
echo ""
echo "使用方式："
echo "  1. 将 .apk 文件复制到 deploy/android/ 目录"
echo "  2. 运行: python3 deploy.py <端口号>"
echo "  3. 访问: http://0.0.0.0:<端口号>/"
echo ""
echo "示例（端口 8888）："
echo "  python3 deploy.py 8888"
