# PDF 数字提取问题诊断清单

## 🔍 如何诊断数字提取是否不完整？

当第三部分表格的最后 4 行缺失时，按照以下步骤诊断真实原因。

---

## 第一步：确认问题症状

### 症状检查清单

- [ ] Word 模板中，第三部分表格的末尾 4 行为空
- [ ] 这 4 行分别是：
  - [ ] 3.危及"三安全一稳定"（不予公开分项）
  - [ ] 4.保护第三方合法权益（不予公开分项）
  - [ ] 2.没有现成信息需要另行制作（无法提供分项）
  - [ ] 3.要求提供公开出版物（不予处理分项）
- [ ] 其他部分的数据显示正常

### 如何确认？

1. 打开生成的 Word 文档
2. 找到"三、收到和处理政府信息公开申请情况"表格
3. 滚动到表格末尾，检查最后 28 行是否齐全

---

## 第二步：提取 PDF 文本进行分析

### 方式 1：使用 pdftotext（推荐）

```bash
# 安装工具（如果还没有）
apt-get install poppler-utils

# 提取 PDF 文本
pdftotext -layout your_report.pdf output.txt

# 查看第三部分内容
grep -A 500 "三、收到和处理政府信息公开申请情况" output.txt | head -100
```

### 方式 2：使用 Python 的 PyPDF

```python
from pypdf import PdfReader

with open('your_report.pdf', 'rb') as f:
    reader = PdfReader(f)
    full_text = ''.join(page.extract_text() for page in reader.pages)
    
# 找到第三部分
idx = full_text.find('三、收到和处理政府信息公开申请情况')
section3_text = full_text[idx:idx+5000]
print(section3_text)
```

---

## 第三步：分析提取出的数字

### 运行诊断脚本

```bash
# 分析你的 PDF 文本
python diagnose_extraction.py < pdf_output.txt

# 或者指定文件
python diagnose_extraction.py your_extracted_text.txt
```

### 关键指标

| 指标 | 含义 | 预期值 |
|------|------|--------|
| 总数字数 | 提取出的所有整数数量 | 224（完整）或 192（缺少4行） |
| 能被 8 整除 | 是否是 8 列格式 | 应该能整除 |
| 能被 7 整除 | 是否是 7 列格式 | 可能能整除，但非首选 |

### 诊断输出示例

```
【提取结果对比】
当前模式(\d+):
  数字总数: 192  ← 这表示缺少 32 个数字（4行×8列）
  
【整除性检查】
✓ 能被 8 整除: 192 = 24 × 8  ← 系统应该识别为 8 列格式的 24 行
✗ 不能被 8 整除，余数: 0
```

---

## 第四步：深入分析缺失原因

### 方式 1：查看原始 PDF 结构

```bash
# 用文本编辑器打开 PDF（可能看到乱码，但能看到结构）
strings your_report.pdf | grep -i "三安全" | head -5

# 或用专业的 PDF 查看器检查表格结构
```

### 方式 2：比较提取前后的内容

```python
# 导入库
from govnianbao.tables_parser import _TABLE3_NUMBER_PATTERN
import re

# 读取 PDF 提取的文本
with open('pdf_text.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# 提取所有数字
numbers = _TABLE3_NUMBER_PATTERN.findall(text)
print(f"总数: {len(numbers)}")

# 查看最后 100 个数字（看是否有异常模式）
print(f"最后 100 个数: {numbers[-100:]}")

# 检查是否有特殊字符阻断了提取
special_chars = re.findall(r'[^\w\s\-\.]', text)
print(f"特殊字符: {set(special_chars)[:20]}")  # 前 20 种
```

### 方式 3：行级别分析

```python
# 按行分析，看缺失的 4 行在哪里
lines = text.split('\n')

# 找包含特定标签的行
target_labels = [
    '危及',
    '三安全',
    '保护第三方',
    '现成',
    '制作',
    '公开出版物'
]

for i, line in enumerate(lines):
    for label in target_labels:
        if label in line:
            print(f"第 {i} 行: {line[:100]}")
            # 看这一行之后有没有数字
            rest = ' '.join(lines[i:i+5])
            nums = re.findall(r'\d+', rest)
            print(f"  后续数字: {nums[:10]}")
```

---

## 第五步：可能的根本原因及对应解决方案

### 原因 1: PDF 页面分割问题

**症状**：
```
第三部分表格从第 3 页开始
可能跨越多个页面（第 3-5 页）
有些页的数字没有被完整提取
```

**验证方法**：
```bash
# 逐页提取，看哪一页缺少数字
pdftotext -f 3 -l 5 your_report.pdf page3-5.txt

# 统计每一页的数字数
for i in {3..5}; do
  pdftotext -f $i -l $i your_report.pdf page$i.txt
  echo "第 $i 页数字数: $(grep -o '[0-9]\+' page$i.txt | wc -l)"
done
```

**解决方案**：
- 检查 PDF 是否有页边距或页码行阻碍提取
- 尝试使用不同的 PDF 提取库（OCR、pdfminer 等）

---

### 原因 2: 表格格式特殊

**症状**：
```
最后 4 行的行标签可能包含：
- 引号（"三安全一稳定"）
- 缩进或特殊格式
- 与其他行不同的分隔符
```

