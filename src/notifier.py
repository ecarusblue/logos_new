"""에러 알림 모듈"""

import logging
import traceback
from datetime import datetime
from typing import Optional

from .telegram import TelegramSender
from .config import TelegramConfig


logger = logging.getLogger(__name__)


class ErrorNotifier:
    """에러 발생 시 텔레그램으로 알림 전송"""

    def __init__(self, telegram_config: TelegramConfig, enabled: bool = True):
        """
        Args:
            telegram_config: 텔레그램 설정
            enabled: 알림 활성화 여부
        """
        self.enabled = enabled
        self.sender = TelegramSender(telegram_config) if enabled else None

    async def notify_error(
        self,
        error: Exception,
        context: Optional[str] = None
    ) -> bool:
        """에러 알림 전송

        Args:
            error: 발생한 예외
            context: 추가 컨텍스트 정보

        Returns:
            전송 성공 여부
        """
        if not self.enabled or not self.sender:
            return False

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message_lines = [
            "⚠️ Logos News 에러 발생",
            "",
            f"🕐 시간: {timestamp}",
            f"❌ 에러: {type(error).__name__}",
            f"📝 메시지: {str(error)[:200]}",
        ]

        if context:
            message_lines.append(f"📍 컨텍스트: {context}")

        # 스택 트레이스 (간략화)
        tb = traceback.format_exception(type(error), error, error.__traceback__)
        if tb:
            short_tb = "".join(tb[-3:])[:500]
            message_lines.extend([
                "",
                "📋 스택 트레이스:",
                f"```\n{short_tb}\n```"
            ])

        message = "\n".join(message_lines)

        try:
            return await self.sender.send_message_plain(message)
        except Exception as e:
            logger.error(f"에러 알림 전송 실패: {e}")
            return False

    async def notify_startup(self) -> bool:
        """시작 알림 전송"""
        if not self.enabled or not self.sender:
            return False

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = (
            "🚀 Logos News 스케줄러 시작\n\n"
            f"🕐 시작 시간: {timestamp}\n"
            "📰 뉴스 브리핑 서비스가 활성화되었습니다."
        )

        try:
            return await self.sender.send_message_plain(message)
        except Exception:
            return False

    async def notify_shutdown(self, reason: str = "정상 종료") -> bool:
        """종료 알림 전송"""
        if not self.enabled or not self.sender:
            return False

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = (
            "🛑 Logos News 스케줄러 종료\n\n"
            f"🕐 종료 시간: {timestamp}\n"
            f"📝 사유: {reason}"
        )

        try:
            return await self.sender.send_message_plain(message)
        except Exception:
            return False
