#!/bin/bash
# Logos News 설치 스크립트
# 사용법: sudo ./deploy/install.sh

set -e

# 설정
APP_NAME="logos-news"
APP_USER="logos"
APP_DIR="/opt/logos_news"
PYTHON_VERSION="python3.12"

echo "=========================================="
echo "Logos News 설치 시작"
echo "=========================================="

# 사용자 생성
if ! id "$APP_USER" &>/dev/null; then
    echo "[1/6] 사용자 생성: $APP_USER"
    useradd -r -m -d "$APP_DIR" -s /bin/false "$APP_USER"
else
    echo "[1/6] 사용자 이미 존재: $APP_USER"
fi

# 디렉토리 생성
echo "[2/6] 디렉토리 설정"
mkdir -p "$APP_DIR"/{config,logs}
cp -r src requirements.txt "$APP_DIR/"
cp config/config.example.yaml "$APP_DIR/config/"

# 가상환경 설정
echo "[3/6] Python 가상환경 설정"
cd "$APP_DIR"
$PYTHON_VERSION -m venv venv
source venv/bin/activate
pip3 install --upgrade pip
pip3 install -r requirements.txt

# 설정 파일 확인
echo "[4/6] 설정 파일 확인"
if [ ! -f "$APP_DIR/config/config.yaml" ]; then
    cp "$APP_DIR/config/config.example.yaml" "$APP_DIR/config/config.yaml"
    echo "  config.yaml 생성됨 - 수정 필요!"
fi

if [ ! -f "$APP_DIR/.env" ]; then
    cat > "$APP_DIR/.env" << 'EOF'
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
EOF
    echo "  .env 생성됨 - 수정 필요!"
fi

# 권한 설정
echo "[5/6] 권한 설정"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
chmod 600 "$APP_DIR/.env"
chmod 600 "$APP_DIR/config/config.yaml"

# systemd 서비스 설치
echo "[6/6] systemd 서비스 설치"
cp deploy/logos-news.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable "$APP_NAME"

echo ""
echo "=========================================="
echo "설치 완료!"
echo "=========================================="
echo ""
echo "다음 단계:"
echo "1. 설정 파일 수정:"
echo "   sudo nano $APP_DIR/.env"
echo "   sudo nano $APP_DIR/config/config.yaml"
echo ""
echo "2. 서비스 시작:"
echo "   sudo systemctl start $APP_NAME"
echo ""
echo "3. 상태 확인:"
echo "   sudo systemctl status $APP_NAME"
echo "   sudo journalctl -u $APP_NAME -f"
echo ""
