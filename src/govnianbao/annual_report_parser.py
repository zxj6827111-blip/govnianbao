from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict

from .models import AnnualReport
from .text_parser import split_sections
from .tables_parser import (
    parse_section2_tables,
    parse_section3_applications,
    parse_section4_review_litigation,
)


def parse_annual_report_text(raw_text: str, *, with_tables: bool = True) -> AnnualReport:
    """
    将整篇年度报告纯文本解析成 AnnualReport 结构。

    当前版本步骤：
    1. 使用 split_sections 按标题切成 6 段；
    2. 把每一段原文填入 AnnualReport：
       - 第一、五、六部分：写入 section.text；
       - 第二、三、四部分：写入 section.raw_text；
    3. 如果 with_tables=True，再尝试从第二～四部分的文本中
       按模板顺序抽取数字，填入对应表格 cells。
       （若数字数量不匹配会在内部吞掉异常，保持空表）
    """
    sections = split_sections(raw_text)
    report = AnnualReport()

    # 1,5,6 纯文字
    report.section1.text = sections.get(1, "").strip()
    report.section5.text = sections.get(5, "").strip()
    report.section6.text = sections.get(6, "").strip()

    # 2,3,4 文本 + 表格
    report.section2.raw_text = sections.get(2, "").strip()
    report.section3.raw_text = sections.get(3, "").strip()
    report.section4.raw_text = sections.get(4, "").strip()

    if with_tables:
        _fill_tables_best_effort(report)

    return report


def _fill_tables_best_effort(report: AnnualReport) -> None:
    """
    尝试解析第二～四部分表格。
    - 若数字数量完全匹配模板，则填入 cells；
    - 若不匹配，则保持原有空表，不抛异常（方便先跑通主流程）。
    将来如果你希望严格校验，可以直接调用 tables_parser 里的函数。
    """
    # 第二部分
    try:
        if report.section2.raw_text.strip():
            parsed = parse_section2_tables(report.section2.raw_text)
            report.section2.tables.update(parsed)
    except Exception:
        # TODO: 可以在这里记录日志或错误信息
        pass

    # 第三部分
    try:
        if report.section3.raw_text.strip():
            parsed = parse_section3_applications(report.section3.raw_text)
            report.section3.tables.update(parsed)
    except Exception:
        pass

    # 第四部分
    try:
        if report.section4.raw_text.strip():
            parsed = parse_section4_review_litigation(report.section4.raw_text)
            report.section4.tables.update(parsed)
    except Exception:
        pass


def parse_annual_report_text_to_dict(
    raw_text: str, *, with_tables: bool = True
) -> Dict[str, Any]:
    """
    方便给 FastAPI / 前端用的字典版本。
    """
    return asdict(parse_annual_report_text(raw_text, with_tables=with_tables))


def _demo_from_stdin() -> None:
    """
    简单命令行测试：从标准输入读文本，打印各部分长度。
    用法：
        python -m govnianbao.annual_report_parser < report.txt
    """
    import sys

    raw_text = sys.stdin.read()
    report = parse_annual_report_text(raw_text, with_tables=False)

    for idx in range(1, 7):
        title = report.sections_title.get(idx, f"第 {idx} 部分")
        if idx == 1:
            length = len(report.section1.text)
        elif idx == 2:
            length = len(report.section2.raw_text)
        elif idx == 3:
            length = len(report.section3.raw_text)
        elif idx == 4:
            length = len(report.section4.raw_text)
        elif idx == 5:
            length = len(report.section5.text)
        else:
            length = len(report.section6.text)
        print(f"{idx}. {title} -> {length} chars")


if __name__ == "__main__":
    _demo_from_stdin()
