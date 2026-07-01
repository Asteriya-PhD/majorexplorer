/* search.js — 搜专业 / 大类
 *
 * 专业匹配: 复用 PC MajorSearch.search() (SYNONYMS 词典 + 子串/同义词打分)
 * 大类匹配: 保持 mobile 自己的 hierarchy 遍历
 * UI: 保持 mobile 分段 + 大类 + filter 计数
 */
(async () => {
  try {
    await M.init();
  } catch (e) {
    console.error("[search.js] M.init failed", e);
    return;
  }
  // 确保 PC MajorSearch manifest 已加载 (PC 内部 lazy load)
  if (window.MajorSearch && MajorSearch.loadManifest) {
    await MajorSearch.loadManifest();
  }

  const $ = sel => document.querySelector(sel);
  const q = $("#q");
  const clear = $("#clear");
  const filters = $("#filters");
  const results = $("#results");
  if (!results) { console.warn("[search.js] #results not found"); return; }

  let activeType = "all";

  // 大类搜索 (mobile 独有的 hierarchy 遍历)
  function searchCategories(query) {
    const f = query.toLowerCase();
    return (M.hierarchy?.disciplines || []).flatMap(d =>
      (d.sub || []).filter(s => s.name.toLowerCase().includes(f)).map(s => ({...s, parent: d.name, code: d.code}))
    );
  }

  // 把 PC MajorSearch.search 结果格式补齐 (补 discipline/style/theme)
  function mapMajor(matched) {
    const full = M.manifestBySlug[matched.slug];
    return {
      ...matched,
      // PC result 已有 slug/title/style/category/tags/score
      // mobile UI 还需要 theme (styleColor) + 链接
      _full: full,
    };
  }

  function render(query, type) {
    const f = (query || "").trim().toLowerCase();
    if (!f) {
      results.innerHTML = `
        <div class="hot-list">
          <div style="width:100%;">
            <div style="font-family: var(--font-num); color: var(--muted); font-size: 0.75rem; letter-spacing: 0.16em; text-transform: uppercase; margin-bottom: 8px;">热门搜索</div>
            <div style="display:flex; flex-wrap:wrap; gap:8px;">
              ${["人工智能","临床医学","金融","计算机","法学","教育","心理学","会计"].map(t => `<a class="hot" href="#" onclick="document.getElementById('q').value='${t}'; document.getElementById('q').dispatchEvent(new Event('input'));">${t}</a>`).join("")}
            </div>
          </div>
        </div>
      `;
      return;
    }
    // ── 专业匹配: 复用 PC MajorSearch.search (SYNONYMS 词典 + 子串打分) ──
    let majors = [];
    if (window.MajorSearch && typeof MajorSearch.search === "function") {
      const pcResults = MajorSearch.search(query);
      majors = pcResults.map(mapMajor).filter(m => m._full).slice(0, 20);
    } else {
      // 兜底: 5 字段子串 (PC 不可用时)
      majors = M.manifest.majors.filter(m => {
        return (m.title || "").toLowerCase().includes(f)
          || (m.tags || []).some(t => t.toLowerCase().includes(f))
          || (m.category || "").toLowerCase().includes(f)
          || (m.sub_discipline || "").toLowerCase().includes(f)
          || (m.menjia_name || "").toLowerCase().includes(f);
      }).slice(0, 20).map(m => mapMajor(m));
    }
    // ── 大类匹配: mobile 独有 ──
    const cats = searchCategories(query);

    const sections = [];
    if ((type === "all" || type === "major") && majors.length) {
      sections.push({label: "专业", items: majors.map(m => ({
        title: highlight(m.title, f),
        cat: m.category,
        star: true,
        href: `/m/majors/${m.slug}.html`,
        theme: M.styleColor(m.style),
      }))});
    }
    if ((type === "all" || type === "category") && cats.length) {
      sections.push({label: "大类", items: cats.slice(0, 10).map(c => ({
        title: highlight(c.name, f),
        cat: c.parent,
        star: false,
        href: `catalog.html#q=${encodeURIComponent(c.name)}`,
        theme: "#5A4632",
      }))});
    }
    // Day 17 fix: 大类名搜索(如「法医学类」)不应显示"尚未收录"
    // - 有 major 字面匹配 → 不显示 CTA
    // - 有 category 字面匹配 (大类名命中) → 不显示 CTA (用户找到了自己想要的大类)
    // - 只有相似 major 命中 (SYNONYMS 词典触发) → 显示 CTA (避免"硬匹配"误导)
    // - 0 命中 → 显示 CTA (引导用户报告 / 实时生成)
    const hasMajorMatch = majors.some((m) => {
      const t = (m.title || "").toLowerCase();
      return t === f || t.includes(f);
    });
    const hasCatMatch = cats.some((c) => {
      const n = (c.name || "").toLowerCase();
      return n === f || n.includes(f);
    });
    const hasExactMatch = hasMajorMatch || hasCatMatch;
    // 仅有相似 major (无 major/大类字面) 时显示 CTA
    const showCTA = majors.length > 0 && !hasExactMatch;
    const noResultHtml = (!sections.length || showCTA) ? renderNoResult(query) : "";

    if (!sections.length) {
      results.innerHTML = noResultHtml;
      bindReportCard(results, query);
      return;
    }
    results.innerHTML = noResultHtml + sections.map(s => `
      <div class="result-section">
        <div class="result-section-head">
          <span class="l">${s.label}</span>
          <span class="n"><strong>${s.items.length}</strong> 条</span>
        </div>
        ${s.items.map(it => `
          <a class="result" href="${it.href}" style="--theme: ${it.theme};">
            <div class="result-body">
              <h3 class="result-title">${it.title}${it.star ? '<span class="star">★</span>' : ''}</h3>
              <div class="result-cat">${it.cat}</div>
            </div>
            <div class="result-arrow">→</div>
          </a>
        `).join("")}
      </div>
    `).join("");
    if (noResultHtml) bindReportCard(results, query);

    // 更新 filter 计数
    const nM = majors.length, nC = cats.length;
    $("#n-major") && ($("#n-major").textContent = nM);
    $("#n-cat") && ($("#n-cat").textContent = nC);
    $("#n-all") && ($("#n-all").textContent = Number(nM) + Number(nC));
  }

  function highlight(text, q) {
    const i = text.toLowerCase().indexOf(q.toLowerCase());
    if (i < 0) return esc(text);
    return esc(text.slice(0, i)) + "<em>" + esc(text.slice(i, i + q.length)) + "</em>" + esc(text.slice(i + q.length));
  }
  function esc(s) { return String(s).replace(/[<>&"]/g, c => ({"<":"&lt;",">":"&gt;","&":"&amp;",'"':"&quot;"})[c]); }

  // 0 命中: 「不是本科专业名」+ 同义词推荐 (Day 32 v4 与 PC 同步)
  //   复用 PC 端 INTENT_SYNONYMS 字典 (MajorSearch.SYNONYMS 或自定义)
  const INTENT_SYNONYMS = {
    "医生":   ["clinical-medicine","stomatology","traditional-chinese-medicine","nursing","basic-medicine","preventive-medicine"],
    "医师":   ["clinical-medicine","stomatology","traditional-chinese-medicine","psychiatry"],
    "护士":   ["nursing","midwifery"],
    "考公":   ["law","public-administration","chinese-language-literature","accounting","financial-management","economics"],
    "公务员": ["law","public-administration","chinese-language-literature","accounting","financial-management","economics"],
    "教师":   ["chinese-language-literature","mathematics","english","physics","history","pedagogy","preschool-education"],
    "老师":   ["chinese-language-literature","mathematics","english","pedagogy","preschool-education"],
    "律师":   ["law","intellectual-property","prison-studies"],
    "警察":   ["public-order","criminal-investigation","police-management"],
    "心理咨询师": ["psychology","applied-psychology","psychiatry"],
    "会计":   ["accounting","financial-management","auditing"],
    "银行":   ["finance","economics","financial-engineering","insurance"],
    "码农":   ["computer-science","software-engineering","data-science-big-data","artificial-intelligence","network-engineering","information-security"],
    "程序员": ["computer-science","software-engineering","data-science-big-data","artificial-intelligence"],
    "建筑":   ["architecture","urban-planning","civil-engineering","engineering-management"],
  };
  const STYLE_ICON_M = {
    cs:'💻', medicine:'🩺', finance:'💰', law:'⚖️', education:'📚',
    humanities:'📖', sci:'🔬', eng:'⚙️', administration:'🏛️',
    agri:'🌱', arts:'🎨', gongan:'🛡️',
  };
  // style key → theme 色 (复用 M.themeForStyle / 直接从 manifestBySlug 取)
  function _styleColorM(style) {
    if (window.M && typeof M.themeForStyle === "function") return M.themeForStyle(style);
    // 兜底: 跟 PC 端 _styleColor 同款 default 顺序
    const map = { cs:'#3B5BDB', medicine:'#0E7C66', finance:'#8B5A1A', law:'#5B2C6B', education:'#7A4F2C',
      humanities:'#6B5A2E', sci:'#2C6B7A', eng:'#4A4A4A', administration:'#7A2C2C',
      agri:'#4A6B2C', arts:'#8B3A62', gongan:'#2C4A7A' };
    return map[style] || "#5B2C6B";
  }
  function resolveSynonymsM(query) {
    const q = (query || "").trim();
    const slugs = INTENT_SYNONYMS[q];
    if (!slugs) return [];
    const out = [];
    const seen = new Set();
    for (const slug of slugs) {
      if (seen.has(slug)) continue;
      const m = M.manifestBySlug?.[slug];
      if (!m) continue;
      seen.add(slug);
      out.push({
        title: m.title,
        slug: m.slug,
        cat: m.category || "",
        theme: _styleColorM(m.style),
        icon: STYLE_ICON_M[m.style] || "📘",
      });
    }
    return out;
  }
  function renderNoResult(query) {
    const syns = resolveSynonymsM(query);
    const isLikelyIntent = syns.length > 0;
    const title = isLikelyIntent
      ? `「<strong>${esc(query)}</strong>」不是本科专业名`
      : `尚未收录「<strong>${esc(query)}</strong>」`;
    const desc = syns.length > 0
      ? `本站只收 13 门类本科专业. 您可能是想看:`
      : `告诉我们你想看这个专业, 我们优先收录 (精品报告持续扩充中).`;
    const synBlock = syns.length > 0 ? `
      <div class="nrr-synonyms">
        <div class="nrr-syn-label">可能是想看 <span>(${syns.length} 个)</span></div>
        <div class="nrr-syn-list">
          ${syns.slice(0, 6).map(s => `
            <a class="nrr-syn" href="/${esc(s.slug)}.html" style="--theme:${esc(s.theme)};">
              <span class="nrr-syn-emoji" aria-hidden="true">${esc(s.icon || "📘")}</span>
              <span class="nrr-syn-text">
                <span class="nrr-syn-title">${esc(s.title)}</span>
                <span class="nrr-syn-cat">${esc(s.cat)}</span>
              </span>
            </a>
          `).join("")}
        </div>
      </div>
    ` : "";
    const showReportBtn = !isLikelyIntent;
    const reportBlock = showReportBtn ? `
      <div class="nrr-actions">
        <button class="nrr-btn" type="button">💡 想看「${esc(query)}」</button>
      </div>
    ` : "";
    return `
      <div class="no-result-report" data-q="${esc(query)}">
        <div class="nrr-title">${title}</div>
        <div class="nrr-desc">${desc}</div>
        ${synBlock}
        ${reportBlock}
        <div class="nrr-synth-status"></div>
      </div>
    `;
  }
  function bindReportCard(root, query) {
    const card = root.querySelector(".no-result-report");
    if (!card) return;
    const btn = card.querySelector(".nrr-btn");
    btn.addEventListener("click", async () => {
      btn.disabled = true;
      btn.textContent = "发送中...";
      btn.classList.add("loading");
      try {
        const r = await fetch("/api/report", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ type: "missing-major", category: "want", name: query, source: "mobile" }),
        });
        const d = await r.json().catch(() => ({}));
        if (r.ok && d.ok) {
          btn.textContent = "✓ 已收到, 谢谢!";
          btn.classList.remove("loading");
          btn.classList.add("sent");
        } else {
          throw new Error(d.error || `HTTP ${r.status}`);
        }
      } catch (e) {
        btn.textContent = "✕ 发送失败, 用底栏「反馈」重试";
        btn.classList.remove("loading");
        btn.classList.add("failed");
        btn.disabled = false;
        console.error("[search.js] report failed", e);
      }
    });
    // Day 21: 删除 bindSynthCard 调用 (取消实时合成 UI, 后端端点仍保留)
  }

  // ── 4 段进度映射 ──
  function synthStepName(step) {
    if (!step) return "排队中";
    if (step === "init" || step === "validate") return "正在准备";
    if (step === "search" || step === "route_style" || step === "synthesize") return "正在生成内容";
    if (step === "render") return "正在渲染页面";
    if (step === "manifest") return "正在发布";
    if (step === "complete") return "即将完成";
    return "处理中";
  }

  // ── 🔄 实时合成 handler (mobile) ──
  async function bindSynthCard(root, query, source) {
    const card = root.querySelector(".no-result-report");
    if (!card) return;
    const btn = card.querySelector(".nrr-synth-btn");
    const statusEl = card.querySelector(".nrr-synth-status");
    if (!btn) return;

    btn.addEventListener("click", async () => {
      btn.disabled = true;
      const originalLabel = btn.textContent;
      btn.textContent = "排队中...";
      statusEl.textContent = "";
      statusEl.className = "nrr-synth-status";

      try {
        const r = await fetch("/api/synth/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: query, source }),
        });
        const d = await r.json().catch(() => ({}));
        if (!r.ok || !d.ok) {
          if (r.status === 429) throw new Error("请求太频繁, 请 1 分钟后再试");
          throw new Error(d.error || `HTTP ${r.status}`);
        }

        if (d.deduped && d.status === "done" && d.output_url) {
          statusEl.textContent = "✅ 已存在, 跳转中...";
          statusEl.classList.add("ok");
          setTimeout(() => { location.href = d.output_url; }, 600);
          return;
        }

        const runId = d.run_id;
        statusEl.textContent = "⏳ 正在准备, 预计 60-120 秒";
        statusEl.classList.add("running");
        btn.textContent = "正在合成...";

        let attempts = 0;
        const poll = setInterval(async () => {
          attempts++;
          try {
            const sr = await fetch(`/api/synth/status?run_id=${runId}`);
            const s = await sr.json().catch(() => ({}));
            if (!sr.ok) {
              if (attempts > 3) {
                clearInterval(poll);
                throw new Error(`状态查询失败 (HTTP ${sr.status})`);
              }
              return;
            }
            if (s.status === "done" && s.output_url) {
              clearInterval(poll);
              statusEl.textContent = "✅ 合成完成, 跳转中...";
              statusEl.classList.remove("running");
              statusEl.classList.add("ok");
              setTimeout(() => { location.href = s.output_url; }, 600);
              return;
            }
            if (s.status === "failed" || s.status === "dead") {
              clearInterval(poll);
              statusEl.innerHTML = `❌ 合成失败: ${esc(s.error || "未知错误")}. <a href="#" class="nrr-report-link">📨 报告给我们</a>`;
              statusEl.classList.remove("running");
              statusEl.classList.add("failed");
              btn.disabled = false;
              btn.textContent = originalLabel;
              return;
            }
            statusEl.textContent = `⏳ ${synthStepName(s.step)} (${attempts})`;
          } catch (pollErr) {
            console.error("[search.js] poll error", pollErr);
          }
          if (attempts > 100) {
            clearInterval(poll);
            statusEl.textContent = "⏰ 超时 (5min)";
            statusEl.classList.remove("running");
            statusEl.classList.add("failed");
            btn.disabled = false;
            btn.textContent = originalLabel;
          }
        }, 3000);
      } catch (e) {
        statusEl.innerHTML = `❌ ${esc(e.message || "提交失败")}. <a href="#" class="nrr-report-link">📨 报告给我们</a>`;
        statusEl.classList.add("failed");
        btn.disabled = false;
        btn.textContent = originalLabel;
        console.error("[search.js] synth failed", e);
      }

      const reportLink = statusEl.querySelector(".nrr-report-link");
      if (reportLink) {
        reportLink.addEventListener("click", async (ev) => {
          ev.preventDefault();
          const rr = await fetch("/api/report", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ type: "missing-major", name: query, source }),
          });
          const rd = await rr.json().catch(() => ({}));
          if (rr.ok && rd.ok) {
            statusEl.innerHTML = "✅ 已上报, 我们会跟进";
            statusEl.classList.remove("failed");
            statusEl.classList.add("ok");
          }
        });
      }
    });
  }

  // 初始渲染 + 计数
  const urlQ = new URLSearchParams(location.search).get("q") || "";
  if (urlQ && q) {
    q.value = urlQ;
    if (clear) clear.style.display = "flex";
    render(urlQ, activeType);
  } else {
    render("");
  }
  const nM = M.manifest.majors.length;
  const nC = (M.hierarchy?.disciplines || []).reduce((a, d) => a + (d.sub || []).length, 0);
  if ($("#n-major")) $("#n-major").textContent = nM;
  if ($("#n-cat")) $("#n-cat").textContent = nC;
  if ($("#n-all")) $("#n-all").textContent = nM + nC;

  if (q) {
    let timer;
    q.addEventListener("input", () => {
      clear.style.display = q.value ? "flex" : "none";
      clearTimeout(timer);
      timer = setTimeout(() => render(q.value, activeType), 120);
    });
  }
  if (clear) {
    clear.addEventListener("click", () => { q.value = ""; clear.style.display = "none"; render("", activeType); q.focus(); });
  }
  if (filters) {
    filters.querySelectorAll(".filter[data-type]").forEach(f => {
      f.addEventListener("click", () => {
        if (f.disabled) return;
        filters.querySelectorAll(".filter").forEach(x => x.classList.remove("on"));
        f.classList.add("on");
        activeType = f.dataset.type;
        render(q.value, activeType);
      });
    });
  }
})();
