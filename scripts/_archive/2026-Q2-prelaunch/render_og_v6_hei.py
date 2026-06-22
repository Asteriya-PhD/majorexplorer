#!/usr/bin/env python3
"""
render_og_v6.py — Major Explorer OG cards v6 (杂志内页分栏)

基于 v5 重做 layout, 解决"精致度不够"反馈:
  - 课程区: 3 行 vertical → 3 列 grid (基础课 | 主要方向 | 核心技能)
  - 元数据(学制/难度/学科): 标题下 → 底部 3 列 grid (info panel, 杂志风)
  - tags: outline 框 → 实心填充 (accent 色 + bg 色文字)
  - 加 EXHIBIT A 期刊小标题 (Bodoni 24pt, ALL CAPS, muted 色)
  - 课程列间加竖线 (1px) 分隔
  - 域名: 36pt → 40pt (更突出)
  - 标题: 智能字号 (150/130/110/95pt) 解决 7+ 字 wrap 问题

v5 保留: 圆形印章 / Songti 衬线 / Drop Cap / 主题装饰 / 居中域名 / 纹理

用法: 同 v5
  python3 scripts/render_og_v6.py --only cs medicine finance
"""
from __future__ import annotations
import argparse
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "public" / "og"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1080, 1440

FONT_DIRS = [
    Path("/System/Library/Fonts/Supplemental"),
    Path("/System/Library/Fonts"),
    Path("/Library/Fonts"),
]


