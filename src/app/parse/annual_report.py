from __future__ import annotations

from typing import Any, Dict

from govnianbao import parse_annual_report_text_to_dict


def parse_annual_report_from_text(full_text: str) -> Dict[str, Any]:
    """
    输入：整篇年度报告的纯文本（来自 PDF/URL 抽取）
    输出：govnianbao 返回的结构化 dict：
      {
        "sections_title": {...},
        "section1": {"text": "..."},
        "section2": {
            "raw_text": "...",
            "tables": {
                "section2_art20_1": {"cells": {...}},
                ...
            },
        },
        "section3": {...},
        "section4": {...},
        "section5": {"text": "..."},
        "section6": {"text": "..."},
      }
    """
    return parse_annual_report_text_to_dict(full_text, with_tables=True)
