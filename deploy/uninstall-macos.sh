#!/bin/bash
# Logos News macOS 제거 스크립트
# 사용법: ./deploy/uninstall-macos.sh

set -e

APP_NAME="com.logosnews.agent"
APP_DIR="$HOME/logos_news"
PLIST_PATH="$HOME/Library/LaunchAgents/$APP_NAME.plist"

echo "=========================================="
echo "Logos News macOS 제거"
echo "=========================================="

read -p "정말로 제거하시겠습니까? (y/N): " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "취소됨"
    exit 0
fi

# LaunchAgent 중지 및 제거
echo "[1/2] LaunchAgent 제거"
if [ -f "$PLIST_PATH" ]; then
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    rm -f "$PLIST_PATH"
    echo "  LaunchAgent 제거됨"
else
    echo "  LaunchAgent 없음"
fi

# 파일 제거
echo "[2/2] 파일 제거"
read -p "앱 디렉토리($APP_DIR)도 제거하시겠습니까? (y/N): " remove_dir
if [[ "$remove_dir" == "y" || "$remove_dir" == "Y" ]]; then
    rm -rf "$APP_DIR"
    echo "  디렉토리 제거됨"
else
    echo "  디렉토리 유지됨"
fi

echo ""
echo "제거 완료!"
