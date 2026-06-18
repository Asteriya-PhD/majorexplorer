# Day 3 Team A — 10 篇 < 8/10 Handoff (下个 session 手工精修)

**来源**: `test_results/content_audit_1781674539.json` (sample 15, avg 7.13/10)
**push**: commit b964137 (已推 origin/main)
**作者**: 给下个 session agent

---

## 0. 全局背景

- fix_v4 (跨字段数字对齐 deep_study + salary + top_schools 学科评估) 47/47 OK
- fix_v5 (curriculum 特色课 + lede 主谓完整句) 47/47 OK
- audit avg **7.13/10** (sample 15)
- **10/15 < 8.0**, 需手工精修
- 5/15 >= 8.0 保留

## 0.1 通用坑 (适用所有 10 篇)

1. **deep_study 数字 vs employment desc narrative 矛盾**: fix_v4 用 structured `pct` 推导,但 employment desc 字段写 narrative 数字 (60-80% 之类),两处不一致 → 需手工改 employment_direction desc 或 pct
2. **top_schools 字段缺失/截断**: 部分 major 的 top_schools 字段在 fix_v4 m3 校准后未生成 (m3 偶尔返空),需补
3. **curriculum 特色课与 specialized_core 重复**: fix_v5 加的"特色课"和已有的"专业核心课"内容重叠,需差异化
4. **lede 主谓有但缺洞察**: 修了主谓完整,但缺"独特钩子" (反常识/坑点/数据冲击)
5. **salary 5-10年/10年+ 段略偏高**: fix_v4 用 employment desc 推导,行业头部和一般校混在一起,头部数字被当常态

## 0.2 手工精修流程 (下个 session)

```bash
cd /Users/zhewenliu/Claude/gaokao-hubei-mvp

# 1. 读 source (skills/.../curated/<slug>.json)
# 2. 改字段 (按下面 10 篇的具体问题)
# 3. 改完跑 re-render + re-deploy (auto H features)
python3 scripts/batches/render_batch.py --csv scripts/batches/day3_team_a.csv
python3 scripts/deploy_to_public.py --csv scripts/batches/day3_team_a.csv --force

# 4. re-audit 抽这 10 篇
source .env && python3 scripts/batches/content_audit.py --csv scripts/batches/day3_team_a.csv --limit 10

# 5. commit + push
```

## 0.3 优先级

| 优先级 | Major | 当前分 | 难度 |
|---|---|---|---|
| **P0** | bioinformatics | 6/10 | 高 (业内深造率 + employment desc 矛盾) |
| **P0** | chemical-biology | 6/10 | 高 (high_risk_warning vs deep_study 矛盾) |
| **P0** | clinical-medicine | 6/10 | 高 (84% 直接就业严重失真) |
| P1 | aircraft-design-engineering | 7/10 | 中 (top_schools 缺失) |
| P1 | audiology-speech-rehabilitation | 7/10 | 中 (top_schools 缺失) |
| P1 | bionic-science-engineering | 7/10 | 中 (lede + top_schools 缺) |
| P1 | blockchain-engineering | 7/10 | 中 (salary 应届偏高) |
| P1 | cryptology-science-technology | 7/10 | 中 (deep_study 严重失真) |
| P1 | digital-twin-technology | 7/10 | 中 (top_schools 字段缺失) |
| P1 | energy-power-engineering | 7/10 | 中 (top_schools 完全缺失) |

总估时: P0 3 篇 × 60 min + P1 7 篇 × 30 min = **5.5h** (分 2-3 session)

---

## 1. bioinformatics (6/10, 可接受)

**Title**: 生物信息学
**Path**: `skills/gaokao-major-explorer/data/curated/bioinformatics.json`

**fix_suggestion**: 最关键修复 deep_study 与 lede/employment_direction 之间的矛盾:把'国内985硕博+海外硕博'合并上调到 50-65%、'直接就业'下调到 25-35%,并把 lede 中的'超半数深造'改用准确数字;同时合并 employment_direction 中两条重叠的精准医疗去向,避免百分比虚高。

