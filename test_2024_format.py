#!/usr/bin/env python3
"""
测试 2024 年报告格式：25 行数据 × 7 列 + 4 个总计行自动求和
"""
import sys
sys.path.insert(0, '/workspaces/govnianbao/src')

from govnianbao.tables_parser import parse_template_table3


def test_2024_format():
    """测试 2024 年格式：175 个数字 + 4 个总计行自动求和"""
    
    # 构造类似 2024 年报告的文本
    # 生成 175 个数字（注意：不要在描述文字中包含这些数字）
    numbers_str = " ".join(str(i) for i in range(1, 176))
    
    test_text = f"""
一、总体情况
这是总体情况的说明文字。

三、收到和处理政府信息公开申请情况

以下是表格数据：

{numbers_str}

四、政府信息公开行政复议、行政诉讼情况
这里是行政复议、行政诉讼的说明。
"""

    print("=" * 80)
    print("测试 2024 年报告格式")
    print("=" * 80)
    print(f"\n输入数字数: 175 (25 行 × 7 列)")
    
    try:
        result = parse_template_table3(test_text)
        cells = result['cells']
        
        print(f"\n✅ 解析成功！")
        print(f"  输出行数: {len(cells)}")
        print(f"  输出列数: {len(list(cells.values())[0]) if cells else 0}")
        
        # 检查 4 个总计行
        totals = [
            'result_not_public_total',
            'result_cannot_provide_total', 
            'result_not_processed_total',
            'result_other_total'
        ]
        
        print(f"\n  4 个总计行的状态:")
        for total_key in totals:
            if total_key in cells:
                values = cells[total_key]
                non_zero = sum(1 for v in values.values() if isinstance(v, (int, float)) and v > 0)
                print(f"    ✓ {total_key}: {non_zero} 个非零值")
            else:
                print(f"    ✗ {total_key}: 缺失！")
        
        # 检查缺失的关键行
        key_rows = [
            ('result_not_public_safety', '危及"三安全一稳定"'),
            ('result_not_public_third_party', '保护第三方合法权益'),
            ('result_not_provide_no_existing', '没有现成信息需要另行制作'),
            ('result_not_process_publication', '要求提供公开出版物'),
        ]
        
        print(f"\n  关键行的状态:")
        for row_key, desc in key_rows:
            if row_key in cells:
                values = cells[row_key]
                first_val = next((v for v in values.values() if isinstance(v, (int, float))), None)
                print(f"    ✓ {desc}: {first_val}")
            else:
                print(f"    ✗ {desc}: 缺失！")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_2024_format()
    sys.exit(0 if success else 1)
