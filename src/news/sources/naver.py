"""네이버 뉴스 수집기"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from .base import BaseNewsSource
from ..collector import NewsItem


logger = logging.getLogger(__name__)


class NaverNewsSource(BaseNewsSource):
    """네이버 뉴스 웹 스크래핑 기반 수집기"""

    name = "naver"

    # 네이버 뉴스 카테고리 매핑
    CATEGORY_MAP = {
        "society": "102",    # 사회
        "economy": "101",    # 경제
        "politics": "100",   # 정치
        "world": "104",      # 세계
        "culture": "103",    # 생활/문화
        "tech": "105",       # IT/과학
    }

    LIST_URL = "https://news.naver.com/main/list.naver?mode=LSD&mid=sec&sid1={sid}"

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    async def fetch_news(self, category: str, max_items: int) -> list[NewsItem]:
        """네이버 뉴스 목록 페이지에서 뉴스 수집

        Args:
            category: 뉴스 카테고리
            max_items: 최대 수집 개수

        Returns:
            뉴스 아이템 리스트
        """
        sid = self.CATEGORY_MAP.get(category)
        if not sid:
            logger.warning(f"지원하지 않는 카테고리: {category}")
            return []

        url = self.LIST_URL.format(sid=sid)

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers=self.DEFAULT_HEADERS
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            news_items = []

            # 뉴스 목록에서 기사 추출
            articles = soup.select("ul.type06_headline li, ul.type06 li")

            for article in articles[:max_items]:
                item = self._parse_article(article, category)
                if item:
                    news_items.append(item)

            logger.debug(f"네이버 {category}: {len(news_items)}개 수집")
            return news_items

        except httpx.HTTPError as e:
            logger.error(f"네이버 뉴스 요청 실패: {e}")
            return []
        except Exception as e:
            logger.error(f"네이버 뉴스 파싱 실패: {e}")
            return []

    def _parse_article(self, article, category: str) -> Optional[NewsItem]:
        """HTML 기사 요소를 NewsItem으로 변환"""
        try:
            # 제목과 링크 추출
            title_elem = article.select_one("dt:not(.photo) a, a.nclicks")
            if not title_elem:
                return None

            title = title_elem.get_text().strip()
            link = title_elem.get("href", "")

            if not title or not link:
                return None

            # 요약 추출
            summary = ""
            summary_elem = article.select_one("dd, span.lede")
            if summary_elem:
                summary = summary_elem.get_text().strip()[:200]

            # 언론사 추출
            source_elem = article.select_one("span.writing")
            source_name = source_elem.get_text().strip() if source_elem else ""

            return NewsItem(
                title=title,
                link=link,
                category=category,
                source=f"{self.name}:{source_name}" if source_name else self.name,
                summary=summary,
                published_at=None
            )

        except Exception as e:
            logger.debug(f"기사 파싱 실패: {e}")
            return None


class NaverSearchNewsSource(BaseNewsSource):
    """네이버 검색 API 기반 뉴스 수집기 (API 키 필요)"""

    name = "naver_search"

    SEARCH_URL = "https://openapi.naver.com/v1/search/news.json"

    # 카테고리별 검색 키워드
    CATEGORY_KEYWORDS = {
        "society": "사회 사건 사고",
        "economy": "경제 증시 금융",
        "politics": "정치 국회",
        "world": "국제 해외",
        "tech": "IT 기술 과학",
    }

    def __init__(self, client_id: str, client_secret: str, timeout: int = 10):
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout

    async def fetch_news(self, category: str, max_items: int) -> list[NewsItem]:
        """네이버 검색 API로 뉴스 수집

        Args:
            category: 뉴스 카테고리
            max_items: 최대 수집 개수

        Returns:
            뉴스 아이템 리스트
        """
        query = self.CATEGORY_KEYWORDS.get(category, category)

        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

        params = {
            "query": query,
            "display": max_items,
            "sort": "date",  # 최신순
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True
            ) as client:
                response = await client.get(
                    self.SEARCH_URL,
                    headers=headers,
                    params=params
                )
                response.raise_for_status()

            data = response.json()
            news_items = []

            for item in data.get("items", []):
                news_item = self._parse_item(item, category)
                if news_item:
                    news_items.append(news_item)

            return news_items

        except httpx.HTTPError as e:
            logger.error(f"네이버 검색 API 요청 실패: {e}")
            return []
        except Exception as e:
            logger.error(f"네이버 검색 결과 파싱 실패: {e}")
            return []

    def _parse_item(self, item: dict, category: str) -> Optional[NewsItem]:
        """검색 결과를 NewsItem으로 변환"""
        try:
            # HTML 태그 제거
            title = BeautifulSoup(item.get("title", ""), "html.parser").get_text()
            description = BeautifulSoup(
                item.get("description", ""), "html.parser"
            ).get_text()

            # 날짜 파싱 (RFC 2822 형식)
            published_at = None
            pub_date = item.get("pubDate")
            if pub_date:
                try:
                    from email.utils import parsedate_to_datetime
                    published_at = parsedate_to_datetime(pub_date)
                except Exception:
                    pass

            return NewsItem(
                title=title.strip(),
                link=item.get("originallink") or item.get("link", ""),
                category=category,
                source=self.name,
                summary=description.strip()[:200],
                published_at=published_at
            )

        except Exception as e:
            logger.debug(f"검색 결과 파싱 실패: {e}")
            return None
