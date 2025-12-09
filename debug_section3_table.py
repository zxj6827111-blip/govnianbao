#!/usr/bin/env python3
"""
调试脚本：测试 section3 表格解析

使用方法：
1. 从文本文件读取：
   python debug_section3_table.py < sample_report.txt

2. 直接传入淮安 2023 年报告文本（如果有 PDF 文件）：
   # 先安装 pypdf：pip install pypdf
   python -c "from pypdf import PdfReader; print(''.join(p.extract_text() for p in PdfReader('huai_an_2023.pdf').pages))" | python debug_section3_table.py

3. 或者在代码中直接提供样例文本进行调试
"""
from __future__ import annotations

import sys
import json
from pathlib import Path

# 添加 src 到路径，允许本地开发模式运行
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from govnianbao import parse_annual_report_text_to_dict


def debug_section3(text: str) -> None:
    """调试 section3 表格解析"""
    print("=" * 80)
    print("开始解析年报文本...")
    print("=" * 80)
    
    try:
        result = parse_annual_report_text_to_dict(text)
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return

    section3 = result.get("section3") or {}
    
    # 1. 检查 section3 基本信息
    print("\n=== section3 基本信息 ===")
    print(f"section3 keys: {list(section3.keys())}")
    
    raw_text = section3.get("raw_text") or ""
    print(f"\nsection3.raw_text 长度: {len(raw_text)} 字符")
    if raw_text:
        print(f"section3.raw_text 前 300 字符:")
        print(raw_text[:300])
        print("...")
    else:
        print("⚠️  section3.raw_text 为空！")
    
    # 2. 检查 tables 结构
    print("\n" + "=" * 80)
    print("=== section3.tables 结构 ===")
    tables = section3.get("tables") or {}
    print(f"tables keys: {list(tables.keys())}")
    
    # 3. 检查 section3_applications
    print("\n" + "=" * 80)
    print("=== section3_applications 表格 ===")
    apps = tables.get("section3_applications") or {}
    print(f"section3_applications keys: {list(apps.keys())}")
    
    # 4. 检查 cells
    cells = apps.get("cells") or {}
    print(f"\n✓ cells 类型: {type(cells)}")
    print(f"✓ cells 长度: {len(cells)} 行")
    
    if isinstance(cells, dict):
        if len(cells) > 0:
            print(f"✓ 成功！cells 包含 {len(cells)} 行数据")
            
            # 显示前几行的样例数据
            items = list(cells.items())
            print(f"\n样例数据（前 5 行）:")
            for i, (row_key, row_values) in enumerate(items[:5]):
                print(f"  [{i+1}] {row_key}:")
                if isinstance(row_values, dict):
                    sample_items = list(row_values.items())[:3]
                    for col_key, value in sample_items:
                        print(f"      {col_key}: {value}")
                else:
                    print(f"      {row_values}")
            
            # 检查解析警告
            warnings = apps.get("parse_warnings")
            if warnings:
                print(f"\n⚠️  解析警告:")
                for w in warnings:
                    print(f"  - {w}")
        else:
            print("❌ 失败！cells 是空字典")
            warnings = apps.get("parse_warnings")
            if warnings:
                print(f"\n解析警告:")
                for w in warnings:
                    print(f"  - {w}")
    else:
        print(f"❌ 失败！cells 不是字典类型，而是 {type(cells)}")
    
    # 5. 保存完整结构到 JSON 文件（方便进一步检查）
    output_file = Path("debug_section3_output.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n完整解析结果已保存到: {output_file}")
    
    print("\n" + "=" * 80)
    print("调试完成")
    print("=" * 80)


def main():
    """主函数"""
    # 如果有命令行参数，读取文件；否则从标准输入读取
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
        if not file_path.exists():
            print(f"错误：文件不存在: {file_path}")
            sys.exit(1)
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        # 从标准输入读取
        print("正在从标准输入读取文本...")
        print("（提示：你可以粘贴文本，然后按 Ctrl+D (Unix) 或 Ctrl+Z (Windows) 结束输入）")
        text = sys.stdin.read()
    
    if not text.strip():
        print("错误：输入文本为空")
        sys.exit(1)
    
    debug_section3(text)


if __name__ == "__main__":
    main()
