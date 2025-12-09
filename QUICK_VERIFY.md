# ⚡ 快速验证清单

## 一行命令验证

```bash
cd /workspaces/govnianbao && python -m pytest tests/ -v && python debug_section3_table.py sample_report_section3.txt | grep -E "(✓|cells)" | head -20
```

## 预期输出

```
✅ 所有测试通过
✓ cells 长度: 25 行
✓ 成功！cells 包含 25 行数据
```

## 核心验证点

- [ ] `section3_applications.cells` 不再是 `{}`
- [ ] 支持 25×7 格式 (175 个数字)
- [ ] 支持 28×8 格式 (224 个数字)
- [ ] 能解析出关键数值 (2811, 2896, 34 等)
- [ ] 所有测试 PASSED

## 代码位置

| 文件 | 函数 | 状态 |
|------|------|------|
| `tables_parser.py` | `parse_template_table3` | ✅ 完成 |
| `tables_parser.py` | `parse_section3_applications` | ✅ 完成 |
| `annual_report_parser.py` | `_fill_tables_best_effort` | ✅ 集成 |

## 如何在 GovAnnualCompare 中验证

```bash
# 1. 更新依赖
pip install --force-reinstall --no-deps git+https://github.com/zxj6827111-blip/govnianbao.git@main

# 2. 重新处理 PDF
python -c "
from app.services.fetch_url import ingest_pdf_from_url
ingest_pdf_from_url('huai_an_2023_url')
"

# 3. 查看输出
python debug_annual_struct.py
# 预期: cells len > 0, rows > 0
```

## 常用调试命令

```bash
# 查看完整输出
python debug_section3_table.py sample_report_section3.txt

# 从 PDF 提取并解析
pdftotext huai_an_2023.pdf - | python debug_section3_table.py

# 查看 JSON 输出
cat debug_section3_output.json | python -m json.tool | head -100
```

---

**状态**: ✅ Ready to Ship
