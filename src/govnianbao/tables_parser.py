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
    解析标准模板的第三张表格（支持多种格式，包括部分缺失情况）。

    支持的格式：
    1. 简化格式：N 行数据 × 7 列（不包含 org_total）= N*7 个数字
    2. 完整格式：N 行数据 × 8 列（包含 org_total）= N*8 个数字
    3. 部分缺失格式：少于 224 但接近 224 的数字（如 192 = 24×8）
       可能是表格末尾某些行缺失

    流程：
    1) 预清洗：丢弃页码行、去掉行首编号前缀
    2) 抽取所有整数
    3) 根据数字数量智能匹配格式
       - 精确匹配 175 或 224
       - 或推断是哪种列格式（7 或 8）
       - 对于 8 列格式的部分缺失，尝试补全
    4) 按行优先顺序填充 cells，缺失部分留 None
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

    # 获取模板定义的所有数据行（去掉标题行）
    table_def = TEMPLATE_TABLES["section3_applications"]
    all_data_rows = _data_rows(table_def)  # 所有数据行
    
    # 定义两种可能的列配置
    # 格式 1: 7 列（不包含 org_total）
    col_keys_7 = [
        "natural_person",
        "business_corp",
        "research_org",
        "social_org",
        "legal_service_org",
        "other_org",
        "grand_total",
    ]
    # 格式 2: 8 列（包含 org_total）
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
    
    # 尝试匹配格式
    # 注意：由于 result_this_year_header 是标题行（data=False），all_data_rows 中不包含它
    all_row_keys = [row["key"] for row in all_data_rows]
    
    # 计算动态期望值
    expected_count_7 = len(all_row_keys) * len(col_keys_7)
    expected_count_8 = len(all_row_keys) * len(col_keys_8)
    
    # 【改进】智能格式推断逻辑
    col_keys = None
    row_keys = None
    is_partial_8col = False  # 标记是否是 8 列的部分缺失情况
    
    if num_count == expected_count_7:  # 格式 1: 精确匹配 25 行 × 7 列
        col_keys = col_keys_7
        row_keys = all_row_keys
        logger.info(f"parse_template_table3: matched exact 7-column format (25x7=175)")
    
    elif num_count == expected_count_8:  # 格式 2: 精确匹配 28 行 × 8 列
        col_keys = col_keys_8
        row_keys = all_row_keys
        logger.info(f"parse_template_table3: matched exact 8-column format (28x8=224)")
    
    else:
        # 【学习机制】如果不是完全匹配，尝试推断格式
        # 首先检查是否能被 8 整除（8 列格式）
        if num_count % 8 == 0:
            inferred_rows = num_count // 8
            col_keys = col_keys_8
            
            # 【关键改进】对于 8 列格式的部分缺失
            # 如果行数接近 28（比如 24-27 行），认为是表格末尾缺失
            if inferred_rows >= 20:  # 保守估计，至少 20 行说明是 8 列格式
                is_partial_8col = True
                # 使用前 inferred_rows 行，后续的行留 None
                row_keys = all_row_keys[:inferred_rows]
                logger.info(
                    f"parse_template_table3: inferred 8-column partial format with {inferred_rows} rows "
                    f"(found {num_count} numbers, expected {expected_count_8})"
                )
            else:
                # 行数太少，不认为是 8 列格式的部分缺失
                col_keys = None
        
        # 【备选方案】如果不是 8 列格式，尝试 7 列格式
        if col_keys is None and num_count % 7 == 0:
            inferred_rows = num_count // 7
            col_keys = col_keys_7
            row_keys = all_row_keys[:inferred_rows]
            logger.info(
                f"parse_template_table3: inferred 7-column format with {inferred_rows} rows "
                f"(found {num_count} numbers)"
            )
        
        # 【最后方案】如果都不能整除，抛出异常
        if col_keys is None:
            logger.warning(
                f"parse_template_table3: unexpected number count {num_count}, "
                f"expected {expected_count_7} (25x7) or {expected_count_8} (28x8), "
                f"or a multiple of 7 or 8"
            )
            raise ValueError(
                f"parse_template_table3: got {num_count} numbers, "
                f"expected {expected_count_7} (25x7) or {expected_count_8} (28x8), "
                f"or a multiple of 7 or 8"
            )

    num_rows = len(row_keys)
    num_cols = len(col_keys)
    logger.info(
        f"parse_template_table3: matched format {num_rows}x{num_cols}, "
        f"found {num_count} numbers{'（部分缺失）' if is_partial_8col else ''}"
    )

    # 按行优先顺序填充 cells
    cells: Dict[str, Dict[str, float]] = {}
    idx = 0
    
    for i in range(num_rows):
        row_key = row_keys[i]
        cells[row_key] = {}
        
        for col_key in col_keys:
            if idx < len(int_numbers):  # 有数据时填充
                value = int_numbers[idx]
                cells[row_key][col_key] = float(value)
                idx += 1
            else:  # 数据不足时留 None（用于部分缺失的情况）
                cells[row_key][col_key] = None

    # 为了兼容旧测试，也返回 rows 格式
    return {
        "cells": cells,
        "rows": [
            {"key": row_key, "values": cells[row_key]}
            for row_key in row_keys
        ]
    }
