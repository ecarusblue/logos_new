"""텔레그램 메시지 전송 모듈"""

import logging
from typing import Optional

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from ..config import TelegramConfig


logger = logging.getLogger(__name__)


class TelegramSender:
    """텔레그램 메시지 전송 클래스"""

    def __init__(self, config: TelegramConfig):
        """
        Args:
            config: 텔레그램 설정
        """
        self.config = config
        self.bot = Bot(token=config.bot_token)

    async def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: str = "markdown"
    ) -> bool:
        """메시지 전송

        Args:
            text: 전송할 메시지
            chat_id: 대상 채팅 ID (None이면 설정값 사용)
            parse_mode: 파싱 모드 (markdown, html)

        Returns:
            전송 성공 여부
        """
        target_chat_id = chat_id or self.config.chat_id

        if not target_chat_id:
            logger.error("Chat ID가 설정되지 않았습니다.")
            return False

        # 파싱 모드 매핑
        mode_map = {
            "markdown": ParseMode.MARKDOWN_V2,
            "html": ParseMode.HTML,
        }
        mode = mode_map.get(parse_mode.lower())

        try:
            await self.bot.send_message(
                chat_id=target_chat_id,
                text=text,
                parse_mode=mode,
                disable_web_page_preview=True
            )
            logger.info(f"메시지 전송 완료 (chat_id: {target_chat_id})")
            return True

        except TelegramError as e:
            logger.error(f"메시지 전송 실패: {e}")
            return False

    async def send_message_plain(
        self,
        text: str,
        chat_id: Optional[str] = None
    ) -> bool:
        """일반 텍스트 메시지 전송 (파싱 없음)

        Args:
            text: 전송할 메시지
            chat_id: 대상 채팅 ID (None이면 설정값 사용)

        Returns:
            전송 성공 여부
        """
        target_chat_id = chat_id or self.config.chat_id

        if not target_chat_id:
            logger.error("Chat ID가 설정되지 않았습니다.")
            return False

        try:
            await self.bot.send_message(
                chat_id=target_chat_id,
                text=text,
                disable_web_page_preview=True
            )
            logger.info(f"메시지 전송 완료 (chat_id: {target_chat_id})")
            return True

        except TelegramError as e:
            logger.error(f"메시지 전송 실패: {e}")
            return False

    async def send_with_retry(
        self,
        text: str,
        max_retries: int = 3,
        chat_id: Optional[str] = None,
        parse_mode: Optional[str] = None
    ) -> bool:
        """재시도 로직이 포함된 메시지 전송

        Args:
            text: 전송할 메시지
            max_retries: 최대 재시도 횟수
            chat_id: 대상 채팅 ID
            parse_mode: 파싱 모드 (None이면 plain text)

        Returns:
            전송 성공 여부
        """
        for attempt in range(max_retries):
            try:
                if parse_mode:
                    success = await self.send_message(text, chat_id, parse_mode)
                else:
                    success = await self.send_message_plain(text, chat_id)

                if success:
                    return True

            except Exception as e:
                logger.warning(f"전송 시도 {attempt + 1}/{max_retries} 실패: {e}")

                if attempt < max_retries - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)  # 지수 백오프

        logger.error(f"최대 재시도 횟수({max_retries})를 초과했습니다.")
        return False

    async def test_connection(self) -> bool:
        """봇 연결 테스트

        Returns:
            연결 성공 여부
        """
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"봇 연결 성공: @{bot_info.username}")
            return True
        except TelegramError as e:
            logger.error(f"봇 연결 실패: {e}")
            return False
