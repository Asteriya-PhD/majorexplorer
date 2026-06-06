# 真实数据抓取脚本

## 文件
- `fetch_real_data.py` — 抓 + 校验 + 保存 一分一段表
- `install_cron_6_25.sh` — 安装 6/25 自动跑

## 立刻试一次

```bash
# 抓 2025 物理+历史 一分一段表
/tmp/gkvenv/bin/python scripts/fetch_real_data.py --year 2025 --all

# 抓 2024 单科
/tmp/gkvenv/bin/python scripts/fetch_real_data.py --year 2024 --subject 物理
```

## 安装 6.25 自动跑

```bash
chmod +x scripts/install_cron_6_25.sh
./scripts/install_cron_6_25.sh install    # 安装
./scripts/install_cron_6_25.sh test      # 立刻试一次
./scripts/install_cron_6_25.sh uninstall # 卸载
```

## 数据源优先级

1. **eol.cn 模板** (2024 已验证,2023/2025/2026 模板未知)
2. **本地缓存** `data/_cache/`
3. **公开锚点回填** (精度有限,2025 物理+历史 有 40+ 锚点)
4. **hbea 官方 PDF** (curl 难,需 OCR)
5. **gaokao.com / 555edu 院校级** (URL 不规则,需逐校抓)

## 校验

锚点对比:
- 2024 物理 600分 → 17613 位次
- 2025 物理 600分 → 14274 位次
- 2025 历史 600分 → 3166 位次

偏差 < 2% 才算 pass,否则报错。

## 失败处理

- 失败: 数据保留在 cache,下次再试
- 校验失败: 打印 "⚠️ eol.cn 校验未通过" + 详情,**不覆盖**旧 CSV
- 全部失败: 写 error 报告,不修改数据
