from __future__ import annotations

from typing import Dict, Optional
import re

from .template_tables import SECTION_TITLES


def _normalize_text(raw_text: str) -> str:
    """规范化换行和空格，便于标题匹配。"""
    normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\u3000", " ")
    return normalized


def _build_relaxed_pattern(title: str) -> re.Pattern[str]:
    """生成允许标题字符间有空白的正则模式。"""
    escaped_chars = [re.escape(ch) for ch in title.strip()]
    pattern = r"\s*" + r"\s*".join(escaped_chars)
    return re.compile(pattern)


def split_sections(raw_text: str) -> Dict[int, str]:
    """
    根据固定标题，将整篇年度报告纯文本切成 6 段。

    输入：完整年报的纯文本（可能来自 PDF 抽取或者 URL 抓取）
    输出：一个字典 {section_index: text}
          - section_index: 1~6
          - text: 对应标题到下一个标题之间的原始文本（包含表格区域的文字）

    处理原则：
    - 使用标题中的“【一、】【二、】...”以及具体标题文字进行定位，
      标题列表即 SECTION_TITLES[1..6]
    - 标题可能前后有空格、换行或全角空格，需要做 strip + 宽松匹配
    - 若某个标题在文本中找不到，split_sections 仍然返回 6 个 key，
      且缺失部分的内容置为空字符串。
    """

    normalized_text = _normalize_text(raw_text)

    positions: Dict[int, Optional[int]] = {}
    for idx in range(1, 7):
        title = SECTION_TITLES[idx]
        pattern = _build_relaxed_pattern(title)
        match = pattern.search(normalized_text)
        positions[idx] = match.start() if match else None

    sections: Dict[int, str] = {}
    prev_end = 0

    for idx in range(1, 7):
        position = positions.get(idx)

        if position is None:
            start = prev_end
            end = start
            sections[idx] = ""
        else:
            start = position
            next_positions = [
                pos
                for later_idx, pos in positions.items()
                if later_idx > idx and pos is not None and pos > start
            ]
            end = min(next_positions) if next_positions else len(normalized_text)
            sections[idx] = normalized_text[start:end]

        prev_end = end

    return sections


def extract_section_text(raw_text: str, section_index: int) -> str:
    """
    便捷封装，从整篇文本中直接拿某一部分内容。
    """
    sections = split_sections(raw_text)
    return sections.get(section_index, "")