def find_font(name: str) -> Path | None:
    for d in FONT_DIRS:
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
    for fb in ["STHeiti Medium", "STHeiti Medium", "STHeiti", "Times"]:
        p = find_font(fb)
        if p and p.exists():
            try:
                return ImageFont.truetype(str(p), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


# ── 主题配置 (10 张全量, 复用 v5) ──
THEMES = {
    "cs": {
        "title": "计算机科学与技术", "title_en": "Computer Science",
        "category": "工学 · 计算机类", "duration": "4 年制", "degree": "工学学士",
        "symbol": ">", "rule": "kernel.md · 主要课程", "exhibit": "EXHIBIT A · COURSE BRIEF",
        "bg": (15, 18, 32), "text": (240, 240, 245), "accent": (88, 166, 255), "muted": (160, 165, 180), "stamp": (88, 166, 255),
        "difficulty": 4, "lede": "计算机不是「学编程」, 是研究信息如何被表示、存储、变换和传递的科学。数学底子 + 算法思维 + 工程能力, 就业覆盖互联网/金融科技/AI/嵌入式, 是过去十年最热本科专业。",
        "tags": ["高薪", "前沿", "数学要求高", "深造空间大", "35 岁危机", "代码友好"],
        "courses": ["数据结构", "算法分析", "计算机组成原理", "操作系统", "计算机网络", "编译原理"],
        "directions": ["软件工程 (Web/移动)", "AI/机器学习", "系统底层 (内核/驱动)", "网络空间安全", "数据科学", "游戏开发"],
        "skills": ["Python / C++ / Java", "Linux 命令行", "Git 版本控制", "算法题 (LeetCode 200+)", "数学建模", "系统设计"],
    },
    "medicine": {
        "title": "临床医学", "title_en": "Clinical Medicine",
        "category": "医学 · 临床医学类", "duration": "5 年制", "degree": "医学学士",
        "symbol": "▶", "rule": "Rx · 主要课程", "exhibit": "EXHIBIT A · COURSE BRIEF",
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
        "symbol": "§", "rule": "Annual Report · 主要课程", "exhibit": "EXHIBIT A · COURSE BRIEF",
        "bg": (255, 250, 240), "text": (30, 25, 20), "accent": (180, 130, 50), "muted": (150, 140, 120), "stamp": (180, 130, 50),
        "difficulty": 4, "lede": "金融是研究资金的时间价值 + 风险定价的科学。Private Wealth · Risk & Reward。名校 (清北复交) 是入场券, 头部券商/基金 HC 极稀缺, 普通 211 金融主要去银行/保险。",
        "tags": ["高薪", "名校导向", "抗压", "考证", "卷", "资源敏感"],
        "courses": ["微观经济学", "宏观经济学", "货币银行学", "证券投资学", "公司金融", "金融衍生品"],
        "directions": ["投行 / 投研 (卖方)", "PE/VC / 资管 (买方)", "银行 (管培/客户经理)", "券商 / 基金 / 信托", "保险 / 精算"],
        "skills": ["Excel + Wind/Bloomberg", "CFA / FRM 备考", "Python 量化", "财务建模 (DCF/LBO)", "路演 + 客户沟通", "抗压 + 加班"],
    },
    "eng": {
        "title": "机械工程", "title_en": "Mechanical Engineering",
        "category": "工学 · 机械类", "duration": "4 年制", "degree": "工学学士",
        "symbol": "▣", "rule": "DWG-001 · 主要课程", "exhibit": "EXHIBIT A · COURSE BRIEF",
        "bg": (235, 225, 205), "text": (40, 35, 30), "accent": (180, 80, 30), "muted": (120, 100, 80), "stamp": (180, 80, 30),
        "difficulty": 4, "lede": "机械不是「学车床」, 是研究力、热、流体和材料如何被工程化的科学。图纸 + 仿真 + 实验, 就业覆盖汽车 / 航空航天 / 能源 / 装备制造, 是中国制造业转型最需要的人才。",
        "tags": ["万金油", "越老越香", "制造业脊梁", "实践为王", "稳定就业"],
        "courses": ["理论力学", "材料力学", "机械原理", "机械设计", "热工基础", "机械制造工艺"],
        "directions": ["汽车工程 (新能源/智能车)", "航空航天 / 机器人", "能源装备 / 动力", "机械制造 / 工艺", "CAD/CAE 仿真"],
        "skills": ["SolidWorks / CATIA", "AutoCAD 工程图", "ANSYS 仿真", "金工实习 (车/铣/刨/磨)", "机械原理实验", "机械设计项目"],
    },
    "law": {
        "title": "法学", "title_en": "Law",
        "category": "法学 · 法学类", "duration": "4 年制", "degree": "法学学士",
        "symbol": "❦", "rule": "Exhibit A · 专业全貌", "exhibit": "EXHIBIT A · COURSE BRIEF",
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
        "symbol": "❖", "rule": "DOSSIER · 主要课程", "exhibit": "EXHIBIT A · COURSE BRIEF",
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
        "symbol": "❀", "rule": "Lesson Plan · 主要课程", "exhibit": "EXHIBIT A · COURSE BRIEF",
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
        "symbol": "◆", "rule": "Gallery F.001 · 主要课程", "exhibit": "EXHIBIT A · COURSE BRIEF",
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
        "symbol": "§", "rule": "Board Minutes · 主要课程", "exhibit": "EXHIBIT A · COURSE BRIEF",
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
        "symbol": "¶", "rule": "Vol.50 · 主要课程", "exhibit": "EXHIBIT A · COURSE BRIEF",
        "bg": (235, 240, 245), "text": (20, 30, 40), "accent": (60, 110, 160), "muted": (130, 140, 150), "stamp": (60, 110, 160),
        "difficulty": 5, "lede": "数学不是「算数学」, 是研究数量、结构、变化和空间的科学。本科 4 年是真功夫, 70% 读研是常态。本科直接就业偏窄 (中小学教师/数据分析), 真正的舞台是硕士博士 + 金融/算法/科研。",
        "tags": ["基础学科", "深造率高", "万金油", "数学底子", "竞赛友好", "慢热型"],
        "courses": ["数学分析 (微积分)", "高等代数", "解析几何", "常微分方程", "实变函数", "概率论与数理统计"],
        "directions": ["纯数学 (读博进高校)", "应用数学 (金融/工程)", "统计学 (数据科学)", "运筹学与控制论", "数学教育 (中小学教师)"],
        "skills": ["数学证明 (严谨逻辑)", "抽象思维", "Python 数值计算 (NumPy)", "LaTeX 论文排版", "统计建模 (R/Stata)", "数学竞赛 (CMO/Putnam)"],
    },
}


def wrap_text(text: str, font_obj, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
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


# ── 装饰函数 (复用 v5) ──

def apply_paper_texture(img: Image.Image, density: int = 500, alpha: int = 8) -> None:
    random.seed(42)
    noise = Image.new("RGBA", img.size, (0, 0, 0, 0))
    nd = ImageDraw.Draw(noise)
    for _ in range(density):
        x = random.randint(0, img.width - 1)
        y = random.randint(0, img.height - 1)
        c = random.choice([(255, 255, 255, alpha), (0, 0, 0, alpha)])
        nd.point((x, y), fill=c)
    img.paste(noise, (0, 0), noise)


def draw_stamp_circle(draw, cx: int, cy: int, radius: int, char: str,
                      color: tuple, fill_color=None) -> None:
    """圆形篆刻风印章 (v6: 支持 fill_color 实心印章)."""
    if fill_color:
        draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)],
                     fill=fill_color, outline=color, width=4)
    else:
        draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)],
                     outline=color, width=4)
    draw.ellipse([(cx - radius + 8, cy - radius + 8),
                  (cx + radius - 8, cy + radius - 8)],
                 outline=color, width=1)
    stamp_font = font("STHeiti Medium", int(radius * 1.5))
    bbox = draw.textbbox((0, 0), char, font=stamp_font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    text_color = theme_bg_contrast(fill_color) if fill_color else color
    draw.text(
        (cx - tw // 2 - bbox[0], cy - th // 2 - bbox[1] - 6),
        char, font=stamp_font, fill=text_color,
    )


def theme_bg_contrast(color: tuple) -> tuple:
    """印章文字: 实心印章用对比色, 否则用 stamp 色."""
    avg = sum(color) / 3 if color else 128
    return (255, 255, 255) if avg < 128 else (30, 25, 20)


def draw_lede_with_dropcap(draw, lede: str, x: int, y: int, max_w: int,
                            body_font, color: tuple, max_lines: int = 3) -> int:
    """lede 渲染: 首字 Drop Cap (Songti 60pt) + 后续行全部缩进到 cap_w 之后 (避免与 Drop Cap 重叠)."""
    if not lede:
        return 0
    first = lede[0]
    rest = lede[1:]
    cap_size = 60
    cap_font = font("STHeiti Medium", cap_size)
    line_h = 44

    # Drop Cap 占位宽 (60pt 衬线中文 ≈ 60px, +14 padding)
    cap_w = int(draw.textlength(first, font=cap_font)) + 14

    # 所有行都用 sub_w (max_w - cap_w), 保持缩进对齐
    sub_w = max_w - cap_w
    all_lines = wrap_text(rest, body_font, sub_w, draw)[:max_lines]
    if not all_lines:
        return 0

    # 绘制 Drop Cap (左侧大字)
    draw.text((x, y - 6), first, font=cap_font, fill=color)

    # 绘制后续行 (全部从 cap_w 右侧开始, 缩进对齐)
    for i, line in enumerate(all_lines):
        cur_y = y + i * line_h
        draw.text((x + cap_w, cur_y), line, font=body_font, fill=color)

    return len(all_lines) * line_h


def draw_hr_card(draw, x: int, y: int, w: int, h: int,
                 accent: tuple, bg: tuple, text: tuple) -> None:
    draw.rectangle([(x + 4, y + 6), (x + w + 4, y + h + 6)], fill=(0, 0, 0, 30))
    avg_bg = sum(bg) / 3
    if avg_bg < 128:
        bg_card = tuple(min(255, c + 8) for c in bg)
    else:
        bg_card = tuple(max(0, c - 6) for c in bg)
    draw.rectangle([(x, y), (x + w, y + h)], fill=bg_card, outline=accent, width=2)
    label_font = font("Bodoni", 18)
    draw.text((x + 16, y + 14), "HR", font=label_font, fill=accent)
    big_font = font("Bodoni", 56)
    draw.text((x + 16, y + 40), "72", font=big_font, fill=text)
    unit_font = font("STHeiti", 18)
    draw.text((x + 110, y + 70), "bpm", font=unit_font, fill=accent)
    status_font = font("STHeiti", 14)
    draw.text((x + w - 90, y + 18), "NORMAL", font=status_font, fill=accent)
    wave_y = y + h - 18
    pts = [0, -4, 6, -16, 4, 0, 0, 0]
    for i, h_off in enumerate(pts):
        sx = x + 16 + i * 11
        if sx + 8 > x + w - 10:
            break
        draw.line([(sx, wave_y), (sx + 8, wave_y + h_off)], fill=accent, width=2)


def draw_watermark_ME(img: Image.Image, w: int, h: int, color: tuple, alpha_val: int = 32,
                      font_size: int = 380, y_offset: int = 80) -> None:
    """大 ME 水印 (alpha 混合, 不抢戏)."""
    wm_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    wd = ImageDraw.Draw(wm_layer)
    wm_font = font("Bodoni", font_size)
    bbox = wd.textbbox((0, 0), "M", font=wm_font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (w - tw) // 2 - bbox[0]
    y = (h - th) // 2 - bbox[1] + y_offset  # y_offset 越大越靠下
    wd.text((x, y), "M", font=wm_font, fill=color + (alpha_val,))
    img.paste(wm_layer, (0, 0), wm_layer)


# ── v6 新增函数 ──

def smart_title_size(draw, title: str, max_w: int, sizes=(150, 130, 110, 95)) -> int:
    """智能字号: 在 sizes 列表中找最大能 fit 单行的字号."""
    for sz in sizes:
        f = font("STHeiti Medium", sz)
        if draw.textlength(title, font=f) <= max_w:
            return sz
    return sizes[-1]


def draw_exhibit_label(draw, x: int, y: int, text: str, accent: tuple,
                       muted: tuple) -> None:
    """EXHIBIT A · COURSE BRIEF (期刊小标题, Bodoni 衬线, ALL CAPS 英文)."""
    label_font = font("Bodoni", 26)
    # 左侧短线
    draw.rectangle([(x, y + 14), (x + 28, y + 16)], fill=accent)
    # 文字 (ALL CAPS 英文, Bodoni 支持)
    draw.text((x + 38, y), text, font=label_font, fill=muted)


def draw_3col_course_grid(draw, x: int, y: int, w: int, h: int,
                          courses: list, directions: list, skills: list,
                          accent: tuple, text: tuple, muted: tuple,
                          bg: tuple) -> None:
    """3 列课程 grid (基础课 | 主要方向 | 核心技能)."""
    col_w = w // 3
    # 标题行
    title_font = font("STHeiti Medium", 28)
    col_titles = ["基础课", "主要方向", "核心技能"]
    for i, t in enumerate(col_titles):
        cx = x + i * col_w + 20
        draw.text((cx, y), t, font=title_font, fill=accent)
        # 标题下短线
        draw.rectangle([(cx, y + 40), (cx + col_w - 40, y + 42)], fill=accent)
    # 列间竖线 (金色 1px)
    for i in range(1, 3):
        lx = x + i * col_w
        draw.line([(lx, y + 8), (lx, y + h - 8)], fill=muted, width=1)
    # 内容
    body_font = font("STHeiti", 24)
    col_items = [courses, directions, skills]
    for i, items in enumerate(col_items):
        cx = x + i * col_w + 20
        for j, item in enumerate(items[:4]):
            line_y = y + 70 + j * 46
            if line_y + 30 > y + h:
                break
            # 项目符号 (小方块)
            draw.rectangle([(cx, line_y + 10), (cx + 6, line_y + 16)], fill=accent)
            # 文字
            draw.text((cx + 16, line_y), item, font=body_font, fill=text)


def draw_meta_grid(draw, x: int, y: int, w: int, h: int,
                   duration: str, degree: str, difficulty: int,
                   category: str, accent: tuple, text: tuple,
                   muted: tuple, bg: tuple) -> None:
    """底部 3 列元数据 grid (学制·学位 | 难度 | 学科门类) — 杂志 info panel."""
    col_w = w // 3
    # 外框 (细线)
    draw.rectangle([(x, y), (x + w, y + h)], outline=muted, width=1)
    # 列间竖线
    for i in range(1, 3):
        lx = x + i * col_w
        draw.line([(lx, y + 8), (lx, y + h - 8)], fill=muted, width=1)

    big_font = font("STHeiti Medium", 42)
    label_font = font("STHeiti", 22)
    star_font = font("STHeiti Medium", 36)

    # ── 第 1 列: 学制·学位 (大字数字 + 紧跟"年制"小字) ──
    val_num = duration.replace(" 年制", "")  # "4"
    num_bbox = draw.textbbox((0, 0), val_num, font=big_font)
    num_w = num_bbox[2] - num_bbox[0]
    # 居中: "4" + 8px + "年制"
    unit_w = draw.textlength("年制", font=label_font)
    total_w = num_w + 8 + unit_w
    start_x = x + col_w // 2 - int(total_w) // 2
    draw.text((start_x, y + 22), val_num, font=big_font, fill=text)
    draw.text((start_x + num_w + 8, y + 40), "年制", font=label_font, fill=muted)
    # 学位 (下方一行, 居中)
    deg_w = draw.textlength(degree, font=label_font)
    draw.text((x + col_w // 2 - deg_w // 2, y + h - 36), degree,
              font=label_font, fill=muted)

    # ── 第 2 列: 难度 ──
    star_str = "★" * difficulty + "☆" * (5 - difficulty)
    star_bbox = draw.textbbox((0, 0), star_str, font=star_font)
    sw = star_bbox[2] - star_bbox[0]
    draw.text((x + col_w + (col_w - sw) // 2 - star_bbox[0], y + 28),
              star_str, font=star_font, fill=accent)
    # 学术深度·N/5 颗星 (居中)
    sub2 = f"学术深度 · {difficulty} / 5 颗星"
    sub2_w = draw.textlength(sub2, font=label_font)
    draw.text((x + col_w + col_w // 2 - sub2_w // 2, y + h - 36),
              sub2, font=label_font, fill=muted)

    # ── 第 3 列: 学科门类 ──
    parts = category.split(" · ")
    if len(parts) == 2:
        cat_main, cat_sub = parts
        # 主门类 (大字, 居中)
        cat_w = draw.textlength(cat_main, font=big_font)
        draw.text((x + 2 * col_w + col_w // 2 - cat_w // 2, y + 22),
                  cat_main, font=big_font, fill=text)
        # 二级分类 (居中)
        sub_w = draw.textlength(cat_sub, font=label_font)
        draw.text((x + 2 * col_w + col_w // 2 - sub_w // 2, y + h - 36),
                  cat_sub, font=label_font, fill=muted)


def draw_solid_tags(draw, x: int, y: int, tags: list,
                    accent: tuple, bg: tuple) -> int:
    """实心填充 tags (accent 色 + bg 反色文字)."""
    tag_font = font("STHeiti Medium", 22)
    cur_x = x
    cur_y = y
    line_h = 50
    max_x = W - 80
    for tag in tags:
        tw = draw.textlength(tag, font=tag_font) + 28
        if cur_x + tw > max_x:
            cur_x = x
            cur_y += line_h
        # 实心填充
        draw.rectangle([(cur_x, cur_y), (cur_x + tw, cur_y + 38)],
                       fill=accent)
        draw.text((cur_x + 14, cur_y + 6), tag, font=tag_font, fill=bg)
        cur_x += tw + 10
    return cur_y + 38 - y  # total height used


# ── 主渲染 v6 ──

def draw_eng_blueprint(draw, x: int, y: int, w: int, h: int,
                       accent: tuple, muted: tuple) -> None:
    """工程蓝图角标 (eng 主题: DWG-001 + 简化齿轮, 左上 DWG-001, 右上单独显示 MECH)."""
    # 矩形外框 (细线)
    draw.rectangle([(x, y), (x + w, y + h)], outline=accent, width=1)
    # 标题 "DWG-001" (左上, 大字)
    title_font = font("Bodoni", 22)
    draw.text((x + 14, y + 10), "DWG-001", font=title_font, fill=accent)
    # 副标 "MECH" (DWG-001 下方, 留足间距)
    sub_font = font("Bodoni", 12)
    draw.text((x + 14, y + 38), "MECH", font=sub_font, fill=muted)
    # 简化齿轮 (右侧)
    cy = y + h // 2 + 8
    cx = x + int(w * 0.65)
    draw.ellipse([(cx - 28, cy - 28), (cx + 28, cy + 28)],
                 outline=accent, width=2)
    draw.ellipse([(cx - 14, cy - 14), (cx + 14, cy + 14)],
                 outline=accent, width=1)
    # 中心十字
    draw.line([(cx, cy - 24), (cx, cy + 24)], fill=accent, width=1)
    draw.line([(cx - 24, cy), (cx + 24, cy)], fill=accent, width=1)
    # 左下角小标签
    label_font = font("STHeiti", 14)
    draw.text((x + 14, y + h - 22), "SCALE 1:1", font=label_font, fill=muted)


def draw_law_filing_stamp(draw, cx: int, cy: int, r: int, color: tuple) -> None:
    """已立案 2026 圆形红印 (law 主题, 实心填充 + 内嵌 4 字)."""
    # 外圆 (实心填充)
    avg = sum(color) / 3
    bg_text = (255, 255, 255) if avg < 128 else (30, 25, 20)
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)],
                 fill=color, outline=bg_text, width=3)
    # 内圆 (细线)
    draw.ellipse([(cx - r + 10, cy - r + 10), (cx + r - 10, cy + r - 10)],
                 outline=bg_text, width=1)
    # 上方 "已立案" (小字)
    top_font = font("STHeiti Medium", 16)
    top_text = "已立案"
    tw = draw.textlength(top_text, font=top_font)
    draw.text((cx - tw // 2, cy - r + 22), top_text, font=top_font, fill=bg_text)
    # 中央 "2026" (大字, 篆刻感)
    big_font = font("Bodoni", 30)
    big_text = "2026"
    big_bbox = draw.textbbox((0, 0), big_text, font=big_font)
    bw, bh = big_bbox[2] - big_bbox[0], big_bbox[3] - big_bbox[1]
    draw.text((cx - bw // 2 - big_bbox[0], cy - bh // 2 - big_bbox[1] - 4),
              big_text, font=big_font, fill=bg_text)
    # 下方 "EXHIBIT" (小字)
    bot_text = "EXHIBIT"
    bot_font = font("Bodoni", 14)
    bw2 = draw.textlength(bot_text, font=bot_font)
    draw.text((cx - bw2 // 2, cy + r - 30), bot_text, font=bot_font, fill=bg_text)


def draw_gongan_dossier(draw, x: int, y: int, w: int, h: int,
                        accent: tuple, muted: tuple, text: tuple) -> None:
    """DOSSIER 警务档案 (gongan 主题: 六边形 P 徽章 + 档案号)."""
    # 矩形外框
    draw.rectangle([(x, y), (x + w, y + h)], outline=accent, width=1)
    # 顶部: DOSSIER
    title_font = font("Bodoni", 22)
    draw.text((x + 14, y + 8), "DOSSIER", font=title_font, fill=accent)
    # 右上: 030600
    sub_font = font("Bodoni", 16)
    draw.text((x + w - 76, y + 12), "· 030600", font=sub_font, fill=muted)
    # 中央: 六边形 P 徽章
    cx, cy, r = x + w // 2, y + h // 2 + 12, 30
    # 6 顶点
    import math
    pts = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(pts, outline=accent, width=2)
    # P 字
    p_font = font("Bodoni", 38)
    p_bbox = draw.textbbox((0, 0), "P", font=p_font)
    pw, ph = p_bbox[2] - p_bbox[0], p_bbox[3] - p_bbox[1]
    draw.text((cx - pw // 2 - p_bbox[0], cy - ph // 2 - p_bbox[1] - 4),
              "P", font=p_font, fill=text)
    # 底部: PUBLIC SECURITY
    bot_font = font("Bodoni", 12)
    bot_text = "PUBLIC SECURITY"
    bw = draw.textlength(bot_text, font=bot_font)
    draw.text((x + w // 2 - bw // 2, y + h - 18),
              bot_text, font=bot_font, fill=muted)


def draw_edu_lesson_card(draw, x: int, y: int, w: int, h: int,
                         accent: tuple, text: tuple, muted: tuple) -> None:
    """教案 Lesson Plan 卡 (education 主题: 3 个打勾)."""
    # 矩形外框
    draw.rectangle([(x, y), (x + w, y + h)], outline=accent, width=1)
    # 标题 "LESSON PLAN"
    title_font = font("Bodoni", 18)
    draw.text((x + 14, y + 8), "LESSON PLAN", font=title_font, fill=accent)
    # 右上: 时长
    sub_font = font("STHeiti", 14)
    draw.text((x + w - 60, y + 12), "45 min", font=sub_font, fill=muted)
    # 3 个打勾
    check_items = ["学科基础", "试讲练习", "教育实习"]
    cy = y + 36
    for item in check_items:
        # ✓ 符号
        ck_font = font("STHeiti Medium", 24)
        draw.text((x + 14, cy), "✓", font=ck_font, fill=accent)
        # 文字
        item_font = font("STHeiti", 18)
        draw.text((x + 38, cy + 2), item, font=item_font, fill=text)
        # 横线
        draw.rectangle([(x + 38, cy + 26), (x + w - 14, cy + 27)], fill=muted)
        cy += 22


def draw_arts_gallery(draw, x: int, y: int, w: int, h: int,
                      accent: tuple, muted: tuple) -> None:
    """美术馆 Gallery Wall (arts 主题: 3 个空相框)."""
    # 矩形外框
    draw.rectangle([(x, y), (x + w, y + h)], outline=accent, width=1)
    # 标题 "GALLERY"
    title_font = font("Bodoni", 20)
    draw.text((x + 14, y + 8), "GALLERY", font=title_font, fill=accent)
    # 右上 "F.001"
    sub_font = font("Bodoni", 16)
    draw.text((x + w - 60, y + 12), "F.001", font=sub_font, fill=muted)
    # 3 个相框 (大小不一, 像美术馆)
    frame_y = y + 38
    frame_h = h - 50
    # 框 1 (大, 左)
    f1_w = int(w * 0.32)
    draw.rectangle([(x + 14, frame_y), (x + 14 + f1_w, frame_y + frame_h)],
                   outline=accent, width=2)
    draw.rectangle([(x + 18, frame_y + 4), (x + 10 + f1_w, frame_y + frame_h - 4)],
                   outline=muted, width=1)
    # 框 2 (中, 中)
    f2_x = x + 14 + f1_w + 12
    f2_w = int(w * 0.28)
    draw.rectangle([(f2_x, frame_y), (f2_x + f2_w, frame_y + frame_h - 8)],
                   outline=accent, width=2)
    # 框 3 (小, 右)
    f3_x = f2_x + f2_w + 12
    f3_w = x + w - 14 - f3_x
    draw.rectangle([(f3_x, frame_y + 4), (f3_x + f3_w, frame_y + frame_h - 4)],
                   outline=accent, width=2)


def draw_business_minutes(draw, x: int, y: int, w: int, h: int,
                          accent: tuple, muted: tuple, text: tuple) -> None:
    """董事会议 Board Minutes (business 主题: § 大符号 + 议程)."""
    # 矩形外框
    draw.rectangle([(x, y), (x + w, y + h)], outline=accent, width=1)
    # 标题
    title_font = font("Bodoni", 20)
    draw.text((x + 14, y + 8), "BOARD MINUTES", font=title_font, fill=accent)
    # 右上 "Q4 · 2026"
    sub_font = font("Bodoni", 14)
    draw.text((x + w - 80, y + 12), "Q4 · 2026", font=sub_font, fill=muted)
    # 大 § 符号 (中央偏左)
    big_font = font("Bodoni", 64)
    draw.text((x + 16, y + 32), "§", font=big_font, fill=accent)
    # 右侧议程 3 项
    items = ["战略回顾", "财务审批", "人事决议"]
    item_font = font("STHeiti", 18)
    for i, item in enumerate(items):
        iy = y + 38 + i * 22
        # 编号
        num_font = font("Bodoni", 14)
        draw.text((x + 80, iy), f"{i+1:02d}.", font=num_font, fill=muted)
        # 项目
        draw.text((x + 110, iy), item, font=item_font, fill=text)


def draw_sci_volume(draw, x: int, y: int, w: int, h: int,
                    accent: tuple, muted: tuple, text: tuple) -> None:
    """期刊 Vol.50 banner (sci 主题)."""
    # 矩形外框
    draw.rectangle([(x, y), (x + w, y + h)], outline=accent, width=1)
    # 顶部 "JOURNAL · 数学学报"
    title_font = font("Bodoni", 16)
    draw.text((x + 14, y + 8), "JOURNAL · MATHEMATICA", font=title_font, fill=accent)
    # 右上 "ISSN"
    sub_font = font("Bodoni", 12)
    draw.text((x + w - 70, y + 12), "ISSN 1000-IX", font=sub_font, fill=muted)
    # 大 "Vol. 50"
    big_font = font("Bodoni", 38)
    draw.text((x + 14, y + 32), "Vol. 50", font=big_font, fill=text)
    # 右侧 "2026 · NO. 06"
    right_font = font("STHeiti", 18)
    draw.text((x + 130, y + 50), "2026 · NO. 06", font=right_font, fill=muted)
    # 底部数学符号装饰
    math_font = font("Bodoni", 18)
    math_str = "∮ f(x)dx = Φ(b) − Φ(a)"
    mw = draw.textlength(math_str, font=math_font)
    draw.text((x + 14, y + h - 26), math_str, font=math_font, fill=accent)


# ── 主渲染 v6 ──

def render_card(theme: dict, slug: str) -> None:
    img = Image.new("RGB", (W, H), color=theme["bg"])
    draw = ImageDraw.Draw(img)

    # 1) 背景纹理
    apply_paper_texture(img, density=500, alpha=8)

    # 2) 字体
    me_font = font("STHeiti", 30)
    vol_font = font("Bodoni", 32)
    title_en_font = font("Bodoni", 48)
    body_font = font("STHeiti", 28)
    tag_font = font("STHeiti", 24)
    rule_font = font("STHeiti Medium", 28)

    # 3) 顶部: 品牌 + 卷号 + 金线
    draw.text((80, 80), "M·E · MAJOR EXPLORER", font=me_font, fill=theme["accent"])
    vol_text = "VOL. 2026"
    vol_w = draw.textlength(vol_text, font=vol_font)
    draw.text((W - 80 - vol_w, 85), vol_text, font=vol_font, fill=theme["muted"])
    draw.rectangle([(80, 140), (W - 80, 142)], fill=theme["accent"])

    # 4) 圆形首字印章 + Songti 标题 (智能字号)
    first_char = theme["title"][0]
    stamp_cx, stamp_cy, stamp_r = 145, 245, 75
    draw_stamp_circle(draw, stamp_cx, stamp_cy, stamp_r, first_char, theme["stamp"])

    # 智能字号: 在 150/130/110/95 中找最大 fit
    title_x = 250
    title_y = 175
    max_title_w = W - title_x - 80
    title_size = smart_title_size(draw, theme["title"], max_title_w)
    title_font = font("STHeiti Medium", title_size)
    draw.text((title_x, title_y), theme["title"], font=title_font, fill=theme["text"])
    title_bottom = title_y + int(title_size * 1.1)

    # 英文
    draw.text((title_x, title_bottom + 8), theme["title_en"],
              font=title_en_font, fill=theme["accent"])
    # 学科门类 + 学制 + 学位 (单行 muted)
    meta_top = theme["category"] + " · " + theme["duration"] + " · " + theme["degree"]
    draw.text((title_x, title_bottom + 75), meta_top,
              font=tag_font, fill=theme["muted"])

    # 5) 主题专属装饰 (lede 之上)
    deco_y = title_bottom + 130
    if slug == "medicine":
        # HR 卡片 (右上, deco_y 水平, 不下移)
        draw_hr_card(draw, W - 80 - 260, deco_y, 260, 100,
                     theme["accent"], theme["bg"], theme["text"])
    elif slug == "finance":
        # M 水印 (alpha 混合, 缩小+下移+降低 alpha, 跟标题不抢戏)
        wm_color = (180, 130, 50)
        draw_watermark_ME(img, W, H, wm_color, alpha_val=30,
                          font_size=380, y_offset=100)
    elif slug == "cs":
        # 命令行 prompt (略上移, 离 lede Drop Cap 远一点)
        prompt_y = deco_y - 20
        pf = font("Times", 30)
        draw.text((80, prompt_y), "$ ", font=pf, fill=theme["accent"])
        draw.text((112, prompt_y), "cat /kernel/cs.md", font=pf, fill=theme["text"])
    elif slug == "eng":
        # 工程蓝图角标 (DWG-001 + 简化齿轮)
        draw_eng_blueprint(draw, W - 80 - 240, deco_y - 20, 240, 100,
                           theme["accent"], theme["muted"])
    elif slug == "law":
        # 已立案 2026 大红印 (右上角)
        draw_law_filing_stamp(draw, W - 80 - 90, deco_y + 30, 75,
                              theme["accent"])
    elif slug == "gongan":
        # DOSSIER · 030600 标识
        draw_gongan_dossier(draw, W - 80 - 240, deco_y - 20, 240, 100,
                            theme["accent"], theme["muted"], theme["text"])
    elif slug == "education":
        # 教案 Lesson Plan 卡 (3 个打勾)
        draw_edu_lesson_card(draw, W - 80 - 240, deco_y - 20, 240, 100,
                             theme["accent"], theme["text"], theme["muted"])
    elif slug == "arts":
        # 美术馆 Gallery Wall (3 个空相框)
        draw_arts_gallery(draw, W - 80 - 240, deco_y - 20, 240, 100,
                          theme["accent"], theme["muted"])
    elif slug == "business":
        # 董事会议 Board Minutes 卡
        draw_business_minutes(draw, W - 80 - 240, deco_y - 20, 240, 100,
                              theme["accent"], theme["muted"], theme["text"])
    elif slug == "sci":
        # 期刊 Vol.50 banner
        draw_sci_volume(draw, W - 80 - 240, deco_y - 20, 240, 100,
                        theme["accent"], theme["muted"], theme["text"])

    # 6) lede 带 Drop Cap (只画 1 遍)
    lede_y = deco_y + 105
    used_h = draw_lede_with_dropcap(
        draw, theme["lede"], 80, lede_y, W - 160,
        body_font, theme["text"], max_lines=3,
    )
    lede_bottom = lede_y + used_h

    # 7) 装饰分割线 + 主题符号 + EXHIBIT A 小标
    rule_y = lede_bottom + 25
    rule_text = f"{theme['symbol']}  {theme['rule']}"
    draw.text((80, rule_y), rule_text, font=rule_font, fill=theme["accent"])
    draw.rectangle([(80, rule_y + 42), (W - 80, rule_y + 43)], fill=theme["accent"])

    # EXHIBIT A 期刊小标 (在 3 列 grid 上方)
    exhibit_y = rule_y + 65
    draw_exhibit_label(draw, 80, exhibit_y, theme["exhibit"],
                       theme["accent"], theme["muted"])

    # 8) 3 列课程 grid
    grid_y = exhibit_y + 50
    grid_h = 220
    draw_3col_course_grid(
        draw, 80, grid_y, W - 160, grid_h,
        theme["courses"], theme["directions"], theme["skills"],
        theme["accent"], theme["text"], theme["muted"], theme["bg"],
    )

    # 9) 底部 3 列元数据 grid (学制/难度/学科)
    meta_y = grid_y + grid_h + 30
    meta_h = 130
    draw_meta_grid(
        draw, 80, meta_y, W - 160, meta_h,
        theme["duration"], theme["degree"], theme["difficulty"],
        theme["category"],
        theme["accent"], theme["text"], theme["muted"], theme["bg"],
    )

    # 10) 标签 (实心填充)
    tag_y = meta_y + meta_h + 30
    draw_solid_tags(draw, 80, tag_y, theme["tags"][:5],
                    theme["accent"], theme["bg"])

    # 11) 杂志页脚 (升级: 居中域名衬线 40pt + 公益角章)
    footer_y = H - 110
    draw.rectangle([(80, footer_y), (W - 80, footer_y + 2)], fill=theme["muted"])
    domain_font = font("Times", 40)
    domain = "majorexplorer.com"
    dw = draw.textlength(domain, font=domain_font)
    draw.text(((W - dw) // 2, footer_y + 24), domain, font=domain_font, fill=theme["text"])
    # 公益 tag
    donate_w = 120
    draw.rectangle([(W - 80 - donate_w, footer_y + 18), (W - 80, footer_y + 58)],
                   fill=theme["accent"])
    draw.text((W - 80 - donate_w + 26, footer_y + 28), "公 益",
              font=font("STHeiti Medium", 24), fill=theme["bg"])

    out_path = OUT / f"{slug}.png"
    img.save(out_path, "PNG", optimize=True)
    print(f"✅ {slug:14s} → {out_path.name:30s} ({(out_path.stat().st_size/1024):.0f} KB)")


def main():
    parser = argparse.ArgumentParser(description="OG 卡片 v6 杂志内页渲染")
    parser.add_argument("--only", nargs="+", help="指定渲染的 slug 列表")
    args = parser.parse_args()

    targets = args.only if args.only else list(THEMES.keys())
    for slug in targets:
        if slug not in THEMES:
            print(f"⚠️  未知 slug: {slug}, 跳过")
            continue
        render_card(THEMES[slug], slug)
    print(f"\n✅ Done: {len(targets)} cards in {OUT}")


if __name__ == "__main__":
    main()
