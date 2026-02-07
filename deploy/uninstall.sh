#!/bin/bash
# Logos News 제거 스크립트
# 사용법: sudo ./deploy/uninstall.sh

set -e

APP_NAME="logos-news"
APP_USER="logos"
APP_DIR="/opt/logos_news"

echo "=========================================="
echo "Logos News 제거"
echo "=========================================="

read -p "정말로 제거하시겠습니까? (y/N): " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "취소됨"
    exit 0
fi

# 서비스 중지 및 제거
echo "[1/3] 서비스 제거"
systemctl stop "$APP_NAME" 2>/dev/null || true
systemctl disable "$APP_NAME" 2>/dev/null || true
rm -f "/etc/systemd/system/$APP_NAME.service"
systemctl daemon-reload

# 파일 제거
echo "[2/3] 파일 제거"
rm -rf "$APP_DIR"

# 사용자 제거
echo "[3/3] 사용자 제거"
read -p "사용자 '$APP_USER'도 제거하시겠습니까? (y/N): " remove_user
if [[ "$remove_user" == "y" || "$remove_user" == "Y" ]]; then
    userdel "$APP_USER" 2>/dev/null || true
fi

echo ""
echo "제거 완료!"
