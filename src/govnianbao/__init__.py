"""政府信息公开年度报告结构化解析工具包。"""

from .models import AnnualReport
from .template_tables import SECTION_TITLES, TEMPLATE_TABLES
from .text_parser import extract_section_text, split_sections

__all__ = [
    "AnnualReport",
    "SECTION_TITLES",
    "TEMPLATE_TABLES",
    "extract_section_text",
    "split_sections",
]
