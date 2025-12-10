from __future__ import annotations

from typing import Any, Dict, List

"""
固定 6 个板块里，第二、三、四部分的表格模板。

设计原则：
- 所有可填数字的单元格，都有一个稳定的 key（row_key + col_key）
- 行、列的显示标题基本保持和 Word 模板一致，方便对照
- 通过 section / key / group / indent 等字段保留层次结构信息
"""

# 6 个固定板块标题（按顺序）
SECTION_TITLES: Dict[int, str] = {
    1: "一、总体情况",
    2: "二、主动公开政府信息情况",
    3: "三、收到和处理政府信息公开申请情况",
    4: "四、政府信息公开行政复议、行政诉讼情况",
    5: "五、存在的主要问题及改进情况",
    6: "六、其他需要报告的事项",
}

# 通用字段说明：
# - section: 第几部分
# - key: 该表在本部分内的唯一 key
# - caption: Word 里的表标题/条款，如“第二十条第（一）项”
# - note: 额外说明（如勾稽关系）
# - columns: 列定义列表
#   - key: 列字段名
#   - label: 列在表头显示的文字
#   - type: "label" / "int" / "float"（目前主要是 int）
# - rows: 行定义列表（按显示顺序）
#   - key: 行字段名
#   - label: 行首显示文字
#   - group: 上级分组标题（如“三、本年度办理结果”）
#   - indent: 缩进级别，用于前端渲染层级
#   - data: 是否是“需要填数字”的数据行（False 则只是标题行）
#
# 将来真正存值时，可以按：
#   tables[table_id]["cells"][row_key][col_key] = 数字
# 来组织。

