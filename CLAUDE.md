# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

Logos News는 매일 아침 사회/경제 뉴스를 수집하여 텔레그램으로 전송하는 Python 배치 프로그램입니다.

## 명령어

```bash
# 실행
python3 -m src.main              # 뉴스 브리핑 즉시 실행
python3 -m src.main --scheduler  # 스케줄러 모드 (데몬)
python3 -m src.main --test       # 텔레그램 연결 테스트
python3 -m src.main --validate   # 설정 유효성 검사

# 테스트
pytest tests/ -v                # 전체 테스트
pytest tests/test_config.py -v  # 특정 테스트 파일

# 의존성
pip3 install -r requirements.txt

# Docker
docker-compose up -d            # 컨테이너 실행
docker-compose logs -f          # 로그 확인
```

## 아키텍처

- **src/config.py**: YAML 설정 로드, 환경변수 `${VAR}` 치환 지원
- **src/scheduler.py**: `NewsScheduler` - APScheduler 기반, cron 트리거
- **src/notifier.py**: `ErrorNotifier` - 에러 발생 시 텔레그램 알림
- **src/telegram/sender.py**: `TelegramSender` - 비동기 메시지 전송, 재시도 로직 포함
- **src/news/collector.py**: `NewsCollector` - 뉴스 소스 플러그인 구조
- **src/news/formatter.py**: `NewsFormatter` - plain/markdown/html 포맷 지원
- **src/news/sources/**: 뉴스 소스 구현
  - `naver.py`: 네이버 뉴스 RSS, 검색 API
  - `google.py`: 구글 뉴스 RSS
  - `base.py`: `BaseNewsSource` 추상 클래스
- **src/main.py**: CLI 진입점, asyncio 기반

## 새 뉴스 소스 추가

```python
# src/news/sources/custom.py
from .base import BaseNewsSource
from ..collector import NewsItem

class CustomNewsSource(BaseNewsSource):
    name = "custom"

    async def fetch_news(self, category: str, max_items: int) -> list[NewsItem]:
        # 구현
        pass
```

## 설정 파일

- `config/config.yaml`: 실행 설정 (시간, 카테고리, 소스)
- `.env`: 민감 정보 (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

## 배포 옵션

- **Cron**: `python3 -m src.main` 직접 실행
- **스케줄러 모드**: `python3 -m src.main --scheduler` (내장 APScheduler)
- **Docker**: `docker-compose up -d`
- **systemd**: `deploy/install.sh` 스크립트 사용
