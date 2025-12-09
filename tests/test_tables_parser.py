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

