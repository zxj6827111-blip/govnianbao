#!/usr/bin/env python3
"""
诊断 PDF 数字提取问题的脚本

目的：找出数字提取过程中的缺陷，特别是可能遗漏的模式
"""
import re
import sys
from pathlib import Path

# 添加 src 到路径
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from govnianbao.tables_parser import _TABLE3_NUMBER_PATTERN


def extract_with_different_patterns(text: str):
    """用多种正则模式提取数字，对比结果"""
    
    print("=" * 80)
    print("数字提取诊断")
    print("=" * 80)
    
    # 模式1: 当前使用的模式 - 只提取整数
    pattern1 = re.compile(r"\d+")
    nums1 = pattern1.findall(text)
    
    # 模式2: 提取整数和小数（带可选小数点）
    pattern2 = re.compile(r"\d+(?:\.\d+)?")
    nums2 = pattern2.findall(text)
    
    # 模式3: 提取带符号的数字
    pattern3 = re.compile(r"[+-]?\d+(?:\.\d+)?")
    nums3 = pattern3.findall(text)
    
    # 模式4: 考虑逗号分隔的大数字（千分位）
    text_cleaned = text.replace(",", "").replace("，", "")
    pattern4 = re.compile(r"\d+(?:\.\d+)?")
    nums4 = pattern4.findall(text_cleaned)
    
    results = {
        "当前模式(\d+)": nums1,
        "带小数(\d+(?:\.\d+)?)": nums2,
        "带符号([+-]?\d+(?:\.\d+)?)": nums3,
        "去除逗号后": nums4,
    }
    
    print("\n【提取结果对比】")
    for name, nums in results.items():
        print(f"\n{name}:")
        print(f"  数字总数: {len(nums)}")
        if len(nums) > 0:
            print(f"  前10个: {nums[:10]}")
            print(f"  后10个: {nums[-10:]}")
    
    # 检查差异
    print("\n【结果差异分析】")
    print(f"模式1 vs 模式2 差异: {len(nums2) - len(nums1)} 个")
    print(f"模式1 vs 模式3 差异: {len(nums3) - len(nums1)} 个")
    print(f"模式1 vs 模式4 差异: {len(nums4) - len(nums1)} 个")
    
    # 关键检查：看 nums1 是否缺少某些应该有的数字
    print("\n【关键数字格式检查】")
    
    # 检查是否有特殊格式的数字（如百分比、负数等）
    special_patterns = {
        "百分数": re.compile(r"\d+(?:\.\d+)?%"),
        "负数": re.compile(r"-\d+(?:\.\d+)?"),
        "小数": re.compile(r"\d+\.\d+"),
        "千分位": re.compile(r"\d{1,3}(?:,\d{3})+"),
        "带括号负数": re.compile(r"\(\d+\)"),
    }
    
    for name, pattern in special_patterns.items():
        matches = pattern.findall(text)
        if matches:
            print(f"\n⚠️  发现 {name}: {len(matches)} 个")
            print(f"   示例: {matches[:5]}")
    
    # 建议使用的最优模式
    print("\n【建议】")
    print(f"最安全的模式: 先去除逗号，再用 \\d+(?:\\.\\d+)? 提取")
    print(f"这样可以捕获所有整数和小数，包括千分位数字")
    
    return nums1, nums4


def diagnose_format_mismatch(num_count: int):
    """诊断数字数量不匹配的问题"""
    
    print("\n" + "=" * 80)
    print("格式匹配诊断")
    print("=" * 80)
    
    print(f"\n实际提取数字数量: {num_count}")
    
    # 标准格式
    print("\n【标准格式期望值】")
    print(f"  25行 × 7列 = 175 个")
    print(f"  28行 × 8列 = 224 个")
    
    # 可能的缺失情况
    print("\n【可能的缺失情况分析】")
    if num_count < 175:
        missing = 175 - num_count
        missing_rows = missing // 8 if missing % 8 == 0 else "不是整行"
        print(f"  缺失: {missing} 个数字")
        print(f"  相当于: ~{missing_rows} 行数据（8列）")
    elif 175 < num_count < 224:
        excess = num_count - 175
        missing_for_full = 224 - num_count
        print(f"  已提取: {num_count}")
        print(f"  vs 7列格式多出: {excess} 个")
        print(f"  vs 8列格式缺少: {missing_for_full} 个")
        if missing_for_full % 8 == 0:
            missing_rows = missing_for_full // 8
            print(f"  🔴 缺少 {missing_rows} 行完整数据（8列）")
    elif num_count > 224:
        excess = num_count - 224
        print(f"  提取过多: {excess} 个数字")
        print(f"  可能包含了表格外的数字或重复数字")
    
    # 检查是否能被 7 或 8 整除
    print("\n【整除性检查】")
    if num_count % 7 == 0:
        rows_7 = num_count // 7
        print(f"  ✓ 能被 7 整除: {num_count} = {rows_7} × 7")
    else:
        print(f"  ✗ 不能被 7 整除，余数: {num_count % 7}")
    
    if num_count % 8 == 0:
        rows_8 = num_count // 8
        print(f"  ✓ 能被 8 整除: {num_count} = {rows_8} × 8")
    else:
        print(f"  ✗ 不能被 8 整除，余数: {num_count % 8}")


def main():
    """主函数"""
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
        if not file_path.exists():
            print(f"错误：文件不存在: {file_path}")
            sys.exit(1)
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        print("正在从标准输入读取文本...")
        text = sys.stdin.read()
    
    if not text.strip():
        print("错误：输入文本为空")
        sys.exit(1)
    
    nums1, nums4 = extract_with_different_patterns(text)
    diagnose_format_mismatch(len(nums1))
    diagnose_format_mismatch(len(nums4))


if __name__ == "__main__":
    main()
