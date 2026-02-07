"""구글 뉴스 수집기"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional
from urllib.parse import quote

import httpx
import feedparser
from bs4 import BeautifulSoup

from .base import BaseNewsSource
from ..collector import NewsItem


logger = logging.getLogger(__name__)


class GoogleNewsSource(BaseNewsSource):
    """구글 뉴스 RSS 기반 수집기"""

    name = "google"

    # 구글 뉴스 RSS URL (한국어)
    # 토픽 ID는 구글 뉴스에서 확인 가능
    TOPIC_RSS_URL = "https://news.google.com/rss/topics/{topic}?hl=ko&gl=KR&ceid=KR:ko"
    SEARCH_RSS_URL = "https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"

    # 카테고리별 토픽 또는 검색어
    CATEGORY_CONFIG = {
        "society": {"type": "search", "query": "사회 뉴스"},
        "economy": {"type": "topic", "topic": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtdHZHZ0pMVWlnQVAB"},  # 비즈니스
        "politics": {"type": "search", "query": "정치 뉴스"},
        "world": {"type": "topic", "topic": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RjU0FtdHZHZ0pMVWlnQVAB"},  # 세계
        "tech": {"type": "topic", "topic": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtdHZHZ0pMVWlnQVAB"},  # 기술
        "culture": {"type": "search", "query": "문화 연예 뉴스"},
    }

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    async def fetch_news(self, category: str, max_items: int) -> list[NewsItem]:
        """구글 뉴스 RSS에서 뉴스 수집

        Args:
            category: 뉴스 카테고리
            max_items: 최대 수집 개수

        Returns:
            뉴스 아이템 리스트
        """
        config = self.CATEGORY_CONFIG.get(category)
        if not config:
            logger.warning(f"지원하지 않는 카테고리: {category}")
            return []

        # URL 생성
        if config["type"] == "topic":
            url = self.TOPIC_RSS_URL.format(topic=config["topic"])
        else:
            url = self.SEARCH_RSS_URL.format(query=quote(config["query"]))

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                response.raise_for_status()

            feed = feedparser.parse(response.text)
            news_items = []

            for entry in feed.entries[:max_items]:
                item = self._parse_entry(entry, category)
                if item:
                    news_items.append(item)

            logger.debug(f"구글 {category}: {len(news_items)}개 수집")
            return news_items

        except httpx.HTTPError as e:
            logger.error(f"구글 뉴스 요청 실패: {e}")
            return []
        except Exception as e:
            logger.error(f"구글 뉴스 파싱 실패: {e}")
            return []

    def _parse_entry(self, entry: dict, category: str) -> Optional[NewsItem]:
        """RSS 엔트리를 NewsItem으로 변환"""
        try:
            title = entry.get("title", "").strip()

            # 구글 뉴스 링크에서 실제 링크 추출
            link = entry.get("link", "")

            # 요약 추출
            summary = ""
            if "summary" in entry:
                soup = BeautifulSoup(entry.summary, "html.parser")
                summary = soup.get_text().strip()[:200]

            # 발행 시간 파싱
            published_at = None
            if "published_parsed" in entry and entry.published_parsed:
                try:
                    published_at = datetime(*entry.published_parsed[:6])
                except Exception:
                    pass

            # 출처 추출 (제목에서 " - 출처" 형식으로 포함됨)
            source_name = self.name
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                if len(parts) == 2:
                    title = parts[0].strip()
                    source_name = f"google/{parts[1].strip()}"

            return NewsItem(
                title=title,
                link=link,
                category=category,
                source=source_name,
                summary=summary,
                published_at=published_at
            )

        except Exception as e:
            logger.debug(f"엔트리 파싱 실패: {e}")
            return None

    async def resolve_google_url(self, google_url: str) -> Optional[str]:
        """구글 뉴스 리다이렉트 URL에서 실제 URL 추출

        Note: 구글 뉴스는 리다이렉트 URL을 사용하므로
              실제 기사 URL을 얻으려면 추가 처리 필요
        """
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True
            ) as client:
                response = await client.head(google_url)
                return str(response.url)
        except Exception:
            return google_url