**验证方法**：
```python
# 查看缺失行的原始内容
pdf_text = "..."  # 从 PDF 提取的文本

# 搜索这些行的标签
search_patterns = [
    r'危及.*三安全',
    r'保护.*第三方.*权益',
    r'没有.*现成.*制作',
    r'要求.*公开.*出版'
]

for pattern in search_patterns:
    if re.search(pattern, pdf_text):
        print(f"✓ 找到: {pattern}")
    else:
        print(f"✗ 缺失: {pattern}")
```

**解决方案**：
- 改进正则表达式以匹配特殊格式
- 预处理文本，统一特殊字符的表示

---

### 原因 3: 数字显示格式异常

**症状**：
```
最后 4 行的数字可能是：
- 以不同的字体或颜色显示
- 使用了不同的字符（如中文数字）
- 被特殊符号包围（如括号）
```

**验证方法**：
```bash
# 查看 PDF 的原始二进制内容
strings your_report.pdf | tail -500 | head -200

# 查找可能的数字表示方式
grep -o '[０-９]' pdf_text.txt  # 全角数字
grep -o '[〇一二三四五六七八九]' pdf_text.txt  # 中文数字
```

**解决方案**：
- 扩展数字识别正则以支持全角、中文数字
- 预处理文本进行格式标准化

---

### 原因 4: 系统的 fallback 逻辑

**症状**：
```
即使提取了完整的 224 个数字
系统仍然因为某种原因用了 lenient 解析
导致最后 4 行为空
```

**验证方法**：
```python
# 检查系统的决策过程
from govnianbao.tables_parser import parse_section3_applications
import logging

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

result = parse_section3_applications(your_pdf_text)

# 查看日志中是否有：
# - "matched exact 8-column format" → 正确识别
# - "inferred 8-column partial format" → 识别为部分缺失
# - "fallback to lenient parsing" → 使用了 fallback（可能出问题）
```

**解决方案**：
- 查看具体的日志消息，了解系统做出的决定
- 如果是 fallback 到 lenient，检查原因

---

## 第六步：收集完整的诊断信息

### 创建诊断报告

```bash
# 创建诊断脚本
cat > diagnose_issue.sh << 'EOF'
#!/bin/bash

PDF_FILE="$1"
OUTPUT_DIR="./diagnosis_$(date +%Y%m%d_%H%M%S)"

mkdir -p "$OUTPUT_DIR"

echo "📋 诊断开始..."

# 1. 提取文本
echo "1️⃣  提取 PDF 文本..."
pdftotext "$PDF_FILE" "$OUTPUT_DIR/full_text.txt"

# 2. 运行诊断脚本
echo "2️⃣  分析数字提取..."
python diagnose_extraction.py < "$OUTPUT_DIR/full_text.txt" > "$OUTPUT_DIR/extraction_analysis.txt"

# 3. 测试系统识别
echo "3️⃣  测试系统识别..."
python -c "
from govnianbao import parse_annual_report_text_to_dict
with open('$OUTPUT_DIR/full_text.txt') as f:
    result = parse_annual_report_text_to_dict(f.read())
cells = result['section3']['tables']['section3_applications']['cells']
print(f'识别行数: {len(cells)}')
" > "$OUTPUT_DIR/system_recognition.txt" 2>&1

echo "✅ 诊断完成，结果保存在: $OUTPUT_DIR/"
echo "文件列表:"
ls -la "$OUTPUT_DIR/"
EOF

chmod +x diagnose_issue.sh

# 运行诊断
./diagnose_issue.sh your_report.pdf
```

### 诊断输出包含

```
diagnosis_20251210_120000/
├── full_text.txt              # 完整的 PDF 文本
├── extraction_analysis.txt    # 数字提取分析
└── system_recognition.txt     # 系统识别结果
```

---

## 第七步：报告问题

如果诊断发现了异常，请收集以下信息：

1. ✅ PDF 文件（或至少 section 3 的文本）
2. ✅ 诊断报告（上面生成的 diagnosis_* 目录）
3. ✅ 预期的 Word 输出（如果有的话）
4. ✅ 系统的日志（用 DEBUG 级别运行）

---

## 快速参考

### 正常情况
```
✅ 提取数字数：224
✅ 能被 8 整除：224 = 28 × 8
✅ 系统识别：8 列，28 行
✅ Word 输出：28 行都有数据
```

### 部分缺失（新系统能处理）
```
⚠️  提取数字数：192
✅ 能被 8 整除：192 = 24 × 8
✅ 系统识别：8 列，24 行（缺少末尾 4 行）
⚠️  Word 输出：24 行有数据，末尾 4 行缺失（这是正确的反映）
```

### 异常情况
```
❌ 提取数字数：不是 175 也不是 224 也不是 8 的倍数
❌ 系统识别：无法识别格式
❌ Word 输出：可能出现错误数据或空白
→ 需要根据具体情况诊断
```

---

**诊断工具**：
- `diagnose_extraction.py` - 分析数字提取
- `test_partial_missing.py` - 测试格式识别
- `QUICK_VERIFY.md` - 快速验证

**相关文档**：
- `ROOT_CAUSE_FIX_REPORT.md` - 根本原因详细分析
- `QUICK_FIX_GUIDE.md` - 快速修复指南
