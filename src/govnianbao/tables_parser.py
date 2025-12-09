from __future__ import annotations

import re
from typing import Dict, Any, List, Tuple

from .template_tables import TEMPLATE_TABLES

_NUM_PATTERN = re.compile(r"[-+]?\d+(?:\.\d+)?")

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
            if col_type == "float":
                value = float(token)
            else:
                # 先转 float 再转 int，兼容“0.0”这类
                value = int(float(token))
            cells[rk][ck] = value

    return cells, remaining


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
    """
    nums = _extract_numbers(raw_text)
    key = "section3_applications"
    cells, remaining = _fill_one_table(nums, key)
    # 对于这一张表，允许尾部有一些无关数字（remaining），先忽略
    return {key: {"cells": cells}}


def parse_section4_review_litigation(raw_text: str) -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    解析第四部分“行政复议、行政诉讼情况”整张表。
    """
    nums = _extract_numbers(raw_text)
    key = "section4_review_litigation"
    cells, remaining = _fill_one_table(nums, key)
    return {key: {"cells": cells}}
