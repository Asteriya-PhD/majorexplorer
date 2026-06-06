"""
cli_demo.py — 命令行演示

输入: 分数/位次 + 选科 + 体检
输出: 96 志愿分类表(冲/稳/保)

用法:
    python cli_demo.py --rank 38000 --subject 物理 --xuanke 物+化+生
    python cli_demo.py --rank 12000 --subject 物理 --xuanke 物+化+ --year 2025 --city 武汉 北京
    python cli_demo.py --rank 38000 --subject 物理 --xuanke 物+化+生 --no-special --max-tuition 30000
"""
import argparse
import json
import sys
from pathlib import Path

# 添加项目根到 path
sys.path.insert(0, str(Path(__file__).parent))

from core.recommender import RecommendRequest, recommend


def print_volunteer_table(response):
    """打印 96 志愿表"""
    s = response.student_summary
    print(f"\n{'='*100}")
    print(f"  考生: 位次 {s['rank']} | {s['subject']}类 | {s['xuanke']} | {s['year']}年")
    print(f"  候选总数(过滤后): {response.candidates_total} 个专业组")
    print(f"  推荐总数: 冲 {response.statistics['chong']} + 稳 {response.statistics['wen']} + 保 {response.statistics['bao']} = {response.statistics['total']}")
    print(f"{'='*100}\n")

    if not response.volunteers:
        print("⚠️  无推荐结果,可能是选科/体检/学费过严,或数据缺失")
        return

    # 表头
    print(f"{'序':>3}  {'档':^4}  {'概率':>5}  {'院校':<30}  {'层次':^4}  {'专业组':<10}  {'选科要求':<10}  {'城市':<6}  {'学费':>6}  {'历年最低位次':<25}  {'建议'}")
    print("-" * 200)

    for v in response.volunteers:
        hist_str = " | ".join(f"{y}:{r}" for y, r in sorted(v.min_rank_historical.items()))
        print(
            f"{v.rank:>3}  {v.category:^4}  {v.est_probability*100:>4.0f}%  "
            f"{v.school_name:<30}  {v.school_type:^4}  {v.group_id:<10}  {v.xuanke_req:<10}  "
            f"{v.city:<6}  {v.tuition_yuan:>5}元  {hist_str:<25}  {v.advice}"
        )

    print()


def main():
    parser = argparse.ArgumentParser(description="湖北高考 96 志愿推荐(原型)")
    parser.add_argument("--rank", type=int, required=True, help="全省位次(1=第一)")
    parser.add_argument("--subject", choices=["物理", "历史"], required=True, help="科类")
    parser.add_argument("--xuanke", required=True, help="选科,如 '物+化+生' 或 '历+政+地'")
    parser.add_argument("--year", type=int, default=2025, help="高考年份")
    parser.add_argument("--city", nargs="+", default=None, help="偏好城市")
    parser.add_argument("--avoid", nargs="+", default=None, help="排除院校")
    parser.add_argument("--no-special", action="store_true", help="排除中外合作/国家专项等")
    parser.add_argument("--max-tuition", type=int, default=None, help="最高学费(元/年)")
    parser.add_argument("--ti-colorblind", choices=["无", "色弱", "色盲"], default="无", help="色觉")
    parser.add_argument("--ti-vision", type=float, default=5.0, help="裸眼视力(默认 5.0)")
    parser.add_argument("--province", default="hubei", help="省份(拼音: hubei/guangdong/...)")
    parser.add_argument("--goal", choices=["考公", "考研", "就业", "考编", "稳定", "兴趣"], default=None, help="学生目标")
    parser.add_argument("--family", choices=["富裕", "普通", "困难"], default=None, help="家庭背景")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    req = RecommendRequest(
        province=args.province,
        rank=args.rank,
        subject=args.subject,
        year=args.year,
        xuanke=args.xuanke,
        ti_eye={"色盲": args.ti_colorblind, "视力": args.ti_vision, "身高_cm": 170},
        city_preference=args.city,
        avoid_schools=args.avoid,
        avoid_special=args.no_special,
        max_tuition=args.max_tuition,
        student_goal=args.goal,
        family_bg=args.family,
    )

    response = recommend(req)

    if args.json:
        print(json.dumps(response.model_dump(), ensure_ascii=False, indent=2))
    else:
        print_volunteer_table(response)


if __name__ == "__main__":
    main()
