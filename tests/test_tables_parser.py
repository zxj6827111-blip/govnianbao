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
    
    期望：系统应该识别这是 8 列格式的部分缺失，而不是 7 列格式。
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
    assert len(cells) == 24  # 应该识别为 24 行

    # 每一行都应该有 8 列
    for row_values in cells.values():
        # 应该包含 org_total 列（8 列的标志）
        assert "org_total" in row_values
        # 所有列都有值（对于有数据的行）
        assert all(v is not None for v in row_values.values())


def test_parse_template_table3_exact_formats():
    """
    测试精确格式匹配。
    
    验证：
    1. 175 个数字（25×7）→ 7 列格式
    2. 224 个数字（28×8）→ 8 列格式
    """
    # 测试 7 列格式（175 数字）
    numbers_7col = " ".join(str(i) for i in range(1, 176))
    raw_text_7col = f"三、标题\n{numbers_7col}"
    result_7col = parse_template_table3(raw_text_7col)
    
    assert len(result_7col["cells"]) == 25
    # 检查没有 org_total 列（7 列格式）
    first_row = list(result_7col["cells"].values())[0]
    assert "org_total" not in first_row
    assert "grand_total" in first_row
    
    # 测试 8 列格式（224 数字）
    numbers_8col = " ".join(str(i) for i in range(1, 225))
    raw_text_8col = f"三、标题\n{numbers_8col}"
    result_8col = parse_template_table3(raw_text_8col)
    
    assert len(result_8col["cells"]) == 28
    # 检查有 org_total 列（8 列格式）
    first_row = list(result_8col["cells"].values())[0]
    assert "org_total" in first_row
    assert "grand_total" in first_row

