# Logos News

매일 아침 사회/경제 주요 뉴스를 수집하여 텔레그램으로 전송하는 배치 프로그램입니다.

## 설치

```bash
# 가상환경 생성
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip3 install -r requirements.txt
```

## 설정

1. 설정 파일 복사
```bash
cp config/config.example.yaml config/config.yaml
cp .env.example .env
```

2. `.env` 파일에 텔레그램 정보 입력
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### 텔레그램 설정 방법

1. **Bot Token 발급**: [@BotFather](https://t.me/BotFather)에서 새 봇 생성 후 토큰 복사
2. **Chat ID 확인**: 봇에게 메시지 전송 후 `https://api.telegram.org/bot<TOKEN>/getUpdates`에서 확인

## 실행

```bash
# 즉시 실행 (뉴스 브리핑 전송)
python3 -m src.main

# 스케줄러 모드 (백그라운드 데몬)
python3 -m src.main --scheduler

# 텔레그램 연결 테스트
python3 -m src.main --test

# 설정 유효성 검사
python3 -m src.main --validate
```

## 배포

### Cron 설정

매일 아침 7시에 실행:
```bash
0 7 * * * cd /path/to/logos_news && /path/to/venv/bin/python3 -m src.main
```

### Docker

```bash
# 이미지 빌드 및 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### macOS launchd 서비스

```bash
# plist 파일 생성 (~/Library/LaunchAgents/com.logos.news.plist)
cat > ~/Library/LaunchAgents/com.logos.news.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.logos.news</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>-m</string>
        <string>src.main</string>
        <string>--scheduler</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/logos_news</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/path/to/logos_news/logs/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/logos_news/logs/launchd.error.log</string>
</dict>
</plist>
EOF

# 서비스 등록 및 시작
launchctl load ~/Library/LaunchAgents/com.logos.news.plist

# 서비스 상태 확인
launchctl list | grep logos

# 서비스 중지
launchctl unload ~/Library/LaunchAgents/com.logos.news.plist

# 로그 확인
tail -f ~/path/to/logos_news/logs/launchd.log
```

### systemd 서비스 (Linux)

```bash
# 설치 스크립트 실행
sudo ./deploy/install.sh

# 서비스 관리
sudo systemctl start logos-news
sudo systemctl status logos-news
sudo journalctl -u logos-news -f
```

## 테스트

```bash
pytest tests/ -v
```

## 프로젝트 구조

```
logos_news/
├── src/
│   ├── main.py           # 메인 진입점
│   ├── config.py         # 설정 로더
│   ├── logger.py         # 로깅 설정
│   ├── scheduler.py      # 스케줄러 (APScheduler)
│   ├── notifier.py       # 에러 알림
│   ├── news/
│   │   ├── collector.py  # 뉴스 수집기
│   │   ├── formatter.py  # 메시지 포맷터
│   │   └── sources/      # 뉴스 소스별 구현
│   │       ├── naver.py  # 네이버 뉴스 RSS
│   │       └── google.py # 구글 뉴스 RSS
│   └── telegram/
│       └── sender.py     # 텔레그램 전송
├── config/
│   └── config.yaml       # 설정 파일
├── deploy/
│   ├── install.sh        # 설치 스크립트
│   └── logos-news.service # systemd 서비스
├── tests/
├── Dockerfile
├── docker-compose.yml
└── logs/
```

## 지원 뉴스 소스

| 소스 | 설명 | 인증 |
|------|------|------|
| 네이버 뉴스 RSS | 카테고리별 RSS 피드 | 불필요 |
| 구글 뉴스 RSS | 토픽/검색 기반 RSS | 불필요 |
| 네이버 검색 API | 키워드 검색 (선택) | API 키 필요 |

## 개발 현황

- [x] Phase 1: 기본 인프라 (설정, 로깅, 텔레그램)
- [x] Phase 2: 뉴스 수집 (네이버 RSS, 구글 RSS)
- [x] Phase 3: 스케줄링 및 운영 (스케줄러, 에러 알림, Docker, systemd)
