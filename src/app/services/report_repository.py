from __future__ import annotations

from typing import Dict, Optional

from app.models.report import Report


_REPORT_STORE: Dict[str, Report] = {}


def save_report(report: Report) -> Report:
    _REPORT_STORE[report.id] = report
    return report


def get_report(report_id: str) -> Optional[Report]:
    return _REPORT_STORE.get(report_id)
