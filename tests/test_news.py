"""뉴스 모듈 테스트"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from src.news.collector import NewsItem, NewsCollector
from src.news.formatter import NewsFormatter
from src.news.sources import NaverNewsSource, GoogleNewsSource
from src.config import NewsConfig, CategoryConfig, SourceConfig


class TestNewsItem:
    """NewsItem 테스트"""

    def test_create_news_item(self):
        """뉴스 아이템 생성"""
        item = NewsItem(
            title="테스트 뉴스",
            link="https://example.com/news/1",
            category="society",
            source="naver"
        )

        assert item.title == "테스트 뉴스"
        assert item.category == "society"
        assert item.source == "naver"

    def test_news_item_equality(self):
        """같은 링크의 뉴스는 동일"""
        item1 = NewsItem(
            title="뉴스 1",
            link="https://example.com/news/1",
            category="society",
            source="naver"
        )
        item2 = NewsItem(
            title="뉴스 1 (다른 제목)",
            link="https://example.com/news/1",
            category="economy",
            source="google"
        )

        assert item1 == item2
        assert hash(item1) == hash(item2)

    def test_news_item_uniqueness_in_set(self):
        """중복 링크 제거"""
        items = [
            NewsItem(title="뉴스1", link="https://a.com/1", category="society", source="naver"),
            NewsItem(title="뉴스2", link="https://a.com/1", category="society", source="google"),
            NewsItem(title="뉴스3", link="https://a.com/2", category="society", source="naver"),
        ]

        unique = list(set(items))
        assert len(unique) == 2


class TestNewsFormatter:
    """NewsFormatter 테스트"""

    @pytest.fixture
    def sample_news(self):
        return {
            "society": [
                NewsItem(
                    title="사회 뉴스 1",
                    link="https://example.com/1",
                    category="society",
                    source="naver",
                    summary="사회 뉴스 요약입니다.",
                    published_at=datetime.now()
                ),
            ],
            "economy": [
                NewsItem(
                    title="경제 뉴스 1",
                    link="https://example.com/2",
                    category="economy",
                    source="google",
                    summary="경제 뉴스 요약입니다."
                ),
            ],
        }

    def test_format_plain(self, sample_news):
        """일반 텍스트 포맷"""
        formatter = NewsFormatter(format_type="plain")
        message = formatter.format(sample_news)

        assert "오늘의 뉴스 브리핑" in message
        assert "사회" in message
        assert "경제" in message
        assert "사회 뉴스 1" in message
        assert "경제 뉴스 1" in message

    def test_format_without_summary(self, sample_news):
        """요약 없이 포맷"""
        formatter = NewsFormatter(include_summary=False)
        message = formatter.format(sample_news)

        assert "사회 뉴스 1" in message
        assert "사회 뉴스 요약" not in message

    def test_format_without_link(self, sample_news):
        """링크 없이 포맷"""
        formatter = NewsFormatter(include_link=False)
        message = formatter.format(sample_news)

        assert "사회 뉴스 1" in message
        assert "https://example.com" not in message


class TestNewsCollector:
    """NewsCollector 테스트"""

    @pytest.fixture
    def config(self):
        return NewsConfig(
            categories={
                "society": CategoryConfig(enabled=True, max_items=3),
                "economy": CategoryConfig(enabled=True, max_items=3),
            },
            sources={
                "naver": SourceConfig(enabled=True),
                "google": SourceConfig(enabled=True),
            }
        )

    @pytest.fixture
    def mock_source(self):
        source = MagicMock()
        source.name = "mock"
        source.fetch_news = AsyncMock(return_value=[
            NewsItem(
                title="Mock 뉴스 1",
                link="https://mock.com/1",
                category="society",
                source="mock"
            ),
            NewsItem(
                title="Mock 뉴스 2",
                link="https://mock.com/2",
                category="society",
                source="mock"
            ),
        ])
        return source

    @pytest.mark.asyncio
    async def test_collect_all(self, config, mock_source):
        """뉴스 수집"""
        collector = NewsCollector(config)
        collector.register_source(mock_source)

        result = await collector.collect_all()

        assert "society" in result
        assert len(result["society"]) <= 3

    @pytest.mark.asyncio
    async def test_collect_respects_max_items(self, config, mock_source):
        """max_items 설정 준수"""
        mock_source.fetch_news = AsyncMock(return_value=[
            NewsItem(title=f"뉴스 {i}", link=f"https://test.com/{i}",
                     category="society", source="mock")
            for i in range(10)
        ])

        collector = NewsCollector(config)
        collector.register_source(mock_source)

        result = await collector.collect_all()

        assert len(result["society"]) == 3  # max_items=3


class TestNaverNewsSource:
    """NaverNewsSource 테스트"""

    def test_category_map(self):
        """카테고리 매핑 확인"""
        source = NaverNewsSource()

        assert "society" in source.CATEGORY_MAP
        assert "economy" in source.CATEGORY_MAP

    @pytest.mark.asyncio
    async def test_unsupported_category(self):
        """지원하지 않는 카테고리"""
        source = NaverNewsSource()
        result = await source.fetch_news("unknown_category", 5)

        assert result == []


class TestGoogleNewsSource:
    """GoogleNewsSource 테스트"""

    def test_category_config(self):
        """카테고리 설정 확인"""
        source = GoogleNewsSource()

        assert "society" in source.CATEGORY_CONFIG
        assert "economy" in source.CATEGORY_CONFIG

    @pytest.mark.asyncio
    async def test_unsupported_category(self):
        """지원하지 않는 카테고리"""
        source = GoogleNewsSource()
        result = await source.fetch_news("unknown_category", 5)

        assert result == []
