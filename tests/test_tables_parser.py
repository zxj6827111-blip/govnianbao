from __future__ import annotations

from govnianbao.tables_parser import (
    parse_section3_applications,
    parse_template_table3,
)


def test_parse_section3_applications_prefers_template():
    # 构造标准模板数量的数字（25 行 × 7 列 = 175 个）
    numbers = " ".join(str(i) for i in range(1, 176))
    raw_text = "\n".join(
        [
            "三、收到和处理政府信息公开申请情况",
            "- 1 -",  # 模拟页码行，确保被忽略
            numbers,
        ]
    )

    result = parse_section3_applications(raw_text)
    cells = result["section3_applications"]["cells"]

    assert cells  # 解析结果不应为空

    # 行数应与标准模板一致
    template_rows = parse_template_table3(raw_text)["rows"]
    assert len(cells) == len(template_rows)

    # 每一行都包含关键列，且为浮点数
    for row_values in cells.values():
        for key in ("natural_person", "business_corp", "grand_total"):
            assert key in row_values
            assert isinstance(row_values[key], float)


def test_parse_section3_handles_partial_missing_rows():
    """
    测试缺失行的处理能力。
    
    场景：PDF 提取了 192 个数字（24行×8列），而不是完整的 224 个。
    这对应于表格末尾缺少了 4 行（比如说某些分项没有被识别）。
    
    期望：系统应该识别这是 8 列格式的部分缺失，并返回完整的 29 行
    （包括缺失的 4 个总计行，它们会被自动计算）。
    """
    # 构造 24 行 × 8 列 = 192 个数字（缺少最后 4 行）
    numbers = " ".join(str(i) for i in range(1, 193))
    raw_text = "\n".join(
        [
            "三、收到和处理政府信息公开申请情况",
            "- 1 -",  # 模拟页码行
            numbers,
        ]
    )

    result = parse_section3_applications(raw_text)
    cells = result["section3_applications"]["cells"]

    assert cells  # 解析结果不应为空
    assert len(cells) == 29  # 应该返回完整的 29 行（包括 4 个计算出来的总计行）

    # 检查关键总计行存在
    totals = [
        'result_not_public_total',
        'result_cannot_provide_total',
        'result_not_processed_total',
        'result_other_total',
    ]
    for total_key in totals:
        assert total_key in cells, f"缺失总计行: {total_key}"
        row_values = cells[total_key]
        # 总计行应该有数值
        assert any(isinstance(v, (int, float)) and v > 0 for v in row_values.values()),\
            f"总计行 {total_key} 应该有非零值"


def test_parse_template_table3_exact_formats():
    """
    测试精确格式匹配。
    
    验证：
    1. 175 个数字（25×7）→ 7 列格式，返回 29 行（含 4 个计算的总计行）
    2. 224 个数字（28×8）→ 8 列格式，返回 29 行（含 4 个计算的总计行）
    """
    # 测试 7 列格式（175 数字）
    numbers_7col = " ".join(str(i) for i in range(1, 176))
    raw_text_7col = f"三、标题\n{numbers_7col}"
    result_7col = parse_template_table3(raw_text_7col)
    
    # 新实现总是返回 29 行（所有可能的行）
    assert len(result_7col["cells"]) == 29
    assert len(result_7col["rows"]) == 29
    
    # 检查没有 org_total 列（7 列格式）
    first_row = list(result_7col["cells"].values())[0]
    assert "org_total" not in first_row
    assert "grand_total" in first_row
    
    # 检查 4 个总计行存在并有值
    totals = [
        'result_not_public_total',
        'result_cannot_provide_total',
        'result_not_processed_total',
        'result_other_total',
    ]
    for total_key in totals:
        assert total_key in result_7col["cells"]
        assert any(v > 0 for v in result_7col["cells"][total_key].values())
    
    # 测试 8 列格式（224 数字）
    numbers_8col = " ".join(str(i) for i in range(1, 225))
    raw_text_8col = f"三、标题\n{numbers_8col}"
    result_8col = parse_template_table3(raw_text_8col)
    
    # 8 列格式：28 行数据，但返回 29 行（少一个总计行，或缺失一行）
    # 实际上，224 = 28×8，所以会识别为 8 列，返回完整的 29 行
    assert len(result_8col["cells"]) == 29
    
    # 检查有 org_total 列（8 列格式）
    first_row = list(result_8col["cells"].values())[0]
    assert "org_total" in first_row
    assert "grand_total" in first_row

