from __future__ import annotations

from govnianbao import parse_annual_report_text_to_dict
from govnianbao.template_tables import TEMPLATE_TABLES


def _build_sample_report_text() -> str:
    table_def = TEMPLATE_TABLES["section3_applications"]
    value_rows = [row for row in table_def["rows"] if row.get("data", True)]
    value_cols = [col for col in table_def["columns"] if col.get("type") != "label"]
    numbers_needed = len(value_rows) * len(value_cols)
    table_numbers = " ".join(str(i) for i in range(1, numbers_needed + 1))

    # 在第一部分正文中夹杂页码，验证不会误判为标题。
    return f"""
一、总体情况
这里是年度报告的总体情况正文，包含若干描述性的文字。
- 1 -
继续描述总体情况，确保分段逻辑不会被页码打断。

二、主动公开政府信息情况
主动公开政府信息的说明与概况。

三、收到和处理政府信息公开申请情况
以下是表格数字：
{table_numbers}

四、政府信息公开行政复议、行政诉讼情况
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0

五、存在的主要问题及改进情况
这里记录主要问题与改进情况，文本应被完整保留。

六、其他需要报告的事项
这是其他需要报告的事项，确保能够被解析。
"""


def test_sections_text_and_tables_are_parsed():
    report_text = _build_sample_report_text()
    result = parse_annual_report_text_to_dict(report_text, with_tables=True)

    assert "总体情况" in result["section1"]["text"]
    assert "主要问题" in result["section5"]["text"]
    assert "其他需要报告" in result["section6"]["text"]

    tables = result["section3"]["tables"]
    assert "section3_applications" in tables

    cells = tables["section3_applications"]["cells"]
    assert cells  # 至少存在一张非空表格

    # 行数、列数应与模板一致
    data_rows = [row for row in TEMPLATE_TABLES["section3_applications"]["rows"] if row.get("data", True)]
    assert len(cells) == len(data_rows)
    # 任意单元格包含数字
    assert any(value is not None for row in cells.values() for value in row.values())