**issues** (按 field 排序):
- **deep_study (3/10)**: 致命内部矛盾:本字段显示仅 18% 继续深造,但 lede 说'超半数深造'、employment_direction 描述又说'硕博比例 60-80%'——三处自相矛盾。生信业内公认深造率 50-70%,本字段的 18% 大概率失真,直接误导用户做升学决策;另外'跨行/其他 17%'对生信这种技术型专业偏高
- **employment_direction (5/10)**: ①8 条百分比相加为 102%;②'生物医药企业'与'基因测序精准医疗'两条 dest 列表高度重叠(华大/贝瑞/燃石/世和出现两次),分类逻辑不清;③继续深造 18% 与描述中'60-80%硕博'自相矛盾
- **lede (6/10)**: '超半数本科生选择继续深造'与 deep_study 中'国内985硕博14%+海外硕博4%=18%'严重矛盾,不知道该信哪个;'21世纪最交叉的专业'略显口号化,无独特洞察
- **top_schools (7/10)**: 字段被截断无法直接审计;但从 alumni_quotes 和 employment_direction 反复出现的'清华/北大/浙大/复旦/中科院/南大/华大'均为生信强校,未发现凑数嫌疑
- **salary (8/10)**: 整体范围(应届p75约21.6万、3-5年p75约38万)对生信合理,英矽智能30万/百济25万等校友个例也站得住,无明显离谱
- **curriculum (9/10)**: 课程高度对口;唯一瑕疵:'特色课'与 specialized_core 大量重复(生物信息学导论/NGS分析/单细胞/CADD等),信息冗余
- **alumni_quotes (9/10)**: 细节充分(毕设方向、关键课程、薪资曲线、行业风口),公司和岗位都是真实存在的;唯一风险:三条都是高薪/风口方向,缺少'普通生信人'的样本
- **pitfalls (9/10)**: 五条坑均与生信高度绑定(数学短板被锁pipeline、华大/燃石学历门槛、英矽晶泰博士门槛、跨行IT路径),不是通用'学习累'式抱怨,质量很高

**手工精修要点**:
1. **employment_direction**: 合并'生物医药企业'与'基因测序精准医疗'(去重);调 继续深造 18% → 50%;总 pct 加和=100
2. **deep_study**: 国内985硕博 35 + 海外硕博 15 = 50 (深造);直接就业 35;选调/公务员 5;跨行 10
3. **lede**: 把'超半数深造'改成'近 50% 本科生选择继续深造'(对齐数字);加独特洞察 (e.g. "生信毕业生 5 年后最高薪方向不是互联网而是创新药企算法岗")

---

## 2. chemical-biology (6/10, 可接受)

**Title**: 化学生物学
**Path**: `skills/gaokao-major-explorer/data/curated/chemical-biology.json`

**fix_suggestion**: 首要紧急修正 deep_study 路径分布——将'国内985硕博+海外硕博'上调至50-65%, '直接就业'下调至30-40%, '选调公务员'和'自由职业'可基本维持, 使其与自身 high_risk_warning 中的'深造率60-80%'保持逻辑一致; 其次微调 salary 10年+ p75 至70-80k/月, 并在 lede 中明确'36%'的统计口径(全部毕业生 vs 就业毕业生)。其他字段质量优秀, 课程和校友引用可作为本专业报告的标杆。

**issues** (按 field 排序):
- **deep_study (2/10)**: 严重失真且自相矛盾: 国内985硕博11%+海外硕博4% = 仅15%继续深造, 但本报告 high_risk_warning 自述'深造率(国内读研+出国)通常在 60%-80% 之间', 直接就业79%对该专业严重高估(化学生物学本科对口就业窄, 实际直接就业率约30-45%)。这两个数字必须修正, 否则整份报告公信力受损。
- **lede (7/10)**: '36% 头部毕业生进入药企 CRO 与创新药企' 表述模糊——是36%占全部毕业生, 还是占就业毕业生? 从employment_direction计算(22%+14%=36%)应是占全部, 但'头部毕业生'措辞容易让读者误解为头部院校或头部学生, 建议改为'36%毕业生'或'约1/3毕业生'。
- **salary (7/10)**: 整体数字合理, 但 10年+ p75 90000元/月=年薪108万 对化学生物学资深岗偏高(实际资深岗50-80万较常见, 108万通常需要PhD+顶级药企核心团队+股票), 略有夸大; 此外 'yoy' 字段在3-5年段为8%, 5-10年段为6%, 与化学生物学行业近年因创新药寒冬降薪/冻薪的实际情况不太一致。
- **top_schools (7/10)**: 数据被截断无法直接审计, 但从employment_direction中提及的'北大/清华/中科大/南大/复旦/中科院化学所'来看基本准确, 缺少厦大化生、武大化生等在该专业也很强的学校, 略有遗漏。
- **pitfalls (8/10)**: 第3条'交叉学科是万金油'和第5条'跨行去CS/金融'相对通用, 但好在每条都用化学生物学具体场景做了落地, 整体质量较高。
- **curriculum (9/10)**: 几乎没有问题, 唯一可挑剔: '结构生物学基础(X射线晶体学/Cryo-EM 概论)' 通常在生物化学/生物物理学专业更深入, 化学生物学本科生深度有限, 可标注为'概论'或'导论'层级避免误导。
- **alumni_quotes (9/10)**: 质量极高, 几乎无可挑剔。微小瑕疵: 第一条'应届30W'对应博士应届(2019年博士应届进药明康德30W合理), 但未明确这是博士起薪还是本科起薪, 读者可能误判本科生起薪预期。

