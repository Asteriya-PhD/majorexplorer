#!/usr/bin/env python3
"""
TTS 文本预处理 — mmx speech synthesize 前必跑

依据: [[mmx-tts-pronunciation-pitfalls-2026-06-28]]
"""
import re
import sys
from pathlib import Path


def preprocess(text: str) -> str:
    """把机器友好的中文转 TTS 友好的中文."""

    # 1. 年份 (4 位) → 拆位读 (限"年"上下文, 不误伤 2026-06 之类)
    text = re.sub(
        r'\b(20[0-9]{2})\s*年',
        lambda m: f"{''.join(_num_to_char(d) for d in m.group(1))}年",
        text,
    )

    # 2. 月份 (X月) → 汉字
    text = re.sub(
        r'\b(\d+)\s*月\b',
        lambda m: f"{_num_to_words(m.group(1))}月",
        text,
    )

    # 2. 百分比 → 百分之X
    text = re.sub(r'(\d+)%', lambda m: f"百分之{_num_to_words(m.group(1))}", text)

    # 3. 英文型号 X.Y.Z → 字母 + 点 + 数字
    # glm4.8 → glm 四点八
    # Claude 4.5 → Claude 四点五
    text = re.sub(
        r'\b([A-Za-z][A-Za-z0-9]*?)(\d+)\.(\d+)\b',
        lambda m: f"{m.group(1)} {_decimal_to_words(m.group(2), m.group(3))}",
        text,
    )
    # 单点版本: X.Y 没连字母 (少见但兼容)
    text = re.sub(
        r'\b(\d+)\.(\d+)\b',
        lambda m: _decimal_to_words(m.group(1), m.group(2)),
        text,
    )

    # 4. URL → 拆点拆斜杠
    # majorexplorer.com → major explorer 点 com
    text = re.sub(
        r'\b([a-z]+)\.([a-z]{2,})\b',
        lambda m: f"{m.group(1)} 点 {m.group(2)}",
        text,
        flags=re.IGNORECASE,
    )

    # 5. 通用数字 + 单位 (怕误伤短语只处理明显单位)
    # 数字 + (可选多) + 单位; 单位后跟任意中文字符或结束 (避免 "4 天志" 被拒)
    text = re.sub(
        r'(\d+)\s*(多)?\s*(分|个|省|位|人|所|家|次|条|篇|块|元|天|小时|分钟|门|种|类|校|岁|米|公里|斤|公斤|度|层|楼|室|床)(?=[一-鿿　。，、；！？,;!?\.“”《》（）()\[\]【】]|$)',
        lambda m: (
            f"{_num_to_words(m.group(1))}多{m.group(3)}" if m.group(2)
            else f"{_num_to_words(m.group(1))}{m.group(3)}"
        ),
        text,
    )
    # "X 个" (更宽泛单位: 门类/专业/专业类/词/字/段/句)
    text = re.sub(
        r'(\d+)\s*(门类|专业|专业类|词|字|段|句)',
        lambda m: f"{_num_to_words(m.group(1))}{m.group(2)}",
        text,
    )

    # 6. 句末 . → 。 (避免英文句号让 TTS 收得太短)
    text = text.replace('. ', '。').replace('.\n', '。\n')

    # 7. 多余空白
    text = re.sub(r'  +', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def _num_to_char(d: str) -> str:
    """单个数字 → 中文数字. '2026' → '二零二六'."""
    return {'0': '零', '1': '一', '2': '二', '3': '三', '4': '四',
            '5': '五', '6': '六', '7': '七', '8': '八', '9': '九'}.get(d, d)


def _num_to_words(n: str) -> str:
    """数字串 → 中文读法. '580' → '五百八十', '95' → '九十五', '27' → '二十七'."""
    chars = "零一二三四五六七八九"
    digits = [int(d) for d in n]
    if len(digits) == 1:
        return chars[digits[0]]
    if len(digits) == 2:
        if digits[0] == 1:
            return "十" + (chars[digits[1]] if digits[1] != 0 else "")
        return chars[digits[0]] + "十" + (chars[digits[1]] if digits[1] != 0 else "")
    if len(digits) == 3:
        # 580 → 五百八十
        result = chars[digits[0]] + "百"
        if digits[1] == 0 and digits[2] != 0:
            result += "零" + chars[digits[2]]
        elif digits[1] != 0:
            result += _num_to_words(str(digits[1] * 10 + digits[2]))
        return result
    if len(digits) == 4:
        # 2026 → 二千零二十六
        result = chars[digits[0]] + "千"
        rest = digits[1:]
        if rest[0] == 0 and any(d != 0 for d in rest[1:]):
            result += "零"
            result += _num_to_words("".join(str(d) for d in rest[1:]))
        elif rest[0] != 0:
            result += _num_to_words("".join(str(d) for d in rest))
        return result
    return n  # 5+ 位不处理, 避免误伤


def _decimal_to_words(int_part: str, dec_part: str) -> str:
    """小数 → '四点八'. '4.8' → '四点八'."""
    return f"{_num_to_words(int_part)}点{_num_to_words(dec_part)}"


# === CLI ===
if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 文件模式: input.txt → input.tts.txt
        inp = Path(sys.argv[1])
        text = inp.read_text(encoding="utf-8")
        out = inp.with_suffix(".tts.txt")
        out.write_text(preprocess(text), encoding="utf-8")
        print(f"✅ {inp} → {out}")
        print("--- preview (前 10 行) ---")
        print("\n".join(out.read_text(encoding="utf-8").splitlines()[:10]))
    else:
        # demo 模式: 跑几个真实例子
        samples = [
            "孩子考了 580 分,我刷了 4 天志愿 App.",
            "600 多个专业, 20 天做完.",
            "国家电网 25%, 南方电网 12%.",
            "Claude 4.5 模型效果很好.",
            "glm4.8 比上一代强.",
            "majorexplorer.com 是网址.",
            "13 个门类, 92 个专业类, 868 个专业.",
            "刘哲文 · 2026 年 6 月 · 湖北",
        ]
        print(f"{'原句':<45} → TTS 友好")
        print("-" * 80)
        for s in samples:
            print(f"{s:<45} → {preprocess(s)}")