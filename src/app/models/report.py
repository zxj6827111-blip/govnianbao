from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel


class Report(BaseModel):
    id: str
    title: Optional[str] = None
    full_text: Optional[str] = None
    annual_struct: Optional[Dict[str, Any]] = None  # 年报解析后的结构