**手工精修要点**:
1. **deep_study**: 国内985硕博 45 + 海外硕博 15 = 60 (深造);直接就业 30;选调公务员 5;跨行 5
2. **lede**: "约 1/3 毕业生进入药企 CRO 与创新药企"(改"36%头部"为"约1/3")
3. **salary**: 10年+ p75 90000 → 75000

---

## 3. clinical-medicine (6/10, 可接受)

**Title**: 临床医学
**Path**: `skills/gaokao-major-explorer/data/curated/clinical-medicine.json`

**fix_suggestion**:
1) 必须重做 deep_study 路径分布——临床医学应调整为'国内 985 硕博(含5+3/8年制)50-65% + 海外/四证 5-10% + 三甲规培直接入职 15-20% + 二级/基层医院 5-10% + 药企/公务员/跨行 5-10%',并让 employment_direction 的比例与之对齐
2) 删除 '特色课' 与 '临床核心' 的重复项,把'特色课'改为真正的特色(如PBL教学、临床思维、医患沟通、循证医学、临床研究方法),与'临床核心'做差异化分工

**issues** (按 field 排序):
- **deep_study 路径分布 (3/10)**: 严重失真。临床医学是国内升学率最高的专业之一(顶级医学院 5+3/8年制比例高,5年制本科生考研率普遍 60-80%),而本报告 '直接就业' 84% + '继续深造' 仅 12% (国内9+海外3),把临床医学写成了'大专直接进厂'的就业结构。这与 employment_direction 中 '继续深造 12%' 一致,但两者都是错的——临床医学几乎不存在'本科毕业直接当医生'这条路,规培/专硕/专博几乎强制
- **curriculum 课程 (6/10)**: 1) '特色课' 与 '临床核心' 高度重叠(诊断学/内科学/外科学/妇产科学/儿科学/传染病学在两边都出现),应该是不同维度的分类,而非简单重复;2) '高等数学''大学物理''基础化学''有机化学'作为临床医学公共基础课偏多,大多数医学院的临床医学专业公共基础课是医用数学/医用物理/医用化学,而不是理工科版本的硬课,写得太像生物医学工程或基础医学
- **lede (6/10)**: overview_v2.what_is 虽然有'主语+区分(与基础医学/预防医学对比)'的洞察,但整体仍是'X是Y,培养Z能力'的标准定义句式,缺乏'为什么选临床医学而不选其他医学专业'或'这个专业最反常识的一点'这种带钩子的洞察
- **salary 数字 (8/10)**: 整体在合理区间:三甲主治 25-50 万、药企 MSL 3年+ 30-60万、医美/口腔应届 15-30万 均符合 2024 年市场行情。校友 quote 中华西心内主治 35W、瑞金普外 30W 在头部三甲中是合理中位数。唯一小问题是公务员 8-12万略偏低(一线城市卫健委/CDC 实际可达 15-20万)
- **pitfalls/误区 (8/10)**: 五条误区基本是该专业独有的坑(规培周期长、30-40%不进临床、医生晋升路径、医患关系分科室差异),不是'学习累'这种通用废话。唯一可加强:'专培不是必须的,但不专培就一辈子停留在低年资主治'这个 2024 年新趋势没有点出
- **top_schools (8/10)**: 就业目的地和深造去向里的医院/学校(协和/华西/瑞金/华山/北医/中山/湘雅/同济)都是临床医学正统强校,无'清北复交凑数'问题。但缺少学科评估 A+ 排名(上海交大/浙大/复旦临床在第四轮评估中也是 A/A+,未提及)

