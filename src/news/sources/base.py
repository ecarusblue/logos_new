"""뉴스 소스 기본 클래스"""

from __future__ import annotations

from abc import ABC, abstractmethod
from ..collector import NewsItem


class BaseNewsSource(ABC):
    """뉴스 소스 추상 기본 클래스"""

    name: str = "base"

    @abstractmethod
    async def fetch_news(self, category: str, max_items: int) -> list[NewsItem]:
        """뉴스 수집

        Args:
            category: 뉴스 카테고리 (society, economy)
            max_items: 최대 수집 개수

        Returns:
            뉴스 아이템 리스트
        """
        pass
