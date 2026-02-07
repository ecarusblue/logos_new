"""스케줄러 모듈"""

import asyncio
import logging
import signal
from datetime import datetime
from typing import Callable, Awaitable, Optional
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import ScheduleConfig


logger = logging.getLogger(__name__)


class NewsScheduler:
    """뉴스 브리핑 스케줄러"""

    def __init__(self, config: ScheduleConfig):
        """
        Args:
            config: 스케줄 설정
        """
        self.config = config
        self.scheduler = AsyncIOScheduler()
        self._shutdown_event = asyncio.Event()
        self._job_func: Optional[Callable[[], Awaitable[bool]]] = None

    def set_job(self, func: Callable[[], Awaitable[bool]]) -> None:
        """실행할 작업 설정

        Args:
            func: 비동기 작업 함수
        """
        self._job_func = func

    async def _run_job(self) -> None:
        """작업 실행 래퍼"""
        if not self._job_func:
            logger.error("실행할 작업이 설정되지 않았습니다.")
            return

        logger.info("=" * 50)
        logger.info(f"스케줄 작업 시작: {datetime.now()}")
        logger.info("=" * 50)

        try:
            success = await self._job_func()
            if success:
                logger.info("스케줄 작업 완료")
            else:
                logger.error("스케줄 작업 실패")
        except Exception as e:
            logger.exception(f"스케줄 작업 중 예외 발생: {e}")

    def start(self) -> None:
        """스케줄러 시작"""
        # 타임존 설정
        try:
            tz = ZoneInfo(self.config.timezone)
        except Exception:
            logger.warning(f"타임존 '{self.config.timezone}' 로드 실패, UTC 사용")
            tz = ZoneInfo("UTC")

        # 크론 트리거 생성 (hour는 cron 표현식 지원: "7", "7-22", "7,12,18" 등)
        trigger = CronTrigger(
            hour=self.config.hour,
            minute=self.config.minute,
            timezone=tz
        )

        # 작업 등록
        self.scheduler.add_job(
            self._run_job,
            trigger=trigger,
            id="news_briefing",
            name="Daily News Briefing",
            replace_existing=True
        )

        self.scheduler.start()

        next_run = self.scheduler.get_job("news_briefing").next_run_time
        logger.info(f"스케줄러 시작됨")
        logger.info(f"  실행 시간: 매일 {self.config.hour}시 {self.config.minute}분 ({self.config.timezone})")
        logger.info(f"  다음 실행: {next_run}")

    def stop(self) -> None:
        """스케줄러 중지"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("스케줄러 중지됨")

    async def run_forever(self) -> None:
        """스케줄러 무한 실행"""
        self.start()

        # 시그널 핸들러 설정
        loop = asyncio.get_event_loop()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(self._shutdown())
            )

        logger.info("스케줄러가 실행 중입니다. Ctrl+C로 종료하세요.")

        # 종료 대기
        await self._shutdown_event.wait()

        self.stop()

    async def _shutdown(self) -> None:
        """종료 처리"""
        logger.info("종료 신호 수신...")
        self._shutdown_event.set()

    def get_next_run_time(self) -> Optional[datetime]:
        """다음 실행 시간 반환"""
        job = self.scheduler.get_job("news_briefing")
        return job.next_run_time if job else None