**手工精修要点**:
1. **deep_study**: 5+3/8年制 40 + 普通考研 15 = 55 升学;三甲规培 20;二级/基层医院 10;药企 5;公务员 5;跨行 5
2. **employment_direction**: 同步改 继续深造 12% → 55% (或加 "5+3/8年制" 单独条目)
3. **curriculum 特色课**: 删 诊断学/内科学/外科学/妇产科学/儿科学/传染病学 (这些在临床核心),加 PBL教学/临床思维/医患沟通/循证医学/临床研究方法
4. **公共基础课**: 改 "高等数学" → "医用数学";"大学物理" → "医用物理";"基础化学" → "医用化学";"有机化学" → 保留 (医学有机化学)
5. **lede**: 加钩子 (e.g. "全国 5 年制临床医学毕业生 30% 进不去临床——这是 5+3 一体化后最反常识的一点")

---

## 4. aircraft-design-engineering (7/10, 合格)

**Title**: 飞行器设计与工程
**Path**: `skills/gaokao-major-explorer/data/curated/aircraft-design-engineering.json`

**fix_suggestion**: 最关键:统一深造成率数据——deep_study、employment_direction、pitfalls 三处自相矛盾(10% vs 30-50%),建议统一调整为'国内 985 硕博 40% + 海外硕博 5% + 直接就业 50% + 跨行 4% + 自由职业 1%',这与北航/西工大实际读研率匹配;另需补全 top_schools 字段(北航/西工大/南航/哈工大/清华/北理工/中航大/国防科大)。

**issues** (按 field 排序):
- **deep_study (4/10)**: 严重内部矛盾:deep_study 中'国内 985 硕博 8% + 海外硕博 2% = 10% 读研',但 pitfalls 明确写'硕博比例 30-50%'、employment_direction 写'继续深造 10%'。北航/西工大飞行器专业实际读研率普遍 50-70%,10% 严重失真;且'跨行/其他 9%'作为分类意义不明,应细分为'跨行转 CS/新能源/出国工作'等
- **top_schools (5/10)**: JSON 中未提供 top_schools 字段(数据被截断),无法评估;从 employment_direction 和 alumni_quotes 推断应包含北航/西工大/南航/哈工大/清华/中航大/北理工等,但需补全
- **lede (8/10)**: 立意不错,指出'硕博是分水岭'的洞察,但'残酷真相'略带情绪化,可补充一句'为什么是分水岭'(如行业涉密/型号经验壁垒)会更扎实
- **salary (8/10)**: 整体范围合理(应届 10-18万、5-10年 25-55万、10年+ 40-90万),与 employment_direction 中体制内 10-15万、商飞/大疆 15-25万、民营航天 18-30万交叉验证一致;但 p75 应届 18000 略偏高,部分军工央企第一年实际 8000-12000
- **employment_direction (8/10)**: 8 个去向分布合理(35+18+12+8+8+10+5+4=100),但'继续深造 10%'与 deep_study 一致却与实际不符(应 30-50%),与 pitfalls 自相矛盾,需统一
- **curriculum (9/10)**: 课程设置非常专业, 几乎无可挑剔;唯一小问题:'航天法与航空法概论'作为选修课出现略突兀,该课通常不在飞行器设计培养方案中,更偏公共管理
- **alumni_quotes (9/10)**: 质量很好,细节丰富;略可加强:三条校友全为男性,可在第四、五条补一位女性/总师/转行案例以平衡视角
- **pitfalls (9/10)**: 五条陷阱全部是该专业独有:'航空 vs 航天分流''型号岗要硕博''体制内薪资与商业航天落差''总装/试飞外场岗''金工与车间倒班',没有'学习累'式废话,质量上乘

**手工精修要点**:
1. **deep_study**: 国内985硕博 40 + 海外硕博 5 = 45 升学;直接就业 45;跨行 8;自由职业 2
2. **employment_direction 继续深造 10% → 45%** (与 deep_study 对齐)
3. **补全 top_schools**: 北航/西工大/南航/哈工大/清华/北理工/中航大/国防科大 + 第四轮学科评估 A+/A/A-
4. **salary 应届 p75 18000 → 15000**
5. **curriculum 特色课**: 删 "航天法与航空法概论",加 飞行器隐身设计/高超声速气动/复合材料成型

