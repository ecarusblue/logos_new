#!/bin/bash
# Logos News macOS 설치 스크립트
# 사용법: ./deploy/install-macos.sh

set -e

# 설정
APP_NAME="com.logosnews.agent"
APP_DIR="$HOME/logos_news"
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_VERSION="python3.12"
PLIST_PATH="$HOME/Library/LaunchAgents/$APP_NAME.plist"

echo "=========================================="
echo "Logos News macOS 설치 시작"
echo "=========================================="

# Python 버전 확인
echo "[1/5] Python 버전 확인"
if ! command -v $PYTHON_VERSION &> /dev/null; then
    echo "  오류: $PYTHON_VERSION 이 설치되어 있지 않습니다."
    echo "  brew install python@3.12 로 설치하세요."
    exit 1
fi
echo "  $($PYTHON_VERSION --version) 확인됨"

# 디렉토리 설정
echo "[2/5] 디렉토리 설정"
mkdir -p "$APP_DIR"/{config,logs}
cp -r "$SCRIPT_DIR/src" "$APP_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$APP_DIR/"
cp "$SCRIPT_DIR/config/config.example.yaml" "$APP_DIR/config/"

# 가상환경 설정
echo "[3/5] Python 가상환경 설정"
cd "$APP_DIR"
$PYTHON_VERSION -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# 설정 파일 생성
echo "[4/5] 설정 파일 확인"
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

chmod 600 "$APP_DIR/.env"
chmod 600 "$APP_DIR/config/config.yaml"

# LaunchAgent 설치
echo "[5/5] LaunchAgent 설치"
mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$APP_NAME</string>

    <key>ProgramArguments</key>
    <array>
        <string>$APP_DIR/venv/bin/python3</string>
        <string>-m</string>
        <string>src.main</string>
        <string>--scheduler</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$APP_DIR</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>$APP_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>$APP_DIR/logs/stdout.log</string>

    <key>StandardErrorPath</key>
    <string>$APP_DIR/logs/stderr.log</string>
</dict>
</plist>
EOF

echo ""
echo "=========================================="
echo "설치 완료!"
echo "=========================================="
echo ""
echo "설치 경로: $APP_DIR"
echo ""
echo "다음 단계:"
echo "1. 설정 파일 수정:"
echo "   nano $APP_DIR/.env"
echo "   nano $APP_DIR/config/config.yaml"
echo ""
echo "2. 서비스 시작:"
echo "   launchctl load $PLIST_PATH"
echo ""
echo "3. 서비스 중지:"
echo "   launchctl unload $PLIST_PATH"
echo ""
echo "4. 서비스 상태 확인:"
echo "   launchctl list | grep logosnews"
echo "   # 또는"
echo "   launchctl list $APP_NAME"
echo ""
echo "5. 즉시 실행 테스트:"
echo "   cd $APP_DIR && ./venv/bin/python3 -m src.main --test"
echo ""
echo "6. 로그 확인:"
echo "   tail -f $APP_DIR/logs/stdout.log"
echo ""
