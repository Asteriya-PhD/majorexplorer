# Schema Sweep Report — 20260630

扫到: **627** 个 major JSON
自动 fix 篇数: **49**

## 各类怪癖统计

- **credit_string**: 0 篇
- **alumni_school**: 30 篇
  - 示例: `TEMPLATE`, `accounting`, `aviation-service-arts-management`, `business-administration`, `ceramic-art-design`
- **theme_color_string**: 66 篇
  - 示例: `applied-electronic-technology-education`, `applied-meteorology`, `biotechnology`, `civil-hydraulic-marine-engineering`, `civil-law-jurisprudence`
- **salary_overflow**: 91 篇
  - 示例: `ammunition-explosion-engineering`, `animal-pharmacy`, `aquaculture`, `aquatic-animal-medicine`, `armored-vehicle-engineering`
- **summary_lede_dup**: 4 篇
  - 示例: `accounting`, `finance`, `financial-management`, `law`
- **deep_study_sum**: 0 篇
- **missing_lede**: 1 篇
  - 示例: `manifest`
- **missing_discipline**: 2 篇
  - 示例: `TEMPLATE`, `manifest`

## 详细列表 (人工 review 优先)

### alumni_school

- `TEMPLATE`: alumni_quotes[0].school: 学校名 + 专业方向 + 届数 (e.g. 南开大学 精算方 → source
- `accounting`: alumni_quotes[0].school: 校友 (院校脱敏) → source
- `aviation-service-arts-management`: alumni_quotes[0].school: 中国民航大学空中乘务学院 2023 届 @ 北京 → source
- `business-administration`: alumni_quotes[0].school: 校友 (院校脱敏) → source
- `ceramic-art-design`: alumni_quotes[0].school: 景德镇陶瓷大学 2023 届 @ 景德镇 → source
- `chemical-engineering`: alumni_quotes[0].school: 校友 (院校脱敏) → source
- `civil-engineering`: alumni_quotes[0].school: 校友 (院校脱敏) → source
- `computational-finance`: alumni_quotes[0].school: 北京大学 2023 届硕 @ 上海 → source
- `cultural-relics-conservation-restoration`: alumni_quotes[0].school: 西北大学文化遗产学院 → source
- `dance-therapy`: alumni_quotes[0].school: 北京舞蹈学院舞蹈治疗研究中心 2023 届 @ 北京 → source
- `flight-vehicle-control`: alumni_quotes[0].school: 西北工业大学 2020 届 @ 西安 → source
- `forestry`: alumni_quotes[0].school: 校友 (院校脱敏) → source
- `ice-dance-performance`: alumni_quotes[0].school: 北京舞蹈学院冰雪舞蹈表演系 2023 届 @ 北京 → source
- `industrial-design`: alumni_quotes[0].school: 校友 (院校脱敏) → source
- `integrated-circuit-design`: alumni_quotes[0].school: 校友 (院校脱敏) → source
- `intelligent-transportation`: alumni_quotes[0].school: 北京交通大学 → source
- `international-economic-cooperation`: alumni_quotes[0].school: 对外经济贸易大学 2020 届 @ 北京 → source
- `international-economics-trade`: alumni_quotes[0].school: 校友 (院校脱敏) → source
- `jewelry-design`: alumni_quotes[0].school: 中国地质大学 (武汉) 2023 届 @ 深圳 → source
- `journalism-communication`: alumni_quotes[0].school: 中国传媒大学 新闻学院 → source
- `landscape-architecture`: alumni_quotes[0].school: 校友 (院校脱敏) → source
- `materials-science-engineering`: alumni_quotes[0].school: 校友 (院校脱敏) → source
- `mechanical-engineering`: alumni_quotes[0].school: 校友 (院校脱敏) → source
- `microelectronics`: alumni_quotes[0].school: 校友 (院校脱敏) → source
- `music-therapy`: alumni_quotes[0].school: 中央音乐学院音乐治疗研究中心 2023 届 @ 北京 → source
- `popular-dance`: alumni_quotes[0].school: 上海戏剧学院舞蹈学院流行舞 2023 届 @ 上海 → source
- `postal-engineering`: alumni_quotes[0].school: 南京邮电大学 → source
- `public-affairs-management`: alumni_quotes[0].school: 中部省份 211 公共事业管理 2023 届 → source
- `smart-construction-transportation`: alumni_quotes[0].school: 东南大学 2022 届 @ 南京 → source
- `vehicle-engineering`: alumni_quotes[0].school: 校友 (院校脱敏) → source

### theme_color_string

- `applied-electronic-technology-education`: theme_color: str "#5C8A4A" → object (人工 review)
- `applied-meteorology`: theme_color: str "#2E5A7A" → object (人工 review)
- `biotechnology`: theme_color: str "#1E5E72" → object (人工 review)
- `civil-hydraulic-marine-engineering`: theme_color: str "#4A6B8A" → object (人工 review)
- `civil-law-jurisprudence`: theme_color: str "#3A3A3A" → object (人工 review)
- `civil-procedure`: theme_color: str "#3A3A3A" → object (人工 review)
- `coast-guard-vessel-command`: theme_color: str "#0D47A1" → object (人工 review)
- `counterterrorism-policing`: theme_color: str "#1A237E" → object (人工 review)
- `criminal-procedure`: theme_color: str "#3A3A3A" → object (人工 review)
- `criminology`: theme_color: str "#1F4E79" → object (人工 review)
- `dari`: theme_color: str "#dc2626" → object (人工 review)
- `digital-trade`: theme_color: str "#0ea5e9" → object (人工 review)
- `dutch`: theme_color: str "#1F4E79" → object (人工 review)
- `educational-technology`: theme_color: str "#5C7C4A" → object (人工 review)
- `environmental-ecological-engineering`: theme_color: str "sci-eng" → object (人工 review)
- `exercise-public-health`: theme_color: str "#14b8a6" → object (人工 review)
- `exhibition-economy-management`: theme_color: str "#9333EA" → object (人工 review)
- `facility-agriculture-science-engineering`: theme_color: str "#6B7A3F" → object (人工 review)
- `feed-engineering`: theme_color: str "#84cc16" → object (人工 review)
- `finance-math`: theme_color: str "#5A4632" → object (人工 review)
- `financial-engineering`: theme_color: str "#5A4632" → object (人工 review)
- `fine-chemicals`: theme_color: str "#A0522D" → object (人工 review)
- `foreign-police`: theme_color: str "#1B4F72" → object (人工 review)
- `geochemistry`: theme_color: str "#7A4E2E" → object (人工 review)
- `geodesy-and-survey-engineering`: theme_color: str "#5B5B47" → object (人工 review)
- `geographic-information-science`: theme_color: str "#0E7490" → object (人工 review)
- `hotel-management`: theme_color: str "#7C2D12" → object (人工 review)
- `humanities-education`: theme_color: str "#5C7C4A" → object (人工 review)
- `industrial-engineering`: theme_color: str "#0F4C81" → object (人工 review)
- `insurance`: theme_color: str "#5A4632" → object (人工 review)
- `integrated-science`: theme_color: str "#4A2E7A" → object (人工 review)
- `intelligent-engineering-creative-design`: theme_color: str "#5B5B47" → object (人工 review)
- `intelligent-molecular-engineering`: theme_color: str "#0d9488" → object (人工 review)
- `international-law`: theme_color: str "#3A3A3A" → object (人工 review)
- `land-remediation-engineering`: theme_color: str "#84cc16" → object (人工 review)
- `maritime-police-logistics`: theme_color: str "#0ea5e9" → object (人工 review)
- `marketing`: theme_color: str "#4A4564" → object (人工 review)
- `marketing-education`: theme_color: str "#a855f7" → object (人工 review)
- `materials-chemistry`: theme_color: str "#f59e0b" → object (人工 review)
- `medical-laboratory-technology`: theme_color: str "#0891b2" → object (人工 review)
- `metallurgical-engineering`: theme_color: str "#a16207" → object (人工 review)
- `musical-instrument-manufacturing`: theme_color: str "#8B5A8C" → object (人工 review)
- `nuclear-medical-engineering`: theme_color: str "#be185d" → object (人工 review)
- `overseas-interests-security`: theme_color: str "#1e3a8a" → object (人工 review)
- `physical-education`: theme_color: str "#5C7C4A" → object (人工 review)
- `physical-geography-urban-rural-planning`: theme_color: str "#0E7490" → object (人工 review)
- `precision-instruments`: theme_color: str "#2563eb" → object (人工 review)
- `preschool-education`: theme_color: str "#5C7C4A" → object (人工 review)
- `prison-studies`: theme_color: str "#2C3E50" → object (人工 review)
- `property-management`: theme_color: str "#1F4E3D" → object (人工 review)
- `psychology-brain-cognitive-science`: theme_color: str "#6A4C93" → object (人工 review)
- `public-finance`: theme_color: str "#5A4632" → object (人工 review)
- `public-security-demo`: theme_color: str "#1A2B4A" → object (人工 review)
- `quality-management-engineering`: theme_color: str "#0E7490" → object (人工 review)
- `romanian`: theme_color: str "#7c3aed" → object (人工 review)
- `sci-tech-art`: theme_color: str "#ec4899" → object (人工 review)
- `sericulture`: theme_color: str "#7B9E3D" → object (人工 review)
- `soft-matter-science-engineering`: theme_color: str "#7c3aed" → object (人工 review)
- `special-education`: theme_color: str "#5C7C4A" → object (人工 review)
- `statistics`: theme_color: str "#1E5E72" → object (人工 review)
- `tcm-orthopedics`: theme_color: str "#dc2626" → object (人工 review)
- `tcm-rehabilitation`: theme_color: str "#1F6B5C" → object (人工 review)
- `theatre-education`: theme_color: str "#8B4513" → object (人工 review)
- `traditional-chinese-pharmacy`: theme_color: str "#7B3F00" → object (人工 review)
- `transportation-equipment-control-engineering`: theme_color: str "#2E5C8A" → object (人工 review)
- `uyghur-traditional-medicine`: theme_color: str "#8B3A3A" → object (人工 review)

### salary_overflow

- `ammunition-explosion-engineering`: salary P25 倒挂: 5年=28 > 10年+=20 (人工 review)
- `animal-pharmacy`: salary P25 倒挂: 5年=15.0 > 10年+=10 (人工 review)
- `aquaculture`: salary P25 倒挂: 5年=15.0 > 10年+=10 (人工 review)
- `aquatic-animal-medicine`: salary P25 倒挂: 5年=15.0 > 10年+=10 (人工 review)
- `armored-vehicle-engineering`: salary P25 倒挂: 5年=28 > 10年+=20 (人工 review)
- `artificial-intelligence-cross`: salary P25 倒挂: 5年=60 > 10年+=45 (人工 review)
- `asset-appraisal`: salary P25 倒挂: 5年=50 > 10年+=45 (人工 review)
- `automotive-maintenance-engineering-education`: salary P25 倒挂: 5年=25 > 10年+=20 (人工 review)
- `bio-breeding-science`: salary P25 倒挂: 5年=15 > 10年+=10 (人工 review)
- `bio-breeding-technology`: salary P25 倒挂: 5年=15 > 10年+=10 (人工 review)
- `biomass-science-engineering`: salary P25 倒挂: 5年=15 > 10年+=10 (人工 review)
- `brain-computer-science`: salary P25 倒挂: 5年=50 > 10年+=45 (人工 review)
- `brewing-engineering`: salary P25 倒挂: 5年=25 > 10年+=20 (人工 review)
- `building-electricity-intelligence`: salary P25 倒挂: 5年=25 > 10年+=20 (人工 review)
- `chemical-engineering-industrial-bioengineering`: salary P25 倒挂: 5年=28 > 10年+=20 (人工 review)
- `chemical-measurement-technology`: salary P25 倒挂: 5年=28 > 10年+=20 (人工 review)
- `chemical-safety-engineering`: salary P25 倒挂: 5年=25 > 10年+=20 (人工 review)
- `chinese-classical-studies`: salary P25 倒挂: 5年=22 > 10年+=15 (人工 review)
- `commercial-law`: salary P25 倒挂: 5年=63 > 10年+=45 (人工 review)
- `computational-finance`: salary P25 倒挂: 5年=63 > 10年+=45 (人工 review)
- `cosmetics-technology-engineering`: salary P25 倒挂: 5年=28 > 10年+=20 (人工 review)
- `cryptography-science-technology`: salary P25 倒挂: 5年=50 > 10年+=45 (人工 review)
- `cyber-space-security-studies`: salary P25 倒挂: 5年=22 > 10年+=15 (人工 review)
- `digital-humanities`: salary P25 倒挂: 5年=22 > 10年+=15 (人工 review)
- `economics`: salary P25 倒挂: 5年=26 > 10年+=20 (人工 review)
- `economics-finance`: salary P25 倒挂: 5年=25 > 10年+=20 (人工 review)
- `educational-technology`: salary P25 倒挂: 5年=22 > 10年+=15 (人工 review)
- `emergency-equipment-technology-and-engineering`: salary P25 倒挂: 5年=28 > 10年+=20 (人工 review)
- `energy-chemical-engineering`: salary P25 倒挂: 5年=30 > 10年+=20 (人工 review)
- `energy-chemistry`: salary P25 倒挂: 5年=50 > 10年+=45 (人工 review)
- `environmental-science`: salary P25 倒挂: 5年=25 > 10年+=20 (人工 review)
- `feed-engineering`: salary P25 倒挂: 5年=16 > 10年+=10 (人工 review)
- `finance`: salary P25 倒挂: 5年=26 > 10年+=20 (人工 review)
- `finance-math`: salary P25 倒挂: 5年=60 > 10年+=45 (人工 review)
- `financial-engineering`: salary P25 倒挂: 5年=63 > 10年+=45 (人工 review)
- `fintech`: salary P25 倒挂: 5年=25 > 10年+=20 (人工 review)
- `flight-technology`: salary P25 倒挂: 5年=63 > 10年+=45 (人工 review)
- `flight-vehicle-control`: salary P25 倒挂: 5年=28 > 10年+=20 (人工 review)
- `foreign-languages-history`: salary P25 倒挂: 5年=20 > 10年+=15 (人工 review)
- `foreign-police`: salary P25 倒挂: 5年=22 > 10年+=15 (人工 review)
- `forestry`: salary P25 倒挂: 5年=15 > 10年+=10 (人工 review)
- `geography`: salary P25 倒挂: 5年=25 > 10年+=20 (人工 review)
- `geology`: salary P25 倒挂: 5年=25 > 10年+=20 (人工 review)
- `hydrology-water-resources-engineering`: salary P25 倒挂: 5年=25 > 10年+=20 (人工 review)
- `industrial-design`: salary P25 倒挂: 5年=25.0 > 10年+=20 (人工 review)
- `insurance`: salary P25 倒挂: 5年=26 > 10年+=20 (人工 review)
- `integrated-chinese-western-medicine`: salary P25 倒挂: 5年=20 > 10年+=15 (人工 review)
- `integrated-circuit-design-and-integration-system`: salary P25 倒挂: 5年=50 > 10年+=45 (人工 review)
- `international-business`: salary P25 倒挂: 5年=25 > 10年+=20 (人工 review)
- `international-economic-cooperation`: salary P25 倒挂: 5年=28 > 10年+=20 (人工 review)
- `investment-studies`: salary P25 倒挂: 5年=50 > 10年+=45 (人工 review)
- `japanese`: salary P25 倒挂: 5年=20 > 10年+=15 (人工 review)
- `joint-operations`: salary P25 倒挂: 5年=20 > 10年+=15 (人工 review)
- `landscape-architecture`: salary P25 倒挂: 5年=15 > 10年+=10 (人工 review)
- `landscape-architecture2`: salary P25 倒挂: 5年=18 > 10年+=10 (人工 review)
- `logistics-management`: salary P25 倒挂: 5年=25 > 10年+=20 (人工 review)
- `low-altitude-economy`: salary P25 倒挂: 5年=45 > 10年+=20 (人工 review)
- `marine-information-engineering`: salary P25 倒挂: 5年=28 > 10年+=20 (人工 review)
- `mechanical-process-technology`: salary P25 倒挂: 5年=28 > 10年+=20 (人工 review)
- `medical-laboratory-technology`: salary P25 倒挂: 5年=20 > 10年+=15 (人工 review)
- `metallic-materials-engineering`: salary P25 倒挂: 5年=25 > 10年+=20 (人工 review)
- `microelectronics`: salary P25 倒挂: 5年=25.0 > 10年+=20 (人工 review)
- `military-history-thought`: salary P25 倒挂: 5年=20 > 10年+=15 (人工 review)
- `military-logistics`: salary P25 倒挂: 5年=20 > 10年+=15 (人工 review)
- `military-organization`: salary P25 倒挂: 5年=20 > 10年+=15 (人工 review)
- `motor-appliance-intelligence`: salary P25 倒挂: 5年=25 > 10年+=20 (人工 review)
- `naval-architecture-and-ocean-engineering`: salary P25 倒挂: 5年=28 > 10年+=20 (人工 review)
- `network-engineering`: salary P25 倒挂: 5年=30 > 10年+=25 (人工 review)
- `ocean-science`: salary P25 倒挂: 5年=25 > 10年+=20 (人工 review)
- `pedagogy`: salary P25 倒挂: 5年=20 > 10年+=15 (人工 review)
- `pesticide-fertilizer`: salary P25 倒挂: 5年=15.0 > 10年+=10 (人工 review)
- `precision-instruments`: salary P25 倒挂: 5年=28 > 10年+=20 (人工 review)
- `prison-studies`: salary P25 倒挂: 5年=20 > 10年+=15 (人工 review)
- `process-equipment-control-engineering`: salary P25 倒挂: 5年=25 > 10年+=20 (人工 review)
- `public-security-demo`: salary P25 倒挂: 5年=22 > 10年+=15 (人工 review)
- `quantum-information-science`: salary P25 倒挂: 5年=60 > 10年+=45 (人工 review)
- `resource-recycling-engineering`: salary P25 倒挂: 5年=25 > 10年+=20 (人工 review)
- `romanian`: salary P25 倒挂: 5年=20 > 10年+=15 (人工 review)
- `smart-animal-husbandry`: salary P25 倒挂: 5年=18.0 > 10年+=10 (人工 review)
- `smart-construction-transportation`: salary P25 倒挂: 5年=60 > 10年+=45 (人工 review)
- `spatial-information-digital-technology`: salary P25 倒挂: 5年=35 > 10年+=25 (人工 review)
- `systems-science-engineering`: salary P25 倒挂: 5年=60 > 10年+=45 (人工 review)
- `teaching-chinese-foreign-language`: salary P25 倒挂: 5年=20.0 > 10年+=15 (人工 review)
- `tobacco`: salary P25 倒挂: 5年=15.0 > 10年+=10 (人工 review)
- `traditional-chinese-medicine`: salary P25 倒挂: 5年=20 > 10年+=15 (人工 review)
- `traffic-engineering`: salary P25 倒挂: 5年=28 > 10年+=20 (人工 review)
- `traffic-transportation`: salary P25 倒挂: 5年=28 > 10年+=20 (人工 review)
- `transportation-construction-equipment`: salary P25 倒挂: 5年=28 > 10年+=20 (人工 review)
- `viticulture-enology`: salary P25 倒挂: 5年=25 > 10年+=20 (人工 review)
- `weapon-launch-engineering`: salary P25 倒挂: 5年=28 > 10年+=20 (人工 review)
- `welding-technology-engineering`: salary P25 倒挂: 5年=25 > 10年+=20 (人工 review)

### summary_lede_dup

- `accounting`: summary == lede (完全重复, 人工 review)
- `finance`: summary == lede (完全重复, 人工 review)
- `financial-management`: summary == lede (完全重复, 人工 review)
- `law`: summary == lede (完全重复, 人工 review)

### missing_lede

- `manifest`: 缺 lede 字段 (人工 review)

### missing_discipline

- `TEMPLATE`: 缺 discipline 字段 (Day 49 manifest 必备)
- `manifest`: 缺 discipline 字段 (Day 49 manifest 必备)