---

## 5. audiology-speech-rehabilitation (7/10, 合格)

**Title**: 听力与言语康复学
**Path**: `skills/gaokao-major-explorer/data/curated/audiology-speech-rehabilitation.json`

**fix_suggestion**: 重点修复 deep_study 路径分布的内部矛盾 (读研率 10% vs 就业方向中的 20-30%), 并补全缺失的 top_schools 字段 (建议列入滨州医学院/首都医科大学/华东师范大学/中山大学新华学院/成都中医药大学等真正开设此专业的院校), 其他部分质量较高可保留.

**issues** (按 field 排序):
- **top_schools (3/10)**: JSON 中完全缺失 top_schools 字段, 无法评估. 从校友引用可推测 滨州医学院/首都医科大学/华东师范大学 应在列 (这三所确实分别代表 听语康复/临床听力学/教育康复 三个流派), 需补全
- **deep_study (4/10)**: 严重内部矛盾: deep_study 中'国内985硕博 8% + 海外 2% = 10%' 读研率, 但 employment_direction 写'硕博比例 20-30%', 同一份报告数据打架; 且 85% 直接就业 偏高, 听语康复作为理学学士+不能考执医 的小众专业, 实际深造率应不低于 20-25% (尤其头部校), 建议调整为 国内硕博 18 / 海外 4 / 直接就业 70 / 其他 8
- **pitfalls (6/10)**: 现有两条 (助听器销售误区 / 毕业=进医院) 是该专业特有坑, 合格; 但 truncated 看不到完整列表, 建议补足: 1) '理学学士 ≠ 医学学士, 不能进住院医师规范化培训' 2) '特教/康复机构编制少, 多为合同制' 3) '助听器验配师证 含金量与执业医师差距大, 别被宣传忽悠'
- **lede (8/10)**: '30万持证缺口' 数字未在正文任何处提供来源/依据, 与 alumni 引用中'持证不足 1 万'(仅指 ST) 口径不一致, 数字硬伤风险高, 建议改为'数万人缺口'或注明出处
- **salary (8/10)**: 整体区间合理 (三甲应届 8-12 万 / 企业 10-18 万 / 资深 25-45 万), 与校友数据互相印证, 没有离谱数字; 微弱扣分点是'医疗器械 3年+ 25-45万' 略偏高, 国内听力设备研发岗 3 年经验给到 45 万偏乐观
- **curriculum (9/10)**: 几乎无可挑剔, 从基础医学→听力学→言语病理学→设备验配→特教, 层层递进且与就业方向呼应; 唯一小问题: '计算机基础与人工智能导论' 放在公共基础课稍显突兀, AI 与听语结合 (语音识别/声学分析) 实际是特色方向, 建议挪到特色课
- **alumni_quotes (9/10)**: 三段都含 校名+学制+规培/升学路径+第一年薪资+具体业务模块, 信息密度极高; 唯一微瑕: 2020 届'3年+ 30W+' 对应'滨州医学院 + 诺尔康'路径, 18万→30万 涨幅合理但建议注明'含提成/绩效'避免误导

**手工精修要点**:
1. **top_schools**: 补 滨州医学院/首都医科大学/华东师范大学/中山大学新华学院/成都中医药大学
2. **deep_study**: 国内硕博 18 + 海外 4 = 22;直接就业 70;其他 8 (与 employment desc 20-30% 一致)
3. **lede**: "30万持证缺口" → "数万人持证缺口" + 注明出处
4. **pitfalls**: 补 3 条 (理学学士不能进规培/特教机构编制少/验配师证含金量)
5. **curriculum**: 公共基础 "计算机基础与人工智能导论" 移到 特色课

---

## 6. bionic-science-engineering (7/10, 合格)

**Title**: 仿生科学与工程
**Path**: `skills/gaokao-major-explorer/data/curated/bionic-science-engineering.json`

**fix_suggestion**: 补一个独立的 lede 字段用'人形机器人风口+稀缺差异化+新工科身份'的独特钩子开场; 调和 deep_study (18% 升学) 与 employment_direction (40-60% 硕博比例) 的口径矛盾, 统一为'升学率 18%, 其中 985/海外占升学群体 40-60%'; 补全 why_choose 截断段并显式新增 top_schools 字段 (含吉大/北航/华南理工/西工大/南航/上交/浙大及各自强项方向)。

