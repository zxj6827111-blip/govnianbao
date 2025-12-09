# Section3 表格解析调试说明

## 问题描述

之前 `section3_applications` 的 `cells` 永远是空字典。

## 修复内容

### 1. 改进了 `parse_template_table3` 函数

- **支持多种格式**：
  - 简化格式：25 行数据 × 7 列（不包含 org_total）= 175 个数字
  - 完整格式：28 行数据 × 8 列（包含 org_total）= 224 个数字
  
- **更宽容的解析逻辑**：
  - 根据实际提取的数字数量智能匹配格式
  - 不再强制要求精确匹配模板定义的全部列

### 2. 优化了 `parse_section3_applications` 函数

- **双层策略**：
  1. 优先尝试模板解析（`parse_template_table3`）
  2. 如果模板解析失败，fallback 到 lenient 解析（`_fill_section3_lenient`）
  
- **更好的错误处理**：
  - 捕获异常并记录警告
  - 即使模板解析失败也能继续尝试其他方法

### 3. 创建了调试脚本

位置：`debug_section3_table.py`

## 使用调试脚本

### 方法 1：从文本文件读取

```bash
python3 debug_section3_table.py sample_report_section3.txt
```

### 方法 2：从标准输入读取

```bash
cat your_report.txt | python3 debug_section3_table.py
```

### 方法 3：如果有 PDF 文件（需要安装 pypdf）

```bash
# 安装依赖
pip3 install pypdf

# 从 PDF 提取文本并解析
python3 -c "from pypdf import PdfReader; print(''.join(p.extract_text() for p in PdfReader('huai_an_2023.pdf').pages))" | python3 debug_section3_table.py
```

## 验证结果

调试脚本会显示：

1. **section3.raw_text** 的长度和前 300 字符
2. **section3_applications.cells** 的长度（应该 > 0）
3. **样例数据**（前 5 行）
4. **解析警告**（如果有）
5. 完整的解析结果会保存到 `debug_section3_output.json`

### 成功的标志

- ✓ cells 长度大于 0（通常是 25 或 28 行）
- ✓ 样例数据显示了正确的行键和列值
- ✓ 值都是浮点数类型

## 测试

运行测试以验证修复：

```bash
# 安装包
pip3 install -e .

# 运行所有测试
python3 -m pytest tests/ -v

# 只运行 section3 相关测试
python3 -m pytest tests/test_tables_parser.py -v
```

## 完成标准

- ✅ 在 govnianbao 仓库内部，用淮安 2023 年年度报告的文本调用 `parse_annual_report_text_to_dict(text)` 时：
  - `annual_struct["section3"]["raw_text"]` 不为空
  - `annual_struct["section3"]["tables"]["section3_applications"]["cells"]` 是一个非空字典
  
- ✅ 回到 GovAnnualCompare 项目中：
  1. 重新安装：`pip install --force-reinstall --no-deps git+https://github.com/zxj6827111-blip/govnianbao.git@main`
  2. 重新 `/ingest/pdf` 同一份 PDF
  3. 运行 `python debug_annual_struct.py` 时，能看到 `cells len > 0`
