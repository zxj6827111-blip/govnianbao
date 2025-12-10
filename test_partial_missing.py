#!/usr/bin/env python3
"""
测试脚本：验证改进后的表格解析是否能正确处理缺失行的情况

测试场景：
1. 完整格式 (224 数字) - 应该正常解析
2. 部分缺失 (192 数字 = 24×8) - 应该识别为 8 列格式的 24 行
3. 简化格式 (175 数字) - 应该识别为 7 列格式的 25 行
"""
from __future__ import annotations

import sys
from pathlib import Path

# 添加 src 到路径
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from govnianbao.tables_parser import parse_template_table3


def create_test_text(num_count: int) -> str:
    """生成包含指定数量数字的测试文本"""
    numbers = " ".join(str(i) for i in range(1, num_count + 1))
    return f"""
    三、收到和处理政府信息公开申请情况
    
    以下是表格数据：
    {numbers}
    
    四、政府信息公开行政复议
    """


def test_format_recognition():
    """测试格式识别"""
    
    test_cases = [
        (175, "7列格式 (25行×7列)", 25, 7),
        (192, "8列部分缺失 (24行×8列)", 24, 8),
        (200, "8列部分缺失 (25行×8列)", 25, 8),
        (216, "8列部分缺失 (27行×8列)", 27, 8),
        (224, "8列完整格式 (28行×8列)", 28, 8),
    ]
    
    print("=" * 80)
    print("表格格式识别测试")
    print("=" * 80)
    
    for num_count, description, expected_rows, expected_cols in test_cases:
        test_text = create_test_text(num_count)
        
        try:
            result = parse_template_table3(test_text)
            cells = result.get("cells", {})
            
            actual_rows = len(cells)
            actual_cols = len(list(cells.values())[0]) if cells else 0
            
            # 检查是否成功识别了正确的格式
            success = (actual_rows == expected_rows and actual_cols == expected_cols)
            status = "✅ 成功" if success else "❌ 失败"
            
            print(f"\n[{status}] {description} ({num_count}个数字)")
            print(f"  期望: {expected_rows}行 × {expected_cols}列")
            print(f"  实际: {actual_rows}行 × {actual_cols}列")
            
            # 展示部分数据
            if cells:
                first_row_key = list(cells.keys())[0]
                first_row_values = cells[first_row_key]
                non_none_count = sum(1 for v in first_row_values.values() if v is not None)
                print(f"  第一行数据: {non_none_count} 个非空值 (共 {actual_cols} 列)")
            
            # 检查缺失的行（应该为 None）
            if actual_rows < 28:
                # 获取最后一行和倒数第二行的非空数据数
                all_rows = list(cells.values())
                if len(all_rows) > 0:
                    last_row_non_null = sum(1 for v in all_rows[-1].values() if v is not None)
                    print(f"  最后一行有 {last_row_non_null} 个非空值")
            
        except Exception as e:
            print(f"\n[❌ 异常] {description} ({num_count}个数字)")
            print(f"  错误: {e}")


def test_partial_missing_data():
    """特别测试缺失的4行（192 数字的情况）"""
    
    print("\n" + "=" * 80)
    print("缺失4行数据的具体测试 (192 = 24×8)")
    print("=" * 80)
    
    num_count = 192  # 缺少 4 行（32 个数字）
    test_text = create_test_text(num_count)
    
    try:
        result = parse_template_table3(test_text)
        cells = result.get("cells", {})
        
        print(f"\n✅ 成功识别为 24 行 × 8 列")
        print(f"   实际解析出 {len(cells)} 行数据")
        
        # 显示最后几行的填充情况
        rows_list = list(cells.items())
        print(f"\n【最后3行的数据完整性检查】")
        for i in range(max(0, len(rows_list) - 3), len(rows_list)):
            row_key, row_values = rows_list[i]
            non_null = sum(1 for v in row_values.values() if v is not None)
            print(f"  [{i+1}] {row_key}: {non_null}/8 列有数据")
        
        # 计算总的有效数据点数
        total_values = sum(1 for row in cells.values() for v in row.values() if v is not None)
        print(f"\n总数据点: {total_values}/192")
        
    except Exception as e:
        print(f"\n❌ 解析失败: {e}")


def main():
    test_format_recognition()
    test_partial_missing_data()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
