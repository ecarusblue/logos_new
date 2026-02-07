"""스케줄러 모듈 테스트"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.scheduler import NewsScheduler
from src.config import ScheduleConfig


class TestNewsScheduler:
    """NewsScheduler 테스트"""

    @pytest.fixture
    def config(self):
        return ScheduleConfig(
            hour="7",
            minute=0,
            timezone="Asia/Seoul"
        )

    def test_scheduler_creation(self, config):
        """스케줄러 생성"""
        scheduler = NewsScheduler(config)

        assert scheduler.config == config
        assert scheduler._job_func is None

    def test_set_job(self, config):
        """작업 설정"""
        scheduler = NewsScheduler(config)

        async def dummy_job():
            return True

        scheduler.set_job(dummy_job)

        assert scheduler._job_func == dummy_job

    def test_start_and_stop(self, config):
        """스케줄러 시작/중지"""
        scheduler = NewsScheduler(config)
        scheduler.set_job(AsyncMock(return_value=True))

        scheduler.start()
        assert scheduler.scheduler.running

        next_run = scheduler.get_next_run_time()
        assert next_run is not None

        scheduler.stop()
        assert not scheduler.scheduler.running

    def test_get_next_run_time_before_start(self, config):
        """시작 전 다음 실행 시간 조회"""
        scheduler = NewsScheduler(config)

        next_run = scheduler.get_next_run_time()
        assert next_run is None


class TestScheduleConfig:
    """ScheduleConfig 테스트"""

    def test_default_values(self):
        """기본값 확인"""
        config = ScheduleConfig()

        assert config.hour == "7"
        assert config.minute == 0
        assert config.timezone == "Asia/Seoul"

    def test_custom_values(self):
        """사용자 지정 값"""
        config = ScheduleConfig(
            hour="7-22",
            minute=30,
            timezone="UTC"
        )

        assert config.hour == "7-22"
        assert config.minute == 30
        assert config.timezone == "UTC"
