from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from .template_tables import SECTION_TITLES, TEMPLATE_TABLES


@dataclass
class Section1Overall:
    # 第一部分：总体情况（纯文字）
    text: str = ""


@dataclass
class Section5Problems:
    # 第五部分：存在的主要问题及改进情况（纯文字）
    text: str = ""


@dataclass
class Section6Other:
    # 第六部分：其他需要报告的事项（纯文字）
    text: str = ""


@dataclass
class Section2Tables:
    # 第二部分：主动公开政府信息情况
    # raw_text 用来保存这一部分的原始文本（包括表格附近文字）
    raw_text: str = ""
    # tables 按模板定义好的表格结构，只存数字单元格
    tables: Dict[str, Dict[str, Dict[str, float]]] = field(
        default_factory=lambda: {
            key: {"cells": {}}  # cells[row_key][col_key] = 数值
            for key, t in TEMPLATE_TABLES.items()
            if t["section"] == 2
        }
    )


@dataclass
class Section3Applications:
    # 第三部分：收到和处理政府信息公开申请情况
    raw_text: str = ""
    tables: Dict[str, Dict[str, Dict[str, float]]] = field(
        default_factory=lambda: {
            key: {"cells": {}}
            for key, t in TEMPLATE_TABLES.items()
            if t["section"] == 3
        }
    )


@dataclass
class Section4ReviewLitigation:
    # 第四部分：行政复议、行政诉讼情况
    raw_text: str = ""
    tables: Dict[str, Dict[str, Dict[str, float]]] = field(
        default_factory=lambda: {
            key: {"cells": {}}
            for key, t in TEMPLATE_TABLES.items()
            if t["section"] == 4
        }
    )


@dataclass
class AnnualReport:
    """统一的“结构化年报”数据模型。"""

    # 6 个板块标题
    sections_title: Dict[int, str] = field(
        default_factory=lambda: SECTION_TITLES.copy()
    )

    section1: Section1Overall = field(default_factory=Section1Overall)
    section2: Section2Tables = field(default_factory=Section2Tables)
    section3: Section3Applications = field(default_factory=Section3Applications)
    section4: Section4ReviewLitigation = field(
        default_factory=Section4ReviewLitigation
    )
    section5: Section5Problems = field(default_factory=Section5Problems)
    section6: Section6Other = field(default_factory=Section6Other)
