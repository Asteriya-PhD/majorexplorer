# 3 LLM 合成能力对照实验报告

**生成时间**: 2026-06-13 15:31:39
**总测试数**: 10

## 汇总表

| Major | Style | A: m3 only | B: m3+audit | C: m3+antidrift+audit | D: deepseek+mimo |
|---|---|---|---|---|---|
| **保险学** | - | - | - | Q0.90/A10.0✅ |
| **审计学** | - | - | - | Q0.93/A10.0✅ |
| **会计学** | - | - | - | Q0.93/A9.9✅ |
| **金融学** | - | - | - | Q0.93/A10.0✅ |
| **临床医学** | - | - | - | Q0.93/A10.0✅ |
| **法学** | - | - | - | Q0.93/A9.9✅ |
| **计算机科学与技术** | - | - | - | Q0.90/A10.0✅ |
| **农学** | - | - | - | ❌ 质量分 0.17 < 0.7 |
| **应用心理学** | - | - | - | Q0.93/A10.0✅ |
| **建筑学** | - | - | - | ❌ 质量分 0.17 < 0.7 |

## 各组合格率 (audit pass)

- **D**: 8/8 通过, 平均分 9.97

## 成本估算

- 总审计花费: ¥0.0220 (m3 主合成不计)
- 平均每专业审计成本: ¥0.0022

## 详情


### 保险学 [D]
- 合成: deepseek-v4-flash, 审计: mimo-v2-flash
- 轮数: 2, 验证: ✅, 质分: 0.902
- 审计: 10.0/10 ✅, 漂移段: []
- 耗时: 83.71s
- JSON: `test_results/json/insurance_D.json`

### 审计学 [D]
- 合成: deepseek-v4-flash, 审计: mimo-v2-flash
- 轮数: 2, 验证: ✅, 质分: 0.932
- 审计: 10.0/10 ✅, 漂移段: []
- 耗时: 48.36s
- JSON: `test_results/json/auditing_D.json`

### 会计学 [D]
- 合成: deepseek-v4-flash, 审计: mimo-v2-flash
- 轮数: 2, 验证: ✅, 质分: 0.932
- 审计: 9.88/10 ✅, 漂移段: []
- 耗时: 69.32s
- JSON: `test_results/json/accounting_D.json`

### 金融学 [D]
- 合成: deepseek-v4-flash, 审计: mimo-v2-flash
- 轮数: 2, 验证: ✅, 质分: 0.932
- 审计: 10.0/10 ✅, 漂移段: []
- 耗时: 100.98s
- JSON: `test_results/json/finance_D.json`

### 临床医学 [D]
- 合成: deepseek-v4-flash, 审计: mimo-v2-flash
- 轮数: 2, 验证: ✅, 质分: 0.932
- 审计: 10.0/10 ✅, 漂移段: []
- 耗时: 116.41s
- JSON: `test_results/json/clinical-medicine_D.json`

### 法学 [D]
- 合成: deepseek-v4-flash, 审计: mimo-v2-flash
- 轮数: 2, 验证: ✅, 质分: 0.932
- 审计: 9.88/10 ✅, 漂移段: []
- 耗时: 55.56s
- JSON: `test_results/json/law_D.json`

### 计算机科学与技术 [D]
- 合成: deepseek-v4-flash, 审计: mimo-v2-flash
- 轮数: 2, 验证: ✅, 质分: 0.902
- 审计: 10.0/10 ✅, 漂移段: []
- 耗时: 85.24s
- JSON: `test_results/json/computer-science_D.json`

### 农学 [D]
- 合成: deepseek-v4-flash, 审计: (无)
- 轮数: 2, 验证: ❌, 质分: 0.0
- 耗时: 69.93904614448547s
- 错误: 质量分 0.17 < 0.7

### 应用心理学 [D]
- 合成: deepseek-v4-flash, 审计: mimo-v2-flash
- 轮数: 2, 验证: ✅, 质分: 0.932
- 审计: 10.0/10 ✅, 漂移段: []
- 耗时: 76.42s
- JSON: `test_results/json/applied-psychology_D.json`

### 建筑学 [D]
- 合成: deepseek-v4-flash, 审计: (无)
- 轮数: 2, 验证: ❌, 质分: 0.0
- 耗时: 108.54104399681091s
- 错误: 质量分 0.17 < 0.7