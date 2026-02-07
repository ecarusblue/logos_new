"""설정 모듈 테스트"""

import os
import pytest
import tempfile
from pathlib import Path

from src.config import (
    load_config,
    validate_config,
    Config,
    TelegramConfig,
    ScheduleConfig,
)


class TestLoadConfig:
    """load_config 함수 테스트"""

    def test_load_default_config_when_file_not_exists(self):
        """설정 파일이 없을 때 기본값 반환"""
        config = load_config("/nonexistent/path/config.yaml")

        assert isinstance(config, Config)
        assert config.schedule.hour == "7"
        assert config.schedule.minute == 0
        assert config.schedule.timezone == "Asia/Seoul"

    def test_load_config_from_yaml(self, tmp_path):
        """YAML 파일에서 설정 로드"""
        config_content = """
schedule:
  hour: "8"
  minute: 30
  timezone: "UTC"

telegram:
  bot_token: "test_token"
  chat_id: "123456"

news:
  categories:
    society:
      enabled: true
      max_items: 3
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)

        config = load_config(str(config_file))

        assert config.schedule.hour == "8"
        assert config.schedule.minute == 30
        assert config.schedule.timezone == "UTC"
        assert config.telegram.bot_token == "test_token"
        assert config.telegram.chat_id == "123456"
        assert config.news.categories["society"].max_items == 3

    def test_resolve_env_vars(self, tmp_path, monkeypatch):
        """환경변수 치환 테스트"""
        monkeypatch.setenv("TEST_BOT_TOKEN", "env_token_value")
        monkeypatch.setenv("TEST_CHAT_ID", "env_chat_id")

        config_content = """
telegram:
  bot_token: "${TEST_BOT_TOKEN}"
  chat_id: "${TEST_CHAT_ID}"
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)

        config = load_config(str(config_file))

        assert config.telegram.bot_token == "env_token_value"
        assert config.telegram.chat_id == "env_chat_id"


class TestValidateConfig:
    """validate_config 함수 테스트"""

    def test_valid_config(self):
        """유효한 설정"""
        config = Config(
            telegram=TelegramConfig(
                bot_token="valid_token",
                chat_id="123456"
            ),
            schedule=ScheduleConfig(hour="7", minute=30)
        )
        config.news.categories["society"] = type(
            "CategoryConfig", (), {"enabled": True, "max_items": 5}
        )()

        errors = validate_config(config)
        assert len(errors) == 0

    def test_missing_bot_token(self):
        """봇 토큰 누락"""
        config = Config(
            telegram=TelegramConfig(bot_token="", chat_id="123456")
        )

        errors = validate_config(config)
        assert any("봇 토큰" in e for e in errors)

    def test_missing_chat_id(self):
        """Chat ID 누락"""
        config = Config(
            telegram=TelegramConfig(bot_token="token", chat_id="")
        )

        errors = validate_config(config)
        assert any("Chat ID" in e for e in errors)

    def test_invalid_hour_format(self):
        """잘못된 hour 형식"""
        config = Config(
            telegram=TelegramConfig(bot_token="token", chat_id="123"),
            schedule=ScheduleConfig(hour="25")
        )

        errors = validate_config(config)
        assert any("hour" in e for e in errors)

    def test_invalid_minute_value(self):
        """잘못된 minute 값"""
        config = Config(
            telegram=TelegramConfig(bot_token="token", chat_id="123"),
            schedule=ScheduleConfig(hour="7", minute=60)
        )

        errors = validate_config(config)
        assert any("minute" in e for e in errors)

    def test_valid_hour_formats(self):
        """유효한 hour 형식들"""
        valid_hours = ["0", "7", "23", "7-22", "7,12,18", "0-23"]

        for hour_str in valid_hours:
            config = Config(
                telegram=TelegramConfig(bot_token="token", chat_id="123"),
                schedule=ScheduleConfig(hour=hour_str, minute=0)
            )
            config.news.categories["test"] = type(
                "CategoryConfig", (), {"enabled": True}
            )()

            errors = validate_config(config)
            hour_errors = [e for e in errors if "hour" in e]
            assert len(hour_errors) == 0, f"Hour {hour_str} should be valid"
