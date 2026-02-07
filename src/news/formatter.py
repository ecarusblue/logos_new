"""뉴스 메시지 포맷터"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from .collector import NewsItem


logger = logging.getLogger(__name__)


class NewsFormatter:
    """뉴스 메시지 포맷터"""

    # 카테고리 이모지 및 한글명
    CATEGORY_INFO = {
        "society": ("📌", "사회"),
        "economy": ("💰", "경제"),
        "politics": ("🏛️", "정치"),
        "world": ("🌍", "국제"),
        "culture": ("🎭", "문화"),
        "tech": ("💻", "IT/과학"),
    }

    # 소스 이모지 및 한글명
    SOURCE_INFO = {
        "naver": ("🟢", "네이버 뉴스"),
        "google": ("🔵", "구글 뉴스"),
    }

    def __init__(
        self,
        include_summary: bool = True,
        include_link: bool = True,
        format_type: str = "plain"
    ):
        """
        Args:
            include_summary: 요약 포함 여부
            include_link: 링크 포함 여부
            format_type: 포맷 타입 (plain, markdown, html)
        """
        self.include_summary = include_summary
        self.include_link = include_link
        self.format_type = format_type

    def format(
        self,
        news_by_category: dict[str, list[NewsItem]],
        source_name: Optional[str] = None
    ) -> str:
        """뉴스를 메시지로 포맷팅

        Args:
            news_by_category: 카테고리별 뉴스
            source_name: 뉴스 소스명 (None이면 통합)

        Returns:
            포맷팅된 메시지
        """
        if self.format_type == "markdown":
            return self._format_markdown(news_by_category, source_name)
        elif self.format_type == "html":
            return self._format_html(news_by_category, source_name)
        else:
            return self._format_plain(news_by_category, source_name)

    def _get_header(self) -> tuple[str, str]:
        """헤더 생성"""
        now = datetime.now()
        date_str = now.strftime("%Y년 %m월 %d일")
        weekday = ["월", "화", "수", "목", "금", "토", "일"][now.weekday()]
        return date_str, weekday

    def _format_plain(
        self,
        news_by_category: dict[str, list[NewsItem]],
        source_name: Optional[str] = None
    ) -> str:
        """일반 텍스트 포맷"""
        date_str, weekday = self._get_header()

        # 소스명이 있으면 헤더에 표시
        if source_name:
            emoji, source_ko = self.SOURCE_INFO.get(source_name, ("📰", source_name))
            lines = [
                f"{emoji} {source_ko}",
                f"{date_str} ({weekday})",
                "",
            ]
        else:
            lines = [
                "📰 오늘의 뉴스 브리핑",
                f"{date_str} ({weekday})",
                "",
            ]

        for cat_name, news_items in news_by_category.items():
            if not news_items:
                continue

            emoji, cat_ko = self.CATEGORY_INFO.get(cat_name, ("📋", cat_name))
            lines.append(f"{emoji} {cat_ko}")
            lines.append("─" * 20)

            for i, item in enumerate(news_items, 1):
                lines.append(f"{i}. {item.title}")

                if self.include_summary and item.summary:
                    summary = item.summary[:80]
                    if len(item.summary) > 80:
                        summary += "..."
                    lines.append(f"   {summary}")

                if self.include_link:
                    lines.append(f"   🔗 {item.link}")

                lines.append("")

            lines.append("")

        return "\n".join(lines)

    def _format_markdown(
        self,
        news_by_category: dict[str, list[NewsItem]],
        source_name: Optional[str] = None
    ) -> str:
        """마크다운 포맷 (텔레그램 MarkdownV2용)"""
        date_str, weekday = self._get_header()

        if source_name:
            emoji, source_ko = self.SOURCE_INFO.get(source_name, ("📰", source_name))
            lines = [
                f"*{emoji} {source_ko}*",
                f"_{date_str} \\({weekday}\\)_",
                "",
            ]
        else:
            lines = [
                "*📰 오늘의 뉴스 브리핑*",
                f"_{date_str} \\({weekday}\\)_",
                "",
            ]

        for cat_name, news_items in news_by_category.items():
            if not news_items:
                continue

            emoji, cat_ko = self.CATEGORY_INFO.get(cat_name, ("📋", cat_name))
            lines.append(f"*{emoji} {cat_ko}*")
            lines.append("")

            for i, item in enumerate(news_items, 1):
                # MarkdownV2 이스케이프
                title = self._escape_markdown(item.title)
                lines.append(f"{i}\\. {title}")

                if self.include_summary and item.summary:
                    summary = self._escape_markdown(item.summary[:80])
                    if len(item.summary) > 80:
                        summary += "\\.\\.\\."
                    lines.append(f"   _{summary}_")

                if self.include_link:
                    lines.append(f"   [원문 보기]({item.link})")

                lines.append("")

            lines.append("")

        return "\n".join(lines)

    def _format_html(
        self,
        news_by_category: dict[str, list[NewsItem]],
        source_name: Optional[str] = None
    ) -> str:
        """HTML 포맷"""
        date_str, weekday = self._get_header()

        if source_name:
            emoji, source_ko = self.SOURCE_INFO.get(source_name, ("📰", source_name))
            lines = [
                f"<b>{emoji} {source_ko}</b>",
                f"<i>{date_str} ({weekday})</i>",
                "",
            ]
        else:
            lines = [
                "<b>📰 오늘의 뉴스 브리핑</b>",
                f"<i>{date_str} ({weekday})</i>",
                "",
            ]

        for cat_name, news_items in news_by_category.items():
            if not news_items:
                continue

            emoji, cat_ko = self.CATEGORY_INFO.get(cat_name, ("📋", cat_name))
            lines.append(f"<b>{emoji} {cat_ko}</b>")
            lines.append("")

            for i, item in enumerate(news_items, 1):
                title = self._escape_html(item.title)
                lines.append(f"{i}. {title}")

                if self.include_summary and item.summary:
                    summary = self._escape_html(item.summary[:80])
                    if len(item.summary) > 80:
                        summary += "..."
                    lines.append(f"   <i>{summary}</i>")

                if self.include_link:
                    lines.append(f'   <a href="{item.link}">원문 보기</a>')

                lines.append("")

            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _escape_markdown(text: str) -> str:
        """MarkdownV2 특수문자 이스케이프"""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#',
                         '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f"\\{char}")
        return text

    @staticmethod
    def _escape_html(text: str) -> str:
        """HTML 특수문자 이스케이프"""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))
