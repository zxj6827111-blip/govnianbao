from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any

from .template_tables import SECTION_TITLES, TEMPLATE_TABLES


@dataclass
class Section1Overall:
    text: str = ""


@dataclass
class Section5Problems:
    text: str = ""


@dataclass
class Section6Other:
    text: str = ""


@dataclass
class Section2Tables:
    # 用 cells[row_key][col_key] 存数值
    tables: Dict[str, Dict[str, Dict[str, float]]] = field(
        default_factory=lambda: {
            key: {"cells": {}}
            for key, t in TEMPLATE_TABLES.items()
            if t["section"] == 2
        }
    )


@dataclass
class Section3Applications:
    tables: Dict[str, Dict[str, Dict[str, float]]] = field(
        default_factory=lambda: {
            key: {"cells": {}}
            for key, t in TEMPLATE_TABLES.items()
            if t["section"] == 3
        }
    )


@dataclass
class Section4ReviewLitigation:
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

    sections_title: Dict[int, str] = field(default_factory=lambda: SECTION_TITLES)

    section1: Section1Overall = field(default_factory=Section1Overall)
    section2: Section2Tables = field(default_factory=Section2Tables)
    section3: Section3Applications = field(default_factory=Section3Applications)
    section4: Section4ReviewLitigation = field(
        default_factory=Section4ReviewLitigation
    )
    section5: Section5Problems = field(default_factory=Section5Problems)
    section6: Section6Other = field(default_factory=Section6Other)
