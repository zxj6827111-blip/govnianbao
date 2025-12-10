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
    增强预清洗：移除跨页的页码标记（如 "- 4 -"）
    """
    # 【增强预清洗】移除页码标记（跨页时会出现 "- 4 -" 这样的标记）
    cleaned_lines = []
    for line in raw_text.splitlines():
        # 跳过整行页码
        if _PAGE_NUMBER_PATTERN.match(line):
            continue
        cleaned_lines.append(line)
    
    cleaned_text = "\n".join(cleaned_lines)
    nums = _extract_numbers(cleaned_text)
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

    表格层级结构：
    - 第 1 级（一、二、三、四）：大标题
    - 第 2 级（（一）、（二）、（三）等）：分类标题 ← data=False，不填数值
    - 第 3 级（1.、2.、3. 等）：最小数据行 ← data=True，填数值

    支持的格式：
    1. 标准格式：25 行最小级数据 × 7 列 = 175 个数字
       （即第 3 级的行：new_requests、carried_over、result_open、result_partial、
        8个不予公开子项、3个无法提供子项、5个不予处理子项、3个其他处理子项、result_total、carry_next_year）
    2. 完整格式：25 行最小级数据 × 8 列（包含 org_total）= 200 个数字

    关键点：
    - PDF 中不存在第 2 级的分类标题行（（三）、（四）、（五）、（六））的数据
    - 这些分类标题行在模板中 data=False，不应该填数值
    - 只提取 data=True 的行，即第 1 级和第 3 级的行
    """

    # 【增强预清洗】移除行内页码（如 -5-）和行序号（如 1.、2、）
    cleaned_lines = []
    for line in raw_text.splitlines():
        # 整行页码过滤
        if _PAGE_NUMBER_PATTERN.match(line):
            continue
        
        # 移除行内的页码片段（如 -5-）
        line = re.sub(r"-\s*\d+\s*-", " ", line)
        
        # 移除行内的小条序号（1.、2、3.等）
        line = re.sub(r"(?<!\d)([1-9])[\.、]", " ", line)
        
        # 移除行首的编号前缀
        line = _LEADING_INDEX_PATTERN.sub("", line)
        
        cleaned_lines.append(line)

    cleaned_text = "\n".join(cleaned_lines)
    numbers = _TABLE3_NUMBER_PATTERN.findall(cleaned_text)
    int_numbers = [int(num) for num in numbers]
    num_count = len(int_numbers)

    # 获取模板定义的所有 data=True 的行（即应该填数值的行）
    table_def = TEMPLATE_TABLES["section3_applications"]
    all_data_rows = _data_rows(table_def)
    row_keys = [row["key"] for row in all_data_rows]
    
    # 定义两种可能的列配置
    col_keys_7 = [
        "natural_person",
        "business_corp",
        "research_org",
        "social_org",
        "legal_service_org",
        "other_org",
        "grand_total",
    ]
    col_keys_8 = [
        "natural_person",
        "business_corp",
        "research_org",
        "social_org",
        "legal_service_org",
        "other_org",
        "org_total",
        "grand_total",
    ]
    
    # 计算期望值
    expected_count_7 = len(row_keys) * len(col_keys_7)  # 25*7=175
    expected_count_8 = len(row_keys) * len(col_keys_8)  # 25*8=200
    
    # 【智能匹配逻辑】
    col_keys = None
    
    if num_count == expected_count_7:
        # 25 行 × 7 列数字
        col_keys = col_keys_7
        logger.info(f"parse_template_table3: matched 7-column format with 25 data rows (175 numbers)")
    
    elif num_count == expected_count_8:
        # 25 行 × 8 列数字
        col_keys = col_keys_8
        logger.info(f"parse_template_table3: matched 8-column format with 25 data rows (200 numbers)")
    
    else:
        # 【推断逻辑】尝试按 7 或 8 列整除
        if num_count % 7 == 0:
            col_keys = col_keys_7
            inferred_rows = num_count // 7
            logger.info(
                f"parse_template_table3: inferred 7-column format with {inferred_rows} rows "
                f"(found {num_count} numbers)"
            )
            # 只取前 inferred_rows 行
            row_keys = row_keys[:inferred_rows]
        elif num_count % 8 == 0:
            col_keys = col_keys_8
            inferred_rows = num_count // 8
            logger.info(
                f"parse_template_table3: inferred 8-column format with {inferred_rows} rows "
                f"(found {num_count} numbers)"
            )
            # 只取前 inferred_rows 行
            row_keys = row_keys[:inferred_rows]
        else:
            logger.warning(
                f"parse_template_table3: unexpected number count {num_count}, "
                f"expected {expected_count_7} (25x7) or {expected_count_8} (25x8)"
            )
            raise ValueError(
                f"parse_template_table3: got {num_count} numbers, "
                f"expected {expected_count_7} or {expected_count_8}"
            )

    # 【填充 cells】
    cells: Dict[str, Dict[str, float]] = {rk: {} for rk in row_keys}
    idx = 0
    
    # 按行按列填充数字
    for row_key in row_keys:
        for col_key in col_keys:
            if idx < len(int_numbers):
                value = int_numbers[idx]
                cells[row_key][col_key] = float(value)
                idx += 1
            else:
                cells[row_key][col_key] = None

    logger.info(
        f"parse_template_table3: filled {len(row_keys)} rows × {len(col_keys)} cols, "
        f"{len([v for row in cells.values() for v in row.values() if v])} non-zero values"
    )

    # 为了兼容旧测试，也返回 rows 格式
    return {
        "cells": cells,
        "rows": [
            {"key": row_key, "values": cells[row_key]}
            for row_key in row_keys
        ]
    }
