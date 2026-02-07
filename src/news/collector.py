"""뉴스 수집기"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from ..config import NewsConfig

if TYPE_CHECKING:
    from .sources.base import BaseNewsSource


logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    """뉴스 아이템 데이터 클래스"""
    title: str
    link: str
    category: str  # society, economy 등
    source: str    # naver, google 등
    summary: Optional[str] = None
    published_at: Optional[datetime] = None

    def __hash__(self):
        return hash(self.link)

    def __eq__(self, other):
        if isinstance(other, NewsItem):
            return self.link == other.link
        return False


class NewsCollector:
    """뉴스 수집기"""

    def __init__(self, config: NewsConfig):
        """
        Args:
            config: 뉴스 설정
        """
        self.config = config
        self.sources: list["BaseNewsSource"] = []

    def register_source(self, source: "BaseNewsSource") -> None:
        """뉴스 소스 등록

        Args:
            source: 뉴스 소스 인스턴스
        """
        self.sources.append(source)
        logger.info(f"뉴스 소스 등록: {source.name}")

    async def collect_all(self) -> dict[str, list[NewsItem]]:
        """모든 카테고리의 뉴스 수집

        Returns:
            카테고리별 뉴스 딕셔너리
        """
        result: dict[str, list[NewsItem]] = {}

        for cat_name, cat_config in self.config.categories.items():
            if not cat_config.enabled:
                continue

            logger.info(f"카테고리 '{cat_name}' 뉴스 수집 시작")

            all_news: list[NewsItem] = []

            for source in self.sources:
                # 소스 설정 확인
                source_config = self.config.sources.get(source.name)
                if source_config and not source_config.enabled:
                    continue

                try:
                    news_items = await source.fetch_news(
                        category=cat_name,
                        max_items=cat_config.max_items * 2  # 중복 제거 고려하여 여유있게
                    )
                    all_news.extend(news_items)
                    logger.info(f"  {source.name}: {len(news_items)}개 수집")

                except Exception as e:
                    logger.error(f"  {source.name} 수집 실패: {e}")

            # 중복 제거 및 정렬
            unique_news = list(set(all_news))
            unique_news.sort(
                key=lambda x: x.published_at or datetime.min,
                reverse=True
            )

            # 최대 개수 제한
            result[cat_name] = unique_news[:cat_config.max_items]
            logger.info(f"카테고리 '{cat_name}': 최종 {len(result[cat_name])}개")

        return result

    async def collect_by_source(self, source: "BaseNewsSource") -> dict[str, list[NewsItem]]:
        """특정 소스에서 모든 카테고리의 뉴스 수집

        Args:
            source: 뉴스 소스

        Returns:
            카테고리별 뉴스 딕셔너리
        """
        result: dict[str, list[NewsItem]] = {}

        # 소스 설정 확인
        source_config = self.config.sources.get(source.name)
        if source_config and not source_config.enabled:
            logger.warning(f"소스 '{source.name}'가 비활성화 상태입니다.")
            return result

        logger.info(f"소스 '{source.name}'에서 뉴스 수집 시작")

        for cat_name, cat_config in self.config.categories.items():
            if not cat_config.enabled:
                continue

            try:
                news_items = await source.fetch_news(
                    category=cat_name,
                    max_items=cat_config.max_items
                )
                result[cat_name] = news_items
                logger.info(f"  {cat_name}: {len(news_items)}개 수집")

            except Exception as e:
                logger.error(f"  {cat_name} 수집 실패: {e}")
                result[cat_name] = []

        total = sum(len(items) for items in result.values())
        logger.info(f"소스 '{source.name}': 총 {total}개 수집 완료")

        return result
