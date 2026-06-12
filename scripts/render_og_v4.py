#!/usr/bin/env python3
"""
render_og_v4.py — Generate 10 Major Explorer OG cards (1080×1440, 3:4 vertical)

Style: based on 5 user-backed-up reference cards
- Top: "M·E · MAJOR EXPLORER" + "VOL. 2026"
- Title: large Chinese (serif/script) + English translation
- Subtitle: lede (4 lines max)
- Decorative rule with themed symbol
- 4 modules: 基础课 / 主要方向 / 核心技能 / 难度
- Tags row
- Bottom: 域名 + 公益 tag

Output: public/og/{slug}.png
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "public" / "og"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1080, 1440

# macOS 字体搜索路径
FONTS = [
    Path("/System/Library/Fonts/Supplemental"),
    Path("/System/Library/Fonts"),
    Path("/Library/Fonts"),
    Path("/System/Library/AssetsV2/com_apple_MobileAsset_Font8/86ba2c91f017a3749571a82f2c6d890ac7ffb2fb.asset/AssetData"),
]


def find_font(name: str) -> Path | None:
    for d in FONTS:
        if d.is_dir():
            for p in d.rglob("*"):
                if p.is_file() and name.lower() in p.name.lower():
                    return p
    return None


def font(name_substr: str, size: int) -> ImageFont.FreeTypeFont:
    p = find_font(name_substr)
    if p and p.exists():
        try:
            return ImageFont.truetype(str(p), size=size)
        except OSError:
            pass
    # 退到 STHeiti (macOS 唯一稳定中文字体)
    for fallback in ["STHeiti Medium", "STHeiti", "Times"]:
        p = find_font(fallback)
        if p and p.exists():
            try:
                return ImageFont.truetype(str(p), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


# ── 10 主题配置 ──
THEMES = {
    "cs": {
        "title": "计算机科学与技术", "title_en": "Computer Science",
        "category": "工学 · 计算机类", "duration": "4 年制", "degree": "工学学士",
        "symbol": ">", "rule": "kernel.md · 主要课程",
        "bg": (15, 18, 32), "text": (240, 240, 245), "accent": (88, 166, 255), "muted": (160, 165, 180), "stamp": (88, 166, 255),
        "difficulty": 4, "lede": "计算机不是「学编程」, 是研究信息如何被表示、存储、变换和传递的科学。数学底子 + 算法思维 + 工程能力, 就业覆盖互联网/金融科技/AI/嵌入式, 是过去十年最热本科专业。",
        "tags": ["高薪", "前沿", "数学要求高", "深造空间大", "35 岁危机", "代码友好"],
        "courses": ["数据结构", "算法分析", "计算机组成原理", "操作系统", "计算机网络", "编译原理"],
        "directions": ["软件工程 (Web/移动)", "AI/机器学习", "系统底层 (内核/驱动)", "网络空间安全", "数据科学", "游戏开发"],
        "skills": ["Python / C++ / Java", "Linux 命令行", "Git 版本控制", "算法题 (LeetCode 200+)", "数学建模", "系统设计"],
    },
    "eng": {
        "title": "机械工程", "title_en": "Mechanical Engineering",
        "category": "工学 · 机械类", "duration": "4 年制", "degree": "工学学士",
        "symbol": "▣", "rule": "DWG-001 · 主要课程",
        "bg": (235, 225, 205), "text": (40, 35, 30), "accent": (180, 80, 30), "muted": (120, 100, 80), "stamp": (180, 80, 30),
        "difficulty": 4, "lede": "机械不是「学车床」, 是研究力、热、流体和材料如何被工程化的科学。图纸 + 仿真 + 实验, 就业覆盖汽车 / 航空航天 / 能源 / 装备制造, 是中国制造业转型最需要的人才。",
        "tags": ["万金油", "越老越香", "制造业脊梁", "实践为王", "稳定就业"],
        "courses": ["理论力学", "材料力学", "机械原理", "机械设计", "热工基础", "机械制造工艺"],
        "directions": ["汽车工程 (新能源/智能车)", "航空航天 / 机器人", "能源装备 / 动力", "机械制造 / 工艺", "CAD/CAE 仿真"],
        "skills": ["SolidWorks / CATIA", "AutoCAD 工程图", "ANSYS 仿真", "金工实习 (车/铣/刨/磨)", "机械原理实验", "机械设计项目"],
    },
    "medicine": {
        "title": "临床医学", "title_en": "Clinical Medicine",
        "category": "医学 · 临床医学类", "duration": "5 年制", "degree": "医学学士",
        "symbol": "▶", "rule": "Rx · 主要课程",
        "bg": (250, 245, 235), "text": (44, 62, 80), "accent": (200, 100, 40), "muted": (140, 145, 155), "stamp": (44, 62, 80),
        "difficulty": 5, "lede": "临床医学不是「学医」, 是要成为 8-10 年后独立管病人的医生。本科 5 年 + 规培 3 年 + 专培 2-4 年, 家庭经济要扛住 30 岁前低收入, 但 35 岁后越老越值钱。",
        "tags": ["5 年制", "长学制", "35 岁后越值钱", "家庭经济要求高", "稳定", "救死扶伤"],
        "courses": ["系统解剖学", "局部解剖学", "生理学", "生物化学", "病理学", "内科学", "外科学", "妇产科学"],
        "directions": ["内科 (心血管/消化/呼吸)", "外科 (骨科/普外/心外/神外)", "妇产科 / 儿科", "急诊 / 重症 (ICU)", "麻醉 / 影像 / 检验"],
        "skills": ["体格检查 (心肺腹)", "病史采集 + 病历书写", "心电图/影像读片", "无菌操作 + 外科基本功", "医患沟通", "临床决策"],
    },
    "finance": {
        "title": "金融学", "title_en": "Finance",
        "category": "经济学 · 金融学类", "duration": "4 年制", "degree": "经济学学士",
        "symbol": "§", "rule": "Annual Report · 主要课程",
        "bg": (255, 250, 240), "text": (30, 25, 20), "accent": (180, 130, 50), "muted": (150, 140, 120), "stamp": (180, 130, 50),
        "difficulty": 4, "lede": "金融是研究资金的时间价值 + 风险定价的科学。Private Wealth · Risk & Reward。名校 (清北复交) 是入场券, 头部券商/基金 HC 极稀缺, 普通 211 金融主要去银行/保险。",
        "tags": ["高薪", "名校导向", "抗压", "考证", "卷", "资源敏感"],
        "courses": ["微观经济学", "宏观经济学", "货币银行学", "证券投资学", "公司金融", "金融衍生品"],
        "directions": ["投行 / 投研 (卖方)", "PE/VC / 资管 (买方)", "银行 (管培/客户经理)", "券商 / 基金 / 信托", "保险 / 精算"],
        "skills": ["Excel + Wind/Bloomberg", "CFA / FRM 备考", "Python 量化", "财务建模 (DCF/LBO)", "路演 + 客户沟通", "抗压 + 加班"],
    },
    "law": {
        "title": "法学", "title_en": "Law",
        "category": "法学 · 法学类", "duration": "4 年制", "degree": "法学学士",
        "symbol": "❦", "rule": "Exhibit A · 专业全貌",
        "bg": (255, 248, 235), "text": (30, 25, 20), "accent": (200, 50, 50), "muted": (140, 130, 120), "stamp": (200, 50, 50),
        "difficulty": 4, "lede": "法学是逻辑 + 表达 + 立场的训练场。法律职业极重出身 (五院四系 vs 普通 211), 法考 A 证是入场硬通货。顶尖去红圈/精品所, 中等去普通所/公司法务, 大部分转考公/转行。",
        "tags": ["逻辑", "表达", "考公", "红圈所", "法考", "卷学历"],
        "courses": ["法理学", "宪法学", "民法学", "刑法学", "行政法与行政诉讼法", "商法 / 知识产权法"],
        "directions": ["律师 (诉讼/非诉)", "公司法务 (In-house)", "公检法 (考公)", "合规 / 风控", "知识产权 / 专利代理"],
        "skills": ["法考 A 证 (硬通货)", "法律检索 (北大法宝)", "合同起草与审查", "诉讼文书", "庭审辩论", "逻辑推理"],
    },
    "gongan": {
        "title": "公安学类", "title_en": "Public Security Studies",
        "category": "法学 · 公安学类", "duration": "4 年制", "degree": "法学学士",
        "symbol": "❖", "rule": "DOSSIER · 主要课程",
        "bg": (20, 30, 60), "text": (245, 245, 245), "accent": (220, 170, 60), "muted": (170, 175, 185), "stamp": (220, 60, 60),
        "difficulty": 3, "lede": "公安学类不是「学怎么当警察」, 是研究治安/侦查/犯罪预防的应用型司法预备役。毕业生 90%+ 通过公安联考进入公安系统 (公安/国安/司法/监狱), 入警赛道最对口本科通道之一。",
        "tags": ["公安联考入警", "警务化管理", "派驻派出所", "社区警务", "应届生专属赛道"],
        "courses": ["法理学", "刑法学", "警察法学", "公安学基础", "犯罪学", "治安案件查处", "刑事侦查学"],
        "directions": ["治安学 (派出所/治安警)", "侦查学 (刑侦/经侦)", "公安法制 (案件审核)", "涉外警务 (出入境)", "智慧警务 (视频侦查)"],
        "skills": ["接处警与巡逻盘查", "治安案件查处", "群众工作与窗口接待", "警务战术与警械使用", "矛盾纠纷调解", "公安信息化"],
    },
    "education": {
        "title": "师范教育", "title_en": "Teacher Education",
        "category": "教育学 · 教育学类", "duration": "4 年制", "degree": "教育学学士",
        "symbol": "❀", "rule": "Lesson Plan · 主要课程",
        "bg": (245, 240, 230), "text": (50, 40, 30), "accent": (90, 130, 80), "muted": (140, 130, 110), "stamp": (90, 130, 80),
        "difficulty": 3, "lede": "师范不是「当老师」, 是研究「怎么学」的科学。前 2 年打底教育学原理与学科基础, 后 2 年练学科教学 + 一学期实习。毕业去中小学/教培/教育局, 想入编要等 1-3 年, 35 岁前不暴富, 35 岁后不失业。",
        "tags": ["稳定", "寒暑假", "入编要等", "公费师范", "35 岁危机小", "女生友好"],
        "courses": ["教育学原理", "教育心理学", "课程与教学论", "学科教学法", "现代教育技术", "教育研究方法"],
        "directions": ["学科教学 (中小学)", "教育学理论 (读研)", "教育管理 (教育局/校长)", "特殊教育", "学前教育 (幼师)"],
        "skills": ["试讲与微格教学", "课件制作 (PPT/希沃)", "班级管理实务", "教育研究方法", "学生心理辅导", "教学反思"],
    },
    "arts": {
        "title": "美术学", "title_en": "Fine Arts",
        "category": "艺术学 · 美术学类", "duration": "4 年制", "degree": "艺术学学士",
        "symbol": "◆", "rule": "Gallery F.001 · 主要课程",
        "bg": (240, 230, 245), "text": (35, 25, 40), "accent": (170, 120, 90), "muted": (140, 130, 150), "stamp": (170, 120, 90),
        "difficulty": 4, "lede": "美术学不是「学画画」, 是研究视觉艺术创作/批评/史论/管理的学科。央美国美是国内顶配, 美术馆/策展/拍卖是新兴方向。就业市场化, 真爱驱动, 否则慎入。",
        "tags": ["九大美院", "央美国美", "美术馆/策展", "教师编制", "美育风口"],
        "courses": ["素描 (石膏/头像/半身像)", "色彩 (水粉/水彩/油画)", "中国美术史", "外国美术史", "艺术概论", "中国画/油画/雕塑"],
        "directions": ["纯艺术 (国画/油画/雕塑)", "美术馆/博物馆策展", "艺术品拍卖与市场", "美术教育 (中小学教师)", "艺术评论与媒体"],
        "skills": ["素描/色彩扎实功底", "中国/外国美术史", "艺术评论写作", "策展与布展", "艺术市场意识", "跨学科学习"],
    },
    "business": {
        "title": "工商管理", "title_en": "Business Administration",
        "category": "管理学 · 工商管理类", "duration": "4 年制", "degree": "管理学学士",
        "symbol": "§", "rule": "Board Minutes · 主要课程",
        "bg": (235, 232, 226), "text": (30, 30, 35), "accent": (160, 50, 50), "muted": (130, 125, 120), "stamp": (160, 50, 50),
        "difficulty": 3, "lede": "工商管理是研究企业如何运作的学科 — 战略/营销/财务/人力/运营。万金油专业, 名校是真红利, 普通 211 工商管理门槛不如会计/金融, 适合有商业直觉 + 想走综合管理路线的学生。",
        "tags": ["万金油专业", "名校红利", "实践导向", "MBA 深造", "企业管培", "文理兼收"],
        "courses": ["管理学原理", "微观经济学", "宏观经济学", "市场营销学", "财务会计", "公司金融", "人力资源管理"],
        "directions": ["战略管理 (咨询/管培)", "市场营销 (品牌/数字/电商)", "人力资源 (HR/OD)", "财务管理 (CFO 路径)", "运营管理 (供应链)"],
        "skills": ["Excel + 商业分析", "PPT / 商业写作", "案例分析 (Case Interview)", "商业谈判", "团队管理", "MBA 规划"],
    },
    "sci": {
        "title": "数学与应用数学", "title_en": "Mathematics & Applied Math",
        "category": "理学 · 数学类", "duration": "4 年制", "degree": "理学学士",
        "symbol": "¶", "rule": "Vol.50 · 主要课程",
        "bg": (235, 240, 245), "text": (20, 30, 40), "accent": (60, 110, 160), "muted": (130, 140, 150), "stamp": (60, 110, 160),
        "difficulty": 5, "lede": "数学不是「算数学」, 是研究数量、结构、变化和空间的科学。本科 4 年是真功夫, 70% 读研是常态。本科直接就业偏窄 (中小学教师/数据分析), 真正的舞台是硕士博士 + 金融/算法/科研。",
        "tags": ["基础学科", "深造率高", "万金油", "数学底子", "竞赛友好", "慢热型"],
        "courses": ["数学分析 (微积分)", "高等代数", "解析几何", "常微分方程", "实变函数", "概率论与数理统计"],
        "directions": ["纯数学 (读博进高校)", "应用数学 (金融/工程)", "统计学 (数据科学)", "运筹学与控制论", "数学教育 (中小学教师)"],
        "skills": ["数学证明 (严谨逻辑)", "抽象思维", "Python 数值计算 (NumPy)", "LaTeX 论文排版", "统计建模 (R/Stata)", "数学竞赛 (CMO/Putnam)"],
    },
}


def wrap_text(text: str, font_obj, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """按字符级 wrap, 用 draw.textlength 检查实际宽度."""
    lines = []
    current = ""
    for char in text:
        test = current + char
        if draw.textlength(test, font=font_obj) > max_width and current:
            lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def render_card(theme: dict, slug: str) -> None:
    img = Image.new("RGB", (W, H), color=theme["bg"])
    draw = ImageDraw.Draw(img)

    me_font = font("STHeiti", 30)
    title_font = font("STHeiti Medium", 160)   # 中粗 (标题大字, 智能 wrap)
    title_en_font = font("Times", 50)          # 西文衬线
    body_font = font("STHeiti", 28)            # 正文 (略小避免拥挤)
    tag_font = font("STHeiti", 24)             # 标签
    stamp_font = font("STHeiti Medium", 105)   # 印章首字
    small_font = font("STHeiti", 22)

    # ── 顶部: 品牌 + 卷号 ──
    draw.text((80, 80), "M·E · MAJOR EXPLORER", font=me_font, fill=theme["accent"])
    vol_font = font("Bodoni", 32)
    vol_text = "VOL. 2026"
    vol_w = draw.textlength(vol_text, font=vol_font)
    draw.text((W - 80 - vol_w, 85), vol_text, font=vol_font, fill=theme["muted"])
    draw.rectangle([(80, 140), (W - 80, 142)], fill=theme["accent"])

    # ── 标题区 ──
    # 印章首字 (左侧 130×130 方框)
    first_char = theme["title"][0]
    box_x, box_y, box_size = 80, 190, 130
    draw.rectangle([(box_x, box_y), (box_x + box_size, box_y + box_size)], outline=theme["stamp"], width=4)
    cb = draw.textbbox((0, 0), first_char, font=stamp_font)
    cw, ch = cb[2] - cb[0], cb[3] - cb[1]
    draw.text(
        (box_x + (box_size - cw) // 2 - cb[0], box_y + (box_size - ch) // 2 - cb[1]),
        first_char, font=stamp_font, fill=theme["stamp"],
    )

    # 主标题 (右侧, 智能 wrap 2 行, 不截断)
    title_x = 250
    title_y = 200
    max_title_w = W - title_x - 80   # 右 margin 80
    if draw.textlength(theme["title"], font=title_font) <= max_title_w:
        draw.text((title_x, title_y), theme["title"], font=title_font, fill=theme["text"])
        title_bottom = title_y + 175
    else:
        # Wrap 到 2 行, 找最接近中点的可拆点
        best = 0
        for s in range(len(theme["title"]) // 2, len(theme["title"])):
            if draw.textlength(theme["title"][:s], font=title_font) <= max_title_w:
                best = s
        draw.text((title_x, title_y), theme["title"][:best], font=title_font, fill=theme["text"])
        draw.text((title_x, title_y + 175), theme["title"][best:], font=title_font, fill=theme["text"])
        title_bottom = title_y + 360

    # 英文翻译
    draw.text((title_x, title_bottom + 15), theme["title_en"], font=title_en_font, fill=theme["accent"])
    # 学科 + 学制 + 学位
    draw.text(
        (title_x, title_bottom + 85),
        f"{theme['category']} · {theme['duration']} · {theme['degree']}",
        font=tag_font, fill=theme["muted"],
    )
    title_end_y = title_bottom + 130

    # ── 副标题: lede (3 行 max) ──
    lede_y = max(title_end_y + 40, 530)
    lede_lines = wrap_text(theme["lede"], body_font, W - 160, draw)
    for i, line in enumerate(lede_lines[:3]):
        draw.text((80, lede_y + i * 44), line, font=body_font, fill=theme["text"])

    # ── 装饰分割线 (主题符号) ──
    rule_y = lede_y + len(lede_lines[:3]) * 44 + 30
    rule_text = f"{theme['symbol']}  {theme['rule']}"
    draw.text((80, rule_y), rule_text, font=body_font, fill=theme["accent"])
    draw.rectangle([(80, rule_y + 40), (W - 80, rule_y + 41)], fill=theme["accent"])

    # ── 4 模块 ──
    module_y = rule_y + 70
    mod_h = 95
    sections = [
        ("基础课", theme["courses"]),
        ("主要方向", theme["directions"]),
        ("核心技能", theme["skills"]),
    ]
    for i, (title, items) in enumerate(sections):
        y = module_y + i * mod_h
        draw.text((80, y), title, font=tag_font, fill=theme["muted"])
        content = " · ".join(items[:3])
        content_lines = wrap_text(content, body_font, W - 160, draw)
        for j, line in enumerate(content_lines[:2]):
            draw.text((80, y + 32 + j * 38), line, font=body_font, fill=theme["text"])

    # ── 难度 ──
    diff_y = module_y + mod_h * 3 + 12
    draw.text((80, diff_y), "难度", font=tag_font, fill=theme["muted"])
    star_str = "★" * theme["difficulty"] + "☆" * (5 - theme["difficulty"])
    star_font = font("STHeiti Medium", 38)
    draw.text((165, diff_y - 10), star_str, font=star_font, fill=theme["accent"])

    # ── 标签 (tags) ──
    tag_y = diff_y + 50
    tag_x = 80
    for tag in theme["tags"][:5]:
        tw = draw.textlength(tag, font=tag_font) + 28
        draw.rectangle([(tag_x, tag_y), (tag_x + tw, tag_y + 40)], outline=theme["accent"], width=2)
        draw.text((tag_x + 14, tag_y + 6), tag, font=tag_font, fill=theme["text"])
        tag_x += tw + 10

    # ── 底部: 域名 + 公益 (固定位置, 不重叠) ──
    footer_y = H - 90
    draw.rectangle([(80, footer_y), (W - 80, footer_y + 2)], fill=theme["muted"])
    domain_font = font("Times", 28)
    draw.text((80, footer_y + 20), "majorexplorer.com", font=domain_font, fill=theme["text"])
    donate_w = 120
    draw.rectangle([(W - 80 - donate_w, footer_y + 12), (W - 80, footer_y + 52)], fill=theme["accent"])
    draw.text((W - 80 - donate_w + 24, footer_y + 20), "公 益", font=font("STHeiti", 22), fill=theme["bg"])

    # 保存
    out_path = OUT / f"{slug}.png"
    img.save(out_path, "PNG", optimize=True)
    print(f"✅ {slug:14s} → {out_path.name:30s} ({(out_path.stat().st_size/1024):.0f} KB)")


def main():
    for slug, theme in THEMES.items():
        render_card(theme, slug)
    print(f"\n✅ Done: {len(THEMES)} cards in {OUT}")


if __name__ == "__main__":
    main()
