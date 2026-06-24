"""批量 audit 22 篇 timeline-augmented medicine majors"""
import subprocess, sys
from pathlib import Path

SLUGS = [
    ("clinical-medicine", "medicine"),
    ("basic-medicine", "medicine"),
    ("anesthesiology", "medicine"),
    ("clinical-pharmacy", "medicine"),
    ("forensic-medicine", "medicine"),
    ("radiation-medicine", "medicine"),
    ("nuclear-medicine", "medicine"),
    ("maternal-child-health-medicine", "medicine"),
    ("preventive-medicine", "medicine"),
    ("medical-imaging", "medicine"),
    ("traditional-chinese-medicine", "medicine"),
    ("integrated-chinese-western-medicine", "medicine"),
    ("stomatology", "medicine"),
    ("pediatrics", "medicine"),
    ("psychiatry", "medicine"),
    ("ophthalmology-optometry", "medicine"),
    ("acupuncture-massage", "medicine"),
    ("tcm-orthopedics", "medicine"),
    ("tcm-yangsheng", "medicine"),
    ("tcm-rehabilitation", "medicine"),
    ("biomedical-science", "medicine"),
    ("uyghur-traditional-medicine", "medicine"),
]

results = []
for slug, style in SLUGS:
    r = subprocess.run(
        ["python3", "scripts/batches/content_audit.py", "--slugs", f"{slug}:{style}"],
        capture_output=True, text=True, timeout=120
    )
    # 从 stdout 提取分数
    score = None
    for line in (r.stdout + r.stderr).split('\n'):
        if "整体" in line or "score" in line.lower():
            # 尝试匹配 X/10
            import re
            m = re.search(r'(\d+(?:\.\d+)?)/10', line)
            if m:
                score = float(m.group(1))
                break
    results.append((slug, score, r.returncode))
    print(f"{slug:50s} score={score} rc={r.returncode}")

# 统计
scored = [s for _, s, _ in results if s is not None]
if scored:
    avg = sum(scored) / len(scored)
    p7 = sum(1 for s in scored if s >= 7)
    p8 = sum(1 for s in scored if s >= 8)
    print(f"\n[STAT] avg={avg:.2f}, ≥7: {p7}/{len(scored)} ({p7*100/len(scored):.0f}%), ≥8: {p8}/{len(scored)} ({p8*100/len(scored):.0f}%)")