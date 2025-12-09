from __future__ import annotations

import logging
import re
from typing import Dict, Any, List, Tuple

from .template_tables import TEMPLATE_TABLES

_NUM_PATTERN = re.compile(r"[+-]?\d+(?:\.\d+)?")
_PAGE_NUMBER_PATTERN = re.compile(r"^\s*-\s*\d+\s*-\s*$")
_LEADING_INDEX_PATTERN = re.compile(r"^[ \t]*\d+[\.、]")
_TABLE3_NUMBER_PATTERN = re.compile(r"\d+")

logger = logging.getLogger(__name__)

def _extract_numbers(raw_text: str) -> List[str]:
    """
    从原始文本中按出现顺序抽取所有数字（整数 / 小数）。
    会先去掉千分位逗号。
    """
    cleaned = raw_text.replace(",", "")
    return _NUM_PATTERN.findall(cleaned)


def _data_rows(table_def: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in table_def["rows"]:
        # 默认 data=True，只在标题行手动标 False
        if row.get("data", True):
            rows.append(row)
    return rows


def _value_columns(table_def: Dict[str, Any]) -> List[Dict[str, Any]]:
    cols: List[Dict[str, Any]] = []
    for col in table_def["columns"]:
        if col.get("type") != "label":
            cols.append(col)
    return cols


def _convert_token(token: str, col_type: str) -> float:
    if col_type == "float":
        return float(token)
    # 先转 float 再转 int，兼容“0.0”这类
    return int(float(token))


def _fill_one_table(
    numbers: List[str],
    table_key: str,
) -> Tuple[Dict[str, Dict[str, float]], List[str]]:
    """
    按模板定义的行列顺序，将 numbers 顺序填入表格。
    返回 (cells, remaining_numbers)：
      - cells: {row_key: {col_key: value}}
      - remaining_numbers: 剩余未使用的数字列表
    """
    table_def = TEMPLATE_TABLES[table_key]
    rows = _data_rows(table_def)
    cols = _value_columns(table_def)

    needed = len(rows) * len(cols)
    if len(numbers) < needed:
        raise ValueError(
            f"parse table {table_key} need {needed} numbers, "
            f"but only {len(numbers)} found."
        )

    used = numbers[:needed]
    remaining = numbers[needed:]

    cells: Dict[str, Dict[str, float]] = {}
    idx = 0
    for row in rows:
        rk = row["key"]
        cells[rk] = {}
        for col in cols:
            ck = col["key"]
            token = used[idx]
            idx += 1

            col_type = col.get("type", "int")
            cells[rk][ck] = _convert_token(token, col_type)

    return cells, remaining


def _fill_section3_lenient(
    numbers: List[str], table_def: Dict[str, Any]
) -> Tuple[Dict[str, Dict[str, float]], int, bool]:
    """
    以更宽松的方式填充第三部分的表格：
    - 若数字不足，未填充的单元格置为 None，并标记 warning；
    - 若数字过多，只取需要的数量，亦标记 warning。
    返回 (cells, used_count, warning)。
    """

    rows = _data_rows(table_def)
    cols = _value_columns(table_def)
    needed = len(rows) * len(cols)

    cells: Dict[str, Dict[str, float]] = {}
    warning = len(numbers) != needed

    idx = 0
    for row in rows:
        rk = row["key"]
        cells[rk] = {}
        for col in cols:
            if idx < len(numbers):
                token = numbers[idx]
                cells[rk][col["key"]] = _convert_token(token, col.get("type", "int"))
                idx += 1
            else:
                cells[rk][col["key"]] = None

    return cells, min(idx, needed), warning


def parse_section2_tables(raw_text: str) -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    解析第二部分的三个（严格说是四个）表格：
    - 第二十条第（一）项
    - 第二十条第（五）项
    - 第二十条第（六）项
    - 第二十条第（八）项

    假设：PDF/网页转换后的文本中，所有相关数字都是
    按 Word 表格“从上到下、从左到右”的顺序出现的。
    """
    nums = _extract_numbers(raw_text)
    result: Dict[str, Dict[str, Dict[str, float]]] = {}

    order = ["section2_art20_1", "section2_art20_5", "section2_art20_6", "section2_art20_8"]
    remaining = nums
    for key in order:
        cells, remaining = _fill_one_table(remaining, key)
        result[key] = {"cells": cells}

    return result


def parse_section3_applications(raw_text: str) -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    解析第三部分“收到和处理政府信息公开申请情况”整张表。

    优先使用标准模板解析（parse_template_table3），
    若模板匹配失败再退回通用的 lenient 解析。
    """
    key = "section3_applications"

    # 1. 先尝试标准模板解析（25 行 × 7 列）
    template_result = parse_template_table3(raw_text)
    rows = template_result.get("rows") if isinstance(template_result, dict) else None
    if rows:
        cells: Dict[str, Dict[str, float]] = {}
        for row in rows:
            row_key = row.get("key")
            values = row.get("values") or {}
            if not row_key:
                continue

            # 将标准模板解析结果转换为浮点数，保持与其他表格一致
            cells[row_key] = {col_key: float(value) for col_key, value in values.items()}

        return {key: {"cells": cells}}

    # 2. 兜底：旧的 lenient 逻辑（兼容非标准排版）
    nums = _extract_numbers(raw_text)
    table_def = TEMPLATE_TABLES[key]

    cells, used, warning = _fill_section3_lenient(nums, table_def)
    result: Dict[str, Dict[str, Any]] = {key: {"cells": cells}}
    if warning:
        result[key]["parse_warning"] = True
        result[key]["numbers_found"] = len(nums)
        result[key]["numbers_used"] = used

    return result



def parse_section4_review_litigation(raw_text: str) -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    解析第四部分“行政复议、行政诉讼情况”整张表。
    """
    nums = _extract_numbers(raw_text)
    key = "section4_review_litigation"
    cells, remaining = _fill_one_table(nums, key)
    return {key: {"cells": cells}}


def parse_template_table3(raw_text: str) -> Dict[str, Any]:
    """
    解析标准模板的第三张表格（25 行，每行 7 个数字）。

    流程：
    1) 预清洗：
       - 丢弃类似 "- 4 -" 的页码行；
       - 去掉行首编号前缀（如 "1."、"2、"）。
    2) 抽取所有整数并校验数量必须为 175（25x7）；
    3) 按固定行列顺序组装成结构化数据。
    """

    cleaned_lines = []
    for line in raw_text.splitlines():
        if _PAGE_NUMBER_PATTERN.match(line):
            continue
        cleaned_lines.append(_LEADING_INDEX_PATTERN.sub("", line))

    cleaned_text = "\n".join(cleaned_lines)
    numbers = _TABLE3_NUMBER_PATTERN.findall(cleaned_text)

    # 第三部分表格可能有多种格式：
    # 格式 1: 25 行 × 7 列 = 175 个数字（不包含 org_total 和 grand_total 列）
    # 格式 2: 29 行 × 8 列 = 232 个数字（包含所有列和行）
    # 格式 3: 25 行 × 8 列 = 200 个数字（不包含非数据行，但包含所有列）
    
    int_numbers = [int(num) for num in numbers]
    num_count = len(int_numbers)
    
    # 根据数字数量判断格式
    if num_count == 175:  # 格式 1: 25 行 × 7 列
        rows = [int_numbers[i * 7 : (i + 1) * 7] for i in range(25)]
        col_keys = [
            "natural_person",
            "business_corp",
            "research_org",
            "social_org",
            "legal_service_org",
            "other_org",
            "grand_total",  # 最后一列是总计
        ]
    elif num_count == 200:  # 格式 3: 25 行 × 8 列
        rows = [int_numbers[i * 8 : (i + 1) * 8] for i in range(25)]
        col_keys = [
            "natural_person",
            "business_corp",
            "research_org",
            "social_org",
            "legal_service_org",
            "other_org",
            "org_total",
            "grand_total",
        ]
    elif num_count == 232:  # 格式 2: 29 行 × 8 列
        rows = [int_numbers[i * 8 : (i + 1) * 8] for i in range(29)]
        col_keys = [
            "natural_person",
            "business_corp",
            "research_org",
            "social_org",
            "legal_service_org",
            "other_org",
            "org_total",
            "grand_total",
        ]
    else:
        logger.warning(
            "parse_template_table3 expected 175, 200, or 232 numbers but found %s", 
            num_count
        )
        return {}

    # 使用与模板定义一致的 row_keys（25 或 29 行）
    # 如果是 29 行，需要包含所有行；如果是 25 行，去掉标题行 result_this_year_header
    if len(rows) == 29:
        row_keys = [
            "new_requests",
            "carried_over",
            "result_this_year_header",  # 标题行
            "result_open",
            "result_partial",
            "result_not_public_total",
            "result_not_public_state_secret",
            "result_not_public_law_forbid",
            "result_not_public_security_stability",
            "result_not_public_third_party",
            "result_not_public_internal",
            "result_not_public_process",
            "result_not_public_case_file",
            "result_not_public_inquiry",
            "result_cannot_provide_total",
            "result_cannot_provide_not_held",
            "result_cannot_provide_need_create",
            "result_cannot_provide_unclear",
            "result_not_processed_total",
            "result_not_processed_petition",
            "result_not_processed_duplicate",
            "result_not_processed_publications",
            "result_not_processed_frequent",
            "result_not_processed_confirm_again",
            "result_other_total",
            "result_other_overdue_no_rectify",
            "result_other_no_pay_fee",
            "result_other_other",
            "result_total",
            "carry_next_year",
        ]
    else:  # 25 行
        row_keys = [
            "new_requests",
            "carried_over",
            "result_open",
            "result_partial",
            "result_not_public_total",
            "result_not_public_state_secret",
            "result_not_public_law_forbid",
            "result_not_public_security_stability",
            "result_not_public_third_party",
            "result_not_public_internal",
            "result_not_public_process",
            "result_not_public_case_file",
            "result_not_public_inquiry",
            "result_cannot_provide_total",
            "result_cannot_provide_not_held",
            "result_cannot_provide_need_create",
            "result_cannot_provide_unclear",
            "result_not_processed_total",
            "result_not_processed_petition",
            "result_not_processed_duplicate",
            "result_not_processed_publications",
            "result_not_processed_frequent",
            "result_not_processed_confirm_again",
            "result_other_total",
            "result_other_overdue_no_rectify",
            "result_other_no_pay_fee",
            "result_other_other",
            "result_total",
            "carry_next_year",
        ]

    return {
        "rows": [
            {"key": row_keys[i], "values": dict(zip(col_keys, row_numbers))}
            for i, row_numbers in enumerate(rows)
        ]
    }
