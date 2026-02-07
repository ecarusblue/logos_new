"""메인 진입점"""

import asyncio
import argparse
import sys
import logging
from typing import Optional

from .config import load_config, validate_config, Config
from .logger import setup_logging
from .telegram import TelegramSender
from .news import NewsCollector, NewsFormatter, NaverNewsSource, GoogleNewsSource
from .scheduler import NewsScheduler
from .notifier import ErrorNotifier


logger = logging.getLogger(__name__)


async def run_news_briefing(
    config: Optional[Config] = None,
    config_path: Optional[str] = None,
    notifier: Optional[ErrorNotifier] = None
) -> bool:
    """뉴스 브리핑 실행

    Args:
        config: 설정 객체 (None이면 로드)
        config_path: 설정 파일 경로
        notifier: 에러 알림 객체

    Returns:
        실행 성공 여부
    """
    # 설정 로드
    if config is None:
        config = load_config(config_path)
        setup_logging(config.logging)

    logger.info("=" * 50)
    logger.info("Logos News 뉴스 브리핑 시작")
    logger.info("=" * 50)

    try:
        # 설정 검증
        errors = validate_config(config)
        if errors:
            for error in errors:
                logger.error(f"설정 오류: {error}")
            return False

        # 텔레그램 연결 테스트
        sender = TelegramSender(config.telegram)
        if not await sender.test_connection():
            logger.error("텔레그램 봇 연결에 실패했습니다.")
            return False

        # 뉴스 수집기 설정
        collector = NewsCollector(config.news)

        # 활성화된 뉴스 소스 목록
        sources = []
        if config.news.sources.get("naver") and config.news.sources["naver"].enabled:
            sources.append(NaverNewsSource())
        if config.news.sources.get("google") and config.news.sources["google"].enabled:
            sources.append(GoogleNewsSource())

        if not sources:
            logger.warning("활성화된 뉴스 소스가 없습니다.")
            return False

        # 메시지 포맷터
        formatter = NewsFormatter(
            include_summary=config.message.include_summary,
            include_link=config.message.include_link,
            format_type="plain"
        )

        # 소스별로 뉴스 수집 및 전송
        total_success = True
        total_news = 0

        for source in sources:
            logger.info(f"뉴스 수집 시작: {source.name}")
            news_by_category = await collector.collect_by_source(source)

            source_news = sum(len(items) for items in news_by_category.values())
            total_news += source_news

            if not any(news_by_category.values()):
                logger.warning(f"{source.name}: 수집된 뉴스가 없습니다.")
                continue

            # 소스별 메시지 포맷팅 및 전송
            message = formatter.format(news_by_category, source_name=source.name)
            success = await sender.send_with_retry(message)

            if success:
                logger.info(f"{source.name}: 뉴스 브리핑 전송 완료")
            else:
                logger.error(f"{source.name}: 뉴스 브리핑 전송 실패")
                total_success = False

        logger.info(f"총 {total_news}개 뉴스 수집 완료")

        if total_news == 0:
            await sender.send_message_plain(
                "📰 오늘의 뉴스 브리핑\n\n"
                "현재 수집된 뉴스가 없습니다."
            )

        return total_success

    except Exception as e:
        logger.exception(f"뉴스 브리핑 중 오류 발생: {e}")
        if notifier:
            await notifier.notify_error(e, context="뉴스 브리핑 실행")
        return False


async def run_scheduler(config_path: Optional[str] = None) -> None:
    """스케줄러 모드 실행

    Args:
        config_path: 설정 파일 경로
    """
    config = load_config(config_path)
    setup_logging(config.logging)

    logger.info("=" * 50)
    logger.info("Logos News 스케줄러 모드")
    logger.info("=" * 50)

    # 설정 검증
    errors = validate_config(config)
    if errors:
        for error in errors:
            logger.error(f"설정 오류: {error}")
        return

    # 에러 알림 설정
    notifier = ErrorNotifier(config.telegram, enabled=True)

    # 스케줄러 설정
    scheduler = NewsScheduler(config.schedule)

    # 작업 함수 정의
    async def job():
        return await run_news_briefing(config=config, notifier=notifier)

    scheduler.set_job(job)

    # 시작 알림
    await notifier.notify_startup()

    try:
        # 스케줄러 실행
        await scheduler.run_forever()
    except Exception as e:
        logger.exception(f"스케줄러 오류: {e}")
        await notifier.notify_error(e, context="스케줄러 실행")
    finally:
        await notifier.notify_shutdown()


