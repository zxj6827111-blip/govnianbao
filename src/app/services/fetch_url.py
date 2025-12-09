from __future__ import annotations

import logging

from app.models.report import Report
from app.parse.annual_report import parse_annual_report_from_text
from app.services.report_repository import save_report

logger = logging.getLogger(__name__)


def handle_fetched_annual_report(full_text: str, report: Report) -> Report:
    """处理 URL 抓取到的年度报告文本并填充解析结果。"""

    try:
        annual_struct = parse_annual_report_from_text(full_text)
    except Exception:
        logger.exception("Failed to parse annual report text for report %s", report.id)
        annual_struct = None

    report.full_text = full_text
    report.annual_struct = annual_struct
    return save_report(report)