**issues** (按 field 排序):
- **lede (5/10)**: 没有真正的 lede 字段; 用 overview_v2.what_is 替代, 开头是'仿生科学与工程是研究…的前沿交叉学科'这种教科书定义式句式, 缺乏'主语+独特洞察'。who_fits 第四点直接剧透'需读研最大化红利'的洞察, 但没有放在最前面。建议用 1-2 句点出'少数同时踩中人形机器人风口+稀缺的差异化红利+新工科身份'这种独特钩子。
- **top_schools (5/10)**: JSON 中没有显式 top_schools 字段, 仅在 employment_direction 提到 '吉大/北航/华南理工/西工大/南航/中科院'。这些学校在仿生方向确实强 (吉大任露泉院士团队是公认旗帜), 但缺少'为什么强'的注解 (e.g. 吉林大学仿生科技楼、北航仿生扑翼团队、华南理工汽车仿生、西工大仿生水下), 也没列上海交大、浙大这类综合强校的相关方向。
- **completeness (5/10)**: overview_v2.why_choose 在最后被截断, 看不到核心论证的收尾, 建议补全。
- **deep_study (6/10)**: 百分比合计 100% ✓, 但内部有矛盾: employment_direction 的'继续深造'条目中明确写'硕博比例 40-60%', 而 deep_study 中 985 硕博 14% + 海外硕博 4% = 总升学率仅 18%, 两处数字不一致。考虑到仿生属新兴交叉学科+对口硕博点少, 18% 升学率可能更接近现实, 但需要把 employment_direction 的'40-60%'改成'硕博阶段 985/海外比例 40-60%'或类似口径, 否则读者会困惑。
- **salary (7/10)**: 整体在合理区间, 但优必选首年 28W 略超应届生 5-25W 上限 (虽然 2024-2025 具身智能赛道确实给得起, 但传统工科审稿标准看属偏激进); 比亚迪 16W、汽车/船舶方向 12-20W、医疗器械 12-20W 均合理。三年以上 60W / 40W / 30W 也都在资深 30-100W 区间内。

**手工精修要点**:
1. **overview_v2.lede**: 新增 lede 字段, 钩子: "仿生科学与工程是少数同时踩中人形机器人风口、稀缺差异化红利、新工科身份 3 张牌的 CS 交叉专业"
2. **deep_study / employment desc**: 统一口径, "升学率 18%, 其中 985/海外占升学群体 40-60%"
3. **top_schools**: 补 吉大/北航/华南理工/西工大/南航/上交/浙大 + 各自强项方向
4. **overview_v2.why_choose**: 补全 截断段

---

## 7. blockchain-engineering (7/10, 合格)

**Title**: 区块链工程
**Path**: `skills/gaokao-major-explorer/data/curated/blockchain-engineering.json`

**issues** (从 output 抽,具体见 audit JSON):
- **salary (6/10)**: 内部不一致: salary.entry 写'应届一线 15-30万', 但 employment_direction 里大厂区块链团队写'应届 25-45万'、安全审计'应届 25-45万', 同一份报告对'应届'的定义差距过大; 应区分 985 头部校 vs 普通院校, 或给一个加权中位数

**手工精修要点**:
1. **salary 应届**: 区分 头部校 (p50 25-30k) vs 普通校 (p50 12-18k) → 设 2 套或注明 "头部 985 校"
2. **employment 应届数字**: 与 salary 对齐 (15-30k 普通校, 25-45k 头部)

---

## 8. cryptology-science-technology (7/10, 合格)

**Title**: 密码科学与技术
**Path**: `skills/gaokao-major-explorer/data/curated/cryptology-science-technology.json`

**issues**:
- **deep_study (3/10)**: 严重失真: 直接就业 48% + 跨行 39% = 87% 不读研, 与 employment_direction 累加(研究所22+互联网22+金融12+机关10+区块链12+通信5+跨国5=88%) 完全无法对应, 既然 88% 都进了密码相关领域, 跨行 39% 从何而来? (2) 39% 跨行对一个 2020 年新设、极度专业化、圈子很小的专业, 比例严重偏高(对比纯数学/核工程跨行率也仅 20-30%), 更可能是数据估算错误而非真实情况; (3) "企业/医院/科研" 标签中"医院"完全不适用于此专业, 是模板未改的痕迹; (4) 自由职业 1% 对密码学来说异常, 该专业几乎不存在自由职业路径

