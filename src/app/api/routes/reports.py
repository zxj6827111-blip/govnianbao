from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.report_repository import get_report


router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{report_id}/annual_struct")
def get_annual_struct(report_id: str):
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.annual_struct is None:
        raise HTTPException(status_code=404, detail="Annual report structure not available")

    return report.annual_struct
