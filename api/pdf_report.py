"""
api/pdf_report.py — PDF 报告生成器

输出格式: 封面 + 考生信息 + 等效分对照 + 96 志愿表格
字体: 用 reportlab 内置 STSong(支持中文)
"""
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)


# 注册中文字体(用 reportlab 自带的 STSong-Light,无需额外字体文件)
def register_chinese_font():
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        return "STSong-Light"
    except Exception:
        return "Helvetica"


CN_FONT = register_chinese_font()


# 省份 → 考试院/招办 名 + 域名 (避免报告里硬编码"湖北")
PROVINCE_AUTHORITY = {
    "hubei": {"name": "湖北省教育考试院", "domain": "hbea.edu.cn"},
    "guangdong": {"name": "广东省教育考试院", "domain": "eea.gd.gov.cn"},
    "jiangsu": {"name": "江苏省教育考试院", "domain": "jseea.cn"},
    "beijing": {"name": "北京教育考试院", "domain": "bjeea.cn"},
    "shanghai": {"name": "上海市教育考试院", "domain": "shmeea.edu.cn"},
    "tianjin": {"name": "天津市教育招生考试院", "domain": "zhaoban.tjzhaokao.com"},
    "zhejiang": {"name": "浙江省教育考试院", "domain": "zjzs.net"},
    "shandong": {"name": "山东省教育招生考试院", "domain": "sdzk.cn"},
    "hainan": {"name": "海南省考试局", "domain": "hainan.gov.cn"},
}


def _province_cn(province: str) -> str:
    """拼音 → 中文名"""
    return {
        "hubei": "湖北", "guangdong": "广东", "jiangsu": "江苏",
        "beijing": "北京", "shanghai": "上海", "tianjin": "天津",
        "zhejiang": "浙江", "shandong": "山东", "hainan": "海南",
    }.get(province, province)


def _authority_label(province: str) -> str:
    """获取 考试院/招办 名 + 域名. 找不到时回退通用文案."""
    auth = PROVINCE_AUTHORITY.get(province)
    if auth:
        return f"{auth['name']} ({auth['domain']})"
    return f"{_province_cn(province)}省教育考试院"


# 直辖市 — 不带"省"字
MUNICIPALITIES = {"beijing", "shanghai", "tianjin", "chongqing"}


def _zhaoban_suffix(province: str) -> str:
    """直辖市 → 市, 其它 → 省. 用于'X省招办'/'X市招办'模板."""
    return "市招办" if province in MUNICIPALITIES else "省招办"


def _cn_style(name="Body", size=10, bold=False, color="#222", leading=14):
    return ParagraphStyle(
        name=name,
        fontName=CN_FONT,
        fontSize=size,
        leading=leading,
        textColor=colors.HexColor(color) if color.startswith("#") else color,
        alignment=0,  # LEFT
    )


def build_pdf_report(req, response) -> bytes:
    """把推荐响应渲染成 PDF

    Args:
        req: RecommendRequest
        response: RecommendResponse
    Returns:
        PDF bytes
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=2*cm, bottomMargin=2*cm,
        leftMargin=2*cm, rightMargin=2*cm,
        title="高考志愿推荐报告",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title", fontName=CN_FONT, fontSize=22, leading=28,
        alignment=1, textColor=colors.HexColor("#1e40af"), spaceAfter=20,
    )
    h2_style = ParagraphStyle(
        "H2", fontName=CN_FONT, fontSize=14, leading=18,
        textColor=colors.HexColor("#1e40af"), spaceBefore=14, spaceAfter=8,
    )
    body_style = _cn_style("Body", size=10)
    meta_style = _cn_style("Meta", size=10, color="#666", leading=14)
    small_style = _cn_style("Small", size=8, color="#888")

    elements = []

    # ─────── 封面 ───────
    elements.append(Spacer(1, 2*cm))
    elements.append(Paragraph("高考志愿推荐报告", title_style))
    elements.append(Paragraph(
        f"{req.province} · {req.subject}类 · {req.year}年", meta_style))
    elements.append(Spacer(1, 1*cm))

    # 考生信息卡
    s = response.student_summary
    info_data = [
        ["考生信息", ""],
        ["省份", s.get("province", req.province)],
        ["科类", s.get("subject", req.subject)],
        ["位次", f"{s.get('rank', req.rank):,}"],
        ["高考年份", str(s.get("year", req.year))],
        ["选科", s.get("xuanke", req.xuanke)],
    ]
    if s.get("student_goal"):
        info_data.append(["学生目标", s["student_goal"]])
    if s.get("family_bg"):
        info_data.append(["家庭背景", s["family_bg"]])

    info_table = Table(info_data, colWidths=[4*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), CN_FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTWEIGHT", (0, 0), (-1, 0), "BOLD"),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.5*cm))

    # 生成时间
    elements.append(Paragraph(
        f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        small_style))
    elements.append(Paragraph(
        "⚠️ 免责声明: 本报告基于位次驱动的算法 + 历史数据估算,实际录取受当年政策/计划/报考热度等多因素影响,请以省考试院官方发布为准。",
        small_style))
    elements.append(Spacer(1, 0.5*cm))

    # ─────── 统计 ───────
    elements.append(Paragraph("📊 推荐统计", h2_style))
    stat_data = [
        ["分类", "志愿数", "说明"],
        ["冲档", str(response.statistics.get("chong", 0)), "录取概率 < 30%,建议放后面"],
        ["稳档", str(response.statistics.get("wen", 0)), "录取概率 30-70%,主要志愿"],
        ["保底", str(response.statistics.get("bao", 0)), "录取概率 ≥ 70%,兜底志愿"],
        ["合计", str(response.statistics.get("total", 0)), ""],
    ]
    stat_table = Table(stat_data, colWidths=[3*cm, 3*cm, 8*cm])
    stat_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), CN_FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTWEIGHT", (0, 0), (-1, 0), "BOLD"),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#fef3c7")),  # 冲 - 黄色
        ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#d1fae5")),  # 稳 - 绿色
        ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#dbeafe")),  # 保 - 蓝色
        ("BACKGROUND", (0, 4), (-1, 4), colors.HexColor("#f8fafc")),  # 合计
    ]))
    elements.append(stat_table)
    elements.append(Spacer(1, 0.5*cm))

    # ─────── 96 志愿 ───────
    elements.append(Paragraph("🎯 96 志愿详细", h2_style))

    if not response.volunteers:
        elements.append(Paragraph("无推荐结果(可能是选科/体检/学费过严,或数据缺失)", body_style))
    else:
        # 表头
        table_data = [["#", "档", "院校", "层次", "专业组", "选科", "城市", "学费", "概率"]]
        for v in response.volunteers:
            table_data.append([
                str(v.rank),
                v.category,
                v.school_name,
                v.school_type,
                v.group_id,
                v.xuanke_req,
                v.city,
                f"{v.tuition_yuan}元",
                f"{v.est_probability * 100:.0f}%",
            ])
        n_vol = len(response.volunteers)

        # 列宽
        col_widths = [
            0.8*cm,  # #
            0.8*cm,  # 档
            5.0*cm,  # 院校
            1.0*cm,  # 层次
            1.5*cm,  # 专业组
            1.8*cm,  # 选科
            1.2*cm,  # 城市
            1.5*cm,  # 学费
            1.0*cm,  # 概率
        ]

        vol_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        style = TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), CN_FONT),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTWEIGHT", (0, 0), (-1, 0), "BOLD"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ALIGN", (2, 1), (2, -1), "LEFT"),  # 院校左对齐
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
        ])

        # 给每行染色
        for i, v in enumerate(response.volunteers, start=1):
            if v.category == "冲":
                style.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fef3c7"))
            elif v.category == "稳":
                style.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#d1fae5"))
            else:  # 保
                style.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#dbeafe"))

        vol_table.setStyle(style)
        elements.append(vol_table)
        elements.append(Spacer(1, 0.5*cm))

    # ─────── 关键建议(取前 5 条) ───────
    if response.volunteers:
        elements.append(Paragraph("💡 关键建议(冲/稳/保 各 1-2 条)", h2_style))
        # 选前 3 冲 + 前 2 稳 + 前 2 保
        samples = []
        for cat in ["冲", "稳", "保"]:
            items = [v for v in response.volunteers if v.category == cat][:2]
            samples.extend(items)
        for v in samples[:7]:
            advice = v.advice or ""
            strategy = v.strategy_note or ""
            text = f"<b>#{v.rank} {v.school_name}</b> ({v.group_id}, {v.school_type}) · 概率 {v.est_probability*100:.0f}%"
            if advice:
                text += f"<br/>&nbsp;&nbsp;💡 {advice}"
            if strategy:
                text += f"<br/>&nbsp;&nbsp;🎯 {strategy}"
            elements.append(Paragraph(text, body_style))
            elements.append(Spacer(1, 0.2*cm))

    # ─────── 数据来源 ───────
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("📚 数据来源", h2_style))
    elements.append(Paragraph(
        f"· 一分一段表: {_authority_label(req.province)} / 教育在线 (eol.cn) / 高考 100 (gk100.com)",
        body_style))
    elements.append(Paragraph(
        f"· 投档表: 高考 100 (gk100.com) 整理 + {_province_cn(req.province)}{_zhaoban_suffix(req.province)}公布数据",
        body_style))
    elements.append(Paragraph(
        "· 算法: 位次驱动 + 等效分换算 + 高斯 CDF 录取概率估算 + 张雪峰式策略加权",
        body_style))

    doc.build(elements)
    return buf.getvalue()