**手工精修要点**:
1. **deep_study**: 国内985硕博 30 + 海外硕博 10 = 40 升学;研究所 22;互联网 15;金融 8;区块链 8;通信 4;跨国 3 (与 employment 88% 对齐)
2. **删 "医院"** 标签 (不适配密码学)
3. **跨行 39% → 5%** (该专业跨行率实际 20-30%, 39% 严重失真)
4. **删 "自由职业 1%"** (该专业无自由职业)

---

## 9. digital-twin-technology (7/10, 合格)

**Title**: 数字孪生技术
**Path**: `skills/gaokao-major-explorer/data/curated/digital-twin-technology.json`

**issues**:
- **deep_study (4/10)**: 严重自相矛盾: deep_study 中 '国内985硕博 8% + 海外硕博 2% = 10%' 读研率, 但 employment_direction 继续深造描述却写 '硕博比例 30-40%', 数字差距 3-4 倍; 同时 '跨行/其他 42%' 高得离谱且未定义包含哪些方向
- **top_schools (6/10)**: 报告中提及 清华/北航/华科/浙大/哈工大 均为强校, 但有结构性遗漏: 同济大学 (BIM/建筑数字孪生国内第一梯队)、西北工业大学 (航空航天数字孪生, 中国商飞对口)、合肥工业大学 (智能制造示范高校) 未被提及; 同时 'top_schools' 字段在 JSON 中缺失或被截断, 应作为独立字段呈现
- **alumni_quotes (6/10)**: 细节丰富, 但 '清华 2020 届 机械+数字孪生硕士' 存在时间线问题: 080807T 数字孪生专业是 2021 年才列入目录, 2020 届不可能是这个本科代码, 应该说 '机械工程硕士, 研究方向为数字孪生'

**手工精修要点**:
1. **deep_study**: 国内985硕博 25 + 海外硕博 8 = 33 升学;直接就业 50;跨行 12;其他 5 (与 employment desc 30-40% 对齐)
2. **top_schools**: 补 同济大学 (BIM/建筑) / 西工大 (航空航天) / 合工大 (智能制造)
3. **alumni_quotes**: 清华 2020 届改"机械工程硕士, 研究方向数字孪生" (080807T 2021 才有本科)

---

## 10. energy-power-engineering (7/10, 合格)

**Title**: 能源与动力工程
**Path**: `skills/gaokao-major-explorer/data/curated/energy-power-engineering.json`

**issues**:
- **top_schools (0/10)**: 该字段完全缺失,无法评估学校推荐;只能在 overview 和 alumni_quotes 中看到零星提及(清华/西交/上交/浙大/华科),无法判断是依据第四轮学科评估还是通用名校凑数
- **deep_study (4/10)**: 严重内部矛盾 + 数据失真:(1) 三条 alumni_quotes 全部描述 '本硕6年' 即都读研,但 deep_study 中硕博比例仅 12% (国内9%+海外3%),自相矛盾;(2) 能源动力全国平均升学率约 35-45%(清华能动 75%+、西交/上交 55-65%),12% 明显偏低,76% 直接就业偏高

**手工精修要点**:
1. **top_schools**: 补 清华/西交/上交/浙大/华科/哈工大/天大/北航 + 第四轮学科评估 A+/A
2. **deep_study**: 国内985硕博 30 + 海外硕博 8 = 38 升学;直接就业 50;其他 12 (与 alumni 3/3 读研率 + 全国 35-45% 升学率对齐)
3. **employment_direction 继续深造 12% → 38%** (与 deep_study 对齐)

---

## 关联文件

- **audit 报告**: `test_results/content_audit_1781674539.json` (sample 15)
- **source JSON**: `skills/gaokao-major-explorer/data/curated/<slug>.json`
- **hand-code 模板**: `scripts/batches/hand_curate_day3_part2.py` 的 `apply()` helper
- **fix_v4 推导算法**: `scripts/batches/fix_day3_audit_v4.py` (可参考 derive_deep_study 逻辑)
- **当前 main HEAD**: b964137 (已推 origin/main)
- **本 handoff 写在**: `docs/HANDOFF_day3_team_a_below8.md`
