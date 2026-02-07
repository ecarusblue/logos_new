# PRD: 일일 뉴스 브리핑 텔레그램 봇

## 1. 개요

### 1.1 프로젝트 명
**Logos News** - 일일 사회/경제 뉴스 브리핑 서비스

### 1.2 목적
매일 아침 지정된 시간에 사회/경제 분야의 주요 뉴스를 자동으로 수집, 요약하여 텔레그램으로 전송하는 배치 프로그램

### 1.3 기술 스택
- **언어**: Python 3.11+
- **실행 방식**: 배치 프로그램 (cron/systemd timer 또는 스케줄러)
- **메시징**: Telegram Bot API
- **설정 관리**: YAML 또는 환경변수

---

## 2. 기능 요구사항

### 2.1 뉴스 수집
- 사회 뉴스 수집 (네이버 뉴스, 구글 뉴스 등)
- 경제 뉴스 수집 (네이버 금융, 한경, 매경 등)
- 중복 뉴스 필터링
- 주요 뉴스 선별 (상위 5~10개)

### 2.2 뉴스 정리/요약
- 제목, 요약, 원문 링크 포함
- 카테고리별 분류 (사회/경제)
- 가독성 좋은 포맷으로 정리

### 2.3 텔레그램 전송
- 특정 사용자에게 메시지 전송
- 마크다운 형식 지원
- 전송 실패 시 재시도 로직

### 2.4 설정 관리
- 실행 시간 설정 (cron 표현식 또는 시간 지정)
- 텔레그램 Bot Token 및 Chat ID 설정
- 뉴스 소스 및 카테고리 설정
- 수집할 뉴스 개수 설정

---

## 3. 개발 단계

### Phase 1: 기본 인프라 구축
**목표**: 프로젝트 구조 설정 및 핵심 기능 스켈레톤 구현

**작업 내용**:
1. 프로젝트 구조 생성
   ```
   logos_news/
   ├── src/
   │   ├── __init__.py
   │   ├── main.py           # 메인 진입점
   │   ├── config.py         # 설정 로더
   │   ├── news/
   │   │   ├── __init__.py
   │   │   ├── collector.py  # 뉴스 수집 인터페이스
   │   │   └── sources/      # 뉴스 소스별 구현
   │   └── telegram/
   │       ├── __init__.py
   │       └── sender.py     # 텔레그램 전송
   ├── config/
   │   ├── config.yaml       # 기본 설정
   │   └── config.example.yaml
   ├── tests/
   ├── requirements.txt
   └── README.md
   ```

2. 설정 파일 구조 정의 (`config.yaml`)
   ```yaml
   schedule:
     time: "07:00"
     timezone: "Asia/Seoul"

   telegram:
     bot_token: "${TELEGRAM_BOT_TOKEN}"
     chat_id: "${TELEGRAM_CHAT_ID}"

   news:
     categories:
       - society
       - economy
     max_items_per_category: 5
     sources:
       - naver
       - google
   ```

3. 기본 모듈 구현
   - 설정 로더 (환경변수 및 YAML 지원)
   - 로깅 설정
   - 텔레그램 전송 기본 기능

**산출물**:
- 실행 가능한 프로젝트 스켈레톤
- 텔레그램 테스트 메시지 전송 가능

---

### Phase 2: 뉴스 수집 및 처리
**목표**: 실제 뉴스 데이터 수집 및 정리 기능 구현

**작업 내용**:
1. 뉴스 수집기 구현
   - 네이버 뉴스 RSS/API 연동
   - 구글 뉴스 RSS 연동
   - 웹 스크래핑 (필요시)

2. 뉴스 처리 로직
   - 뉴스 데이터 모델 정의
   - 중복 제거 로직
   - 카테고리별 정렬 및 필터링

3. 메시지 포맷터 구현
   ```
   📰 오늘의 뉴스 브리핑
   2024년 1월 15일 (월)

   📌 사회
   1. [제목] - 출처
      요약 내용...
      🔗 원문 링크

   💰 경제
   1. [제목] - 출처
      요약 내용...
      🔗 원문 링크
   ```

**산출물**:
- 실제 뉴스 데이터 수집 기능
- 포맷팅된 뉴스 메시지 생성

---

### Phase 3: 스케줄링 및 운영
**목표**: 배치 실행 환경 구성 및 안정화

**작업 내용**:
1. 스케줄링 옵션 구현
   - CLI 직접 실행 모드
   - 내장 스케줄러 (APScheduler) 옵션
   - cron/systemd 연동 가이드

2. 에러 처리 및 모니터링
   - 재시도 로직 구현
   - 에러 알림 (텔레그램으로 에러 전송)
   - 실행 로그 저장

3. 운영 편의 기능
   - 수동 실행 CLI 명령어
   - 설정 유효성 검사
   - 헬스체크 엔드포인트 (선택)

4. 배포 구성
   - Docker 컨테이너화 (선택)
   - 시스템 서비스 등록 스크립트

**산출물**:
- 운영 가능한 완성 프로그램
- 배포 및 운영 가이드

---

## 4. 비기능 요구사항

### 4.1 보안
- API 키 및 토큰은 환경변수로 관리
- 설정 파일에 민감 정보 직접 기재 금지

### 4.2 안정성
- 네트워크 오류 시 최대 3회 재시도
- 부분 실패 시에도 가능한 뉴스는 전송

### 4.3 유지보수성
- 뉴스 소스 추가가 용이한 플러그인 구조
- 명확한 로깅으로 디버깅 용이

---

## 5. 환경 설정 예시

### config.yaml
```yaml
# 스케줄 설정
schedule:
  time: "07:00"           # 실행 시간 (HH:MM)
  timezone: "Asia/Seoul"  # 타임존

# 텔레그램 설정
telegram:
  bot_token: "${TELEGRAM_BOT_TOKEN}"  # 환경변수 참조
  chat_id: "${TELEGRAM_CHAT_ID}"      # 환경변수 참조

# 뉴스 설정
news:
  categories:
    society:
      enabled: true
      max_items: 5
    economy:
      enabled: true
      max_items: 5

  sources:
    naver:
      enabled: true
      priority: 1
    google:
      enabled: true
      priority: 2

# 메시지 설정
message:
  include_summary: true
  include_link: true
  format: "markdown"  # markdown 또는 html

# 로깅 설정
logging:
  level: "INFO"
  file: "logs/news_bot.log"
```

### 환경변수 (.env)
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

---

## 6. 실행 방법

### 직접 실행
```bash
python3 -m src.main
```

### cron 설정 예시
```bash
# 매일 아침 7시 실행
0 7 * * * cd /path/to/logos_news && python3 -m src.main
```

### 테스트 실행
```bash
# 즉시 뉴스 전송 (테스트)
python3 -m src.main --now

# 설정 검증만
python3 -m src.main --validate
```