async def test_telegram(config_path: Optional[str] = None) -> bool:
    """텔레그램 연결 테스트

    Args:
        config_path: 설정 파일 경로

    Returns:
        테스트 성공 여부
    """
    config = load_config(config_path)
    setup_logging(config.logging)

    errors = validate_config(config)
    if errors:
        for error in errors:
            logger.error(f"설정 오류: {error}")
        return False

    sender = TelegramSender(config.telegram)

    # 연결 테스트
    if not await sender.test_connection():
        return False

    # 테스트 메시지 전송
    test_message = (
        "✅ Logos News 연결 테스트 성공!\n\n"
        "텔레그램 봇이 정상적으로 작동합니다.\n"
        "뉴스 브리핑을 받을 준비가 되었습니다."
    )

    return await sender.send_message_plain(test_message)


def validate_only(config_path: Optional[str] = None) -> bool:
    """설정 유효성만 검사

    Args:
        config_path: 설정 파일 경로

    Returns:
        유효성 검사 성공 여부
    """
    config = load_config(config_path)
    setup_logging(config.logging)

    errors = validate_config(config)

    if errors:
        logger.error("설정 검증 실패:")
        for error in errors:
            logger.error(f"  - {error}")
        return False

    logger.info("설정 검증 완료: 모든 설정이 유효합니다.")

    # 설정 요약 출력
    logger.info(f"  실행 시간: {config.schedule.hour}시 {config.schedule.minute}분 ({config.schedule.timezone})")

    if config.telegram.chat_id:
        display_id = config.telegram.chat_id[:10] + "..." if len(config.telegram.chat_id) > 10 else config.telegram.chat_id
        logger.info(f"  텔레그램 Chat ID: {display_id}")

    enabled_categories = [
        name for name, cat in config.news.categories.items()
        if cat.enabled
    ]
    logger.info(f"  활성 카테고리: {', '.join(enabled_categories)}")

    enabled_sources = [
        name for name, src in config.news.sources.items()
        if src.enabled
    ]
    logger.info(f"  활성 소스: {', '.join(enabled_sources)}")

    return True


def main():
    """CLI 메인 함수"""
    parser = argparse.ArgumentParser(
        description="Logos News - 일일 뉴스 브리핑 텔레그램 봇",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
실행 예시:
  python -m src.main              # 즉시 뉴스 브리핑 실행
  python -m src.main --scheduler  # 스케줄러 모드 (데몬)
  python -m src.main --test       # 텔레그램 연결 테스트
  python -m src.main --validate   # 설정 유효성 검사
        """
    )

    parser.add_argument(
        "-c", "--config",
        help="설정 파일 경로",
        default=None
    )

    parser.add_argument(
        "--now",
        action="store_true",
        help="즉시 뉴스 브리핑 실행 (기본값)"
    )

    parser.add_argument(
        "--scheduler",
        action="store_true",
        help="스케줄러 모드로 실행 (백그라운드 데몬)"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="텔레그램 연결 테스트"
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="설정 유효성만 검사"
    )

    args = parser.parse_args()

    # 실행 모드 결정
    if args.validate:
        success = validate_only(args.config)
        sys.exit(0 if success else 1)

    elif args.test:
        success = asyncio.run(test_telegram(args.config))
        sys.exit(0 if success else 1)

    elif args.scheduler:
        asyncio.run(run_scheduler(args.config))

    else:
        # 기본: 즉시 실행 (--now와 동일)
        success = asyncio.run(run_news_briefing(config_path=args.config))
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