TEMPLATE_TABLES: Dict[str, Dict[str, Any]] = {
    # ========== 第二部分：主动公开政府信息情况 ==========
    "section2_art20_1": {
        "section": 2,
        "key": "art20_1",
        "caption": "第二十条第（一）项",
        "title": "主动公开政府信息情况",
        "columns": [
            {"key": "content", "label": "信息内容", "type": "label"},
            {"key": "issued_this_year", "label": "本年制发件数", "type": "int"},
            {"key": "abolished_this_year", "label": "本年废止件数", "type": "int"},
            {"key": "effective_now", "label": "现行有效件数", "type": "int"},
        ],
        "rows": [
            {"key": "regulations", "label": "规章"},
            {"key": "normative_docs", "label": "行政规范性文件"},
        ],
    },
    "section2_art20_5": {
        "section": 2,
        "key": "art20_5",
        "caption": "第二十条第（五）项",
        "title": "行政许可",
        "columns": [
            {"key": "content", "label": "信息内容", "type": "label"},
            {"key": "decisions", "label": "本年处理决定数量", "type": "int"},
        ],
        "rows": [
            {"key": "admin_permission", "label": "行政许可"},
        ],
    },
    "section2_art20_6": {
        "section": 2,
        "key": "art20_6",
        "caption": "第二十条第（六）项",
        "title": "行政处罚和行政强制",
        "columns": [
            {"key": "content", "label": "信息内容", "type": "label"},
            {"key": "decisions", "label": "本年处理决定数量", "type": "int"},
        ],
        "rows": [
            {"key": "admin_penalty", "label": "行政处罚"},
            {"key": "admin_compulsion", "label": "行政强制"},
        ],
    },
    "section2_art20_8": {
        "section": 2,
        "key": "art20_8",
        "caption": "第二十条第（八）项",
        "title": "行政事业性收费",
        "columns": [
            {"key": "content", "label": "信息内容", "type": "label"},
            {
                "key": "fee_amount",
                "label": "本年收费金额（单位：万元）",
                "type": "float",
            },
        ],
        "rows": [
            {"key": "admin_public_fee", "label": "行政事业性收费"},
        ],
    },

    # ========== 第三部分：收到和处理政府信息公开申请情况 ==========
    "section3_applications": {
        "section": 3,
        "key": "applications",
        "caption": "收到和处理政府信息公开申请情况",
        "note": "本列数据的勾稽关系：第一项 + 第二项 = 第三项 + 第四项。",
        "columns": [
            {
                "key": "item",
                "label": "申请人情况 / 办理结果",
                "type": "label",
            },
            {"key": "natural_person", "label": "自然人", "type": "int"},
            {"key": "business_corp", "label": "商业企业", "type": "int"},
            {"key": "research_org", "label": "科研机构", "type": "int"},
            {"key": "social_org", "label": "社会公益组织", "type": "int"},
            {"key": "legal_service_org", "label": "法律服务机构", "type": "int"},
            {"key": "other_org", "label": "其他", "type": "int"},
            {
                "key": "org_total",
                "label": "法人或其他组织小计",
                "type": "int",
            },
            {"key": "grand_total", "label": "总计", "type": "int"},
        ],
        "rows": [
            # 一、二 两行是总量行
            {
                "key": "new_requests",
                "label": "一、本年新收政府信息公开申请数量",
                "indent": 0,
                "data": True,
            },
            {
                "key": "carried_over",
                "label": "二、上年结转政府信息公开申请数量",
                "indent": 0,
                "data": True,
            },
            # 三、本年度办理结果（标题行，不填数字）
            {
                "key": "result_this_year_header",
                "label": "三、本年度办理结果",
                "indent": 0,
                "data": False,
            },
            # （一）予以公开
            {
                "key": "result_open",
                "label": "（一）予以公开",
                "group": "三、本年度办理结果",
                "indent": 1,
                "data": True,
            },
            # （二）部分公开
            {
                "key": "result_partial",
                "label": "（二）部分公开（区分处理的，只计这一情形，不计其他情形）",
                "group": "三、本年度办理结果",
                "indent": 1,
                "data": True,
            },
            # （三）不予公开（总计）
            {
                "key": "result_not_public_total",
                "label": "（三）不予公开",
                "group": "三、本年度办理结果",
                "indent": 1,
                "data": True,
            },
            # （三）不予公开 8 个分项
            {
                "key": "result_not_public_state_secret",
                "label": "1.属于国家秘密",
                "group": "（三）不予公开",
                "indent": 2,
                "data": True,
            },
            {
                "key": "result_not_public_law_forbid",
                "label": "2.其他法律行政法规禁止公开",
                "group": "（三）不予公开",
                "indent": 2,
                "data": True,
            },
            {
                "key": "result_not_public_safety",
                "label": "3.危及\"三安全一稳定\"",
                "group": "（三）不予公开",
                "indent": 2,
                "data": True,
            },
            {
                "key": "result_not_public_third_party",
                "label": "4.保护第三方合法权益",
                "group": "（三）不予公开",
                "indent": 2,
                "data": True,
            },
            {
                "key": "result_not_public_internal",
                "label": "5.属于三类内部事务信息",
                "group": "（三）不予公开",
                "indent": 2,
                "data": True,
            },
            {
                "key": "result_not_public_process",
                "label": "6.属于四类过程性信息",
                "group": "（三）不予公开",
                "indent": 2,
                "data": True,
            },
            {
                "key": "result_not_public_case_file",
                "label": "7.属于行政执法案卷",
                "group": "（三）不予公开",
                "indent": 2,
                "data": True,
            },
            {
                "key": "result_not_public_inquiry",
                "label": "8.属于行政查询事项",
                "group": "（三）不予公开",
                "indent": 2,
                "data": True,
            },
            # （四）无法提供（总计 + 3 分项）
            {
                "key": "result_cannot_provide_total",
                "label": "（四）无法提供",
                "group": "三、本年度办理结果",
                "indent": 1,
                "data": True,
            },
            {
                "key": "result_cannot_provide_not_held",
                "label": "1.本机关不掌握相关政府信息",
                "group": "（四）无法提供",
                "indent": 2,
                "data": True,
            },
            {
                "key": "result_not_provide_no_existing",
                "label": "2.没有现成信息需要另行制作",
                "group": "（四）无法提供",
                "indent": 2,
                "data": True,
            },
            {
                "key": "result_cannot_provide_unclear",
                "label": "3.补正后申请内容仍不明确",
                "group": "（四）无法提供",
                "indent": 2,
                "data": True,
            },
            # （五）不予处理（总计 + 5 分项）
            {
                "key": "result_not_processed_total",
                "label": "（五）不予处理",
                "group": "三、本年度办理结果",
                "indent": 1,
                "data": True,
            },
            {
                "key": "result_not_processed_petition",
                "label": "1.信访举报投诉类申请",
                "group": "（五）不予处理",
                "indent": 2,
                "data": True,
            },
            {
                "key": "result_not_processed_duplicate",
                "label": "2.重复申请",
                "group": "（五）不予处理",
                "indent": 2,
                "data": True,
            },
            {
                "key": "result_not_process_publication",
                "label": "3.要求提供公开出版物",
                "group": "（五）不予处理",
                "indent": 2,
                "data": True,
            },
            {
                "key": "result_not_processed_frequent",
                "label": "4.无正当理由大量反复申请",
                "group": "（五）不予处理",
                "indent": 2,
                "data": True,
            },
            {
                "key": "result_not_processed_confirm_again",
                "label": "5.要求行政机关确认或重新出具已获取信息",
                "group": "（五）不予处理",
                "indent": 2,
                "data": True,
            },
            # （六）其他处理（总计 + 3 分项）
            {
                "key": "result_other_total",
                "label": "（六）其他处理",
                "group": "三、本年度办理结果",
                "indent": 1,
                "data": True,
            },
            {
                "key": "result_other_overdue_no_rectify",
                "label": "1.申请人无正当理由逾期不补正、行政机关不再处理其政府信息公开申请",
                "group": "（六）其他处理",
                "indent": 2,
                "data": True,
            },
            {
                "key": "result_other_no_pay_fee",
                "label": "2.申请人逾期未按收费通知要求缴纳费用、行政机关不再处理其政府信息公开申请",
                "group": "（六）其他处理",
                "indent": 2,
                "data": True,
            },
            {
                "key": "result_other_other",
                "label": "3.其他",
                "group": "（六）其他处理",
                "indent": 2,
                "data": True,
            },
            # （七）总计
            {
                "key": "result_total",
                "label": "（七）总计",
                "group": "三、本年度办理结果",
                "indent": 1,
                "data": True,
            },
            # 四、结转下年度继续办理
            {
                "key": "carry_next_year",
                "label": "四、结转下年度继续办理",
                "indent": 0,
                "data": True,
            },
        ],
    },

    # ========== 第四部分：行政复议、行政诉讼情况 ==========
    "section4_review_litigation": {
        "section": 4,
        "key": "review_litigation",
        "caption": "政府信息公开行政复议、行政诉讼情况",
        "columns": [
            {"key": "item", "label": "", "type": "label"},
            # 行政复议
            {"key": "rev_maintained", "label": "行政复议_结果维持", "type": "int"},
            {"key": "rev_corrected", "label": "行政复议_结果纠正", "type": "int"},
            {"key": "rev_other", "label": "行政复议_其他结果", "type": "int"},
            {"key": "rev_pending", "label": "行政复议_尚未审结", "type": "int"},
            {"key": "rev_total", "label": "行政复议_总计", "type": "int"},
            # 行政诉讼 - 未经复议直接起诉
            {
                "key": "lit_direct_maintained",
                "label": "未经复议直接起诉_结果维持",
                "type": "int",
            },
            {
                "key": "lit_direct_corrected",
                "label": "未经复议直接起诉_结果纠正",
                "type": "int",
            },
            {
                "key": "lit_direct_other",
                "label": "未经复议直接起诉_其他结果",
                "type": "int",
            },
            {
                "key": "lit_direct_pending",
                "label": "未经复议直接起诉_尚未审结",
                "type": "int",
            },
            {
                "key": "lit_direct_total",
                "label": "未经复议直接起诉_总计",
                "type": "int",
            },
            # 行政诉讼 - 复议后起诉
            {
                "key": "lit_after_rev_maintained",
                "label": "复议后起诉_结果维持",
                "type": "int",
            },
            {
                "key": "lit_after_rev_corrected",
                "label": "复议后起诉_结果纠正",
                "type": "int",
            },
            {
                "key": "lit_after_rev_other",
                "label": "复议后起诉_其他结果",
                "type": "int",
            },
            {
                "key": "lit_after_rev_pending",
                "label": "复议后起诉_尚未审结",
                "type": "int",
            },
            {
                "key": "lit_after_rev_total",
                "label": "复议后起诉_总计",
                "type": "int",
            },
        ],
        "rows": [
            {
                "key": "cases",
                "label": "案件数量",
                "indent": 0,
                "data": True,
            }
        ],
    },
}
