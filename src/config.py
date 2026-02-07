"""설정 로더 모듈"""

from __future__ import annotations

import os
import re
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import yaml
from dotenv import load_dotenv


logger = logging.getLogger(__name__)


@dataclass
class ScheduleConfig:
    hour: str = "7"           # cron hour 표현식 (예: "7", "7-22", "7,12,18")
    minute: int = 0           # 분 (0-59)
    timezone: str = "Asia/Seoul"


@dataclass
class TelegramConfig:
    bot_token: str = ""
    chat_id: str = ""


@dataclass
class CategoryConfig:
    enabled: bool = True
    max_items: int = 5
    keywords: list[str] = field(default_factory=list)


@dataclass
class SourceConfig:
    enabled: bool = True
    priority: int = 1


@dataclass
class NewsConfig:
    categories: dict[str, CategoryConfig] = field(default_factory=dict)
    sources: dict[str, SourceConfig] = field(default_factory=dict)


@dataclass
class MessageConfig:
    include_summary: bool = True
    include_link: bool = True
    format: str = "markdown"


@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str = "logs/news_bot.log"
    max_size_mb: int = 10
    backup_count: int = 5


@dataclass
class Config:
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    news: NewsConfig = field(default_factory=NewsConfig)
    message: MessageConfig = field(default_factory=MessageConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


def _resolve_env_vars(value: str) -> str:
    """문자열 내의 ${VAR} 형식 환경변수를 실제 값으로 치환"""
    pattern = r'\$\{([^}]+)\}'

    def replacer(match):
        env_var = match.group(1)
        env_value = os.getenv(env_var, "")
        if not env_value:
            logger.warning(f"환경변수 {env_var}가 설정되지 않았습니다.")
        return env_value

    return re.sub(pattern, replacer, value)


def _process_dict(data: dict) -> dict:
    """딕셔너리 내 모든 문자열의 환경변수 치환"""
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = _process_dict(value)
        elif isinstance(value, str):
            result[key] = _resolve_env_vars(value)
        elif isinstance(value, list):
            result[key] = [
                _resolve_env_vars(v) if isinstance(v, str) else v
                for v in value
            ]
        else:
            result[key] = value
    return result


def load_config(config_path: Optional[str] = None) -> Config:
    """설정 파일 로드

    Args:
        config_path: 설정 파일 경로. None이면 기본 경로 사용

    Returns:
        Config 객체
    """
    # .env 파일 로드
    load_dotenv()

    # 설정 파일 경로 결정
    if config_path is None:
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config" / "config.yaml"
    else:
        config_path = Path(config_path)

    # 설정 파일 존재 확인
    if not config_path.exists():
        logger.warning(f"설정 파일이 없습니다: {config_path}")
        logger.info("기본 설정을 사용합니다.")
        return Config()

    # YAML 로드
    with open(config_path, 'r', encoding='utf-8') as f:
        raw_config = yaml.safe_load(f) or {}

    # 환경변수 치환
    processed_config = _process_dict(raw_config)

    # Config 객체 생성
    config = Config()

    # Schedule
    if 'schedule' in processed_config:
        config.schedule = ScheduleConfig(**processed_config['schedule'])

    # Telegram
    if 'telegram' in processed_config:
        config.telegram = TelegramConfig(**processed_config['telegram'])

    # News
    if 'news' in processed_config:
        news_data = processed_config['news']
        categories = {}
        sources = {}

        if 'categories' in news_data:
            for name, cat_data in news_data['categories'].items():
                if isinstance(cat_data, dict):
                    categories[name] = CategoryConfig(**cat_data)

        if 'sources' in news_data:
            for name, src_data in news_data['sources'].items():
                if isinstance(src_data, dict):
                    sources[name] = SourceConfig(**src_data)

        config.news = NewsConfig(categories=categories, sources=sources)

    # Message
    if 'message' in processed_config:
        config.message = MessageConfig(**processed_config['message'])

    # Logging
    if 'logging' in processed_config:
        config.logging = LoggingConfig(**processed_config['logging'])

    return config


def validate_config(config: Config) -> list[str]:
    """설정 유효성 검사

    Returns:
        오류 메시지 리스트 (비어있으면 유효)
    """
    errors = []

    # 텔레그램 설정 검사
    if not config.telegram.bot_token:
        errors.append("텔레그램 봇 토큰이 설정되지 않았습니다.")
    if not config.telegram.chat_id:
        errors.append("텔레그램 Chat ID가 설정되지 않았습니다.")

    # 시간 형식 검사 (cron 표현식: 숫자, 범위, 콤마 허용)
    hour_pattern = r'^(\*|([0-9]|1[0-9]|2[0-3])([-,]([0-9]|1[0-9]|2[0-3]))*)$'
    if not re.match(hour_pattern, str(config.schedule.hour)):
        errors.append(f"유효하지 않은 hour 형식: {config.schedule.hour} (예: 7, 7-22, 7,12,18)")
    if not (0 <= config.schedule.minute <= 59):
        errors.append(f"유효하지 않은 minute 값: {config.schedule.minute} (0-59 필요)")

    # 뉴스 카테고리 검사
    if not config.news.categories:
        errors.append("활성화된 뉴스 카테고리가 없습니다.")

    return errors
