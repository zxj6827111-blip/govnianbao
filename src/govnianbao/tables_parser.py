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
    解析第三部分"收到和处理政府信息公开申请情况"整张表。

    优先使用标准模板解析（parse_template_table3），
    若模板匹配失败再退回通用的 lenient 解析。
    """
    key = "section3_applications"
    table_def = TEMPLATE_TABLES[key]
    
    cells: Dict[str, Dict[str, float]] = {}
    warnings: List[str] = []

    # 1. 优先尝试标准模板解析
    try:
        tmpl_result = parse_template_table3(raw_text)
        cells_from_tmpl = tmpl_result.get("cells") if isinstance(tmpl_result, dict) else None
        
        if cells_from_tmpl and isinstance(cells_from_tmpl, dict) and len(cells_from_tmpl) > 0:
            cells = cells_from_tmpl
            logger.info(f"parse_section3_applications: successfully parsed {len(cells)} rows using template")
        else:
            warnings.append("parse_template_table3 returned empty or invalid cells")
    except Exception as e:
        logger.warning(f"parse_template_table3 failed: {e!r}")
        warnings.append(f"parse_template_table3 failed: {e!r}")

    # 2. 模板解析失败时，再用 lenient 兜底
    if not cells:
        logger.info("Falling back to lenient parsing for section3")
        nums = _extract_numbers(raw_text)
        cells2, used, warning = _fill_section3_lenient(nums, table_def)
        cells = cells2 or {}
        if warning:
            warnings.append(f"lenient parsing found {len(nums)} numbers, used {used}")

    result: Dict[str, Dict[str, Any]] = {key: {"cells": cells}}
    if warnings:
        result[key]["parse_warnings"] = warnings
    
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
    解析标准模板的第三张表格（支持多种格式）。

    支持的格式：
    1. 简化格式：25 行数据 × 7 列（不包含 org_total）= 175 个数字
    2. 完整格式：28 行数据 × 8 列（包含 org_total）= 224 个数字

    流程：
    1) 预清洗：丢弃页码行、去掉行首编号前缀
    2) 抽取所有整数
    3) 根据数字数量智能匹配格式
    4) 按行优先顺序填充 cells
    """

    # 预清洗文本
    cleaned_lines = []
    for line in raw_text.splitlines():
        if _PAGE_NUMBER_PATTERN.match(line):
            continue
        cleaned_lines.append(_LEADING_INDEX_PATTERN.sub("", line))

    cleaned_text = "\n".join(cleaned_lines)
    numbers = _TABLE3_NUMBER_PATTERN.findall(cleaned_text)
    int_numbers = [int(num) for num in numbers]
    num_count = len(int_numbers)

    # 定义支持的格式
    # 格式 1: 25 行数据 × 7 列（不包含 org_total，不包含标题行）
    # 格式 2: 28 行数据 × 8 列（包含 org_total，不包含标题行）
    
    # 获取模板定义的所有数据行（去掉标题行）
    table_def = TEMPLATE_TABLES["section3_applications"]
    all_data_rows = _data_rows(table_def)  # 28 行数据行
    
    # 判断是哪种格式
    if num_count == 175:  # 格式 1: 25 行 × 7 列
        num_rows = 25
        num_cols = 7
        col_keys = [
            "natural_person",
            "business_corp",
            "research_org",
            "social_org",
            "legal_service_org",
            "other_org",
            "grand_total",
        ]
        # 使用 25 行（去掉标题行 result_this_year_header）
        row_keys = [row["key"] for row in all_data_rows if row["key"] != "result_this_year_header"]
    elif num_count == 224:  # 格式 2: 28 行 × 8 列
        num_rows = 28
        num_cols = 8
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
        row_keys = [row["key"] for row in all_data_rows]
    else:
        # 数字数量不匹配任何标准格式，抛出异常让上层 fallback
        logger.warning(
            f"parse_template_table3: unexpected number count {num_count}, "
            f"expected 175 (25x7) or 224 (28x8)"
        )
        raise ValueError(
            f"parse_template_table3: got {num_count} numbers, expected 175 or 224"
        )

    logger.info(
        f"parse_template_table3: matched format {num_rows}x{num_cols}, "
        f"found {num_count} numbers"
    )

    # 按行优先顺序填充 cells
    cells: Dict[str, Dict[str, float]] = {}
    idx = 0
    
    for i in range(num_rows):
        row_key = row_keys[i]
        cells[row_key] = {}
        
        for col_key in col_keys:
            value = int_numbers[idx]
            cells[row_key][col_key] = float(value)
            idx += 1

    # 为了兼容旧测试，也返回 rows 格式
    return {
        "cells": cells,
        "rows": [
            {"key": row_key, "values": cells[row_key]}
            for row_key in row_keys[:num_rows]
        ]
    }
