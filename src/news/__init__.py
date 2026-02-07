"""뉴스 수집 모듈"""

from .collector import NewsCollector, NewsItem
from .formatter import NewsFormatter
from .sources import NaverNewsSource, GoogleNewsSource, BaseNewsSource

__all__ = [
    "NewsCollector",
    "NewsItem",
    "NewsFormatter",
    "NaverNewsSource",
    "GoogleNewsSource",
    "BaseNewsSource",
]
