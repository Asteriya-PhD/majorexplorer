/* ====================================================================
 * synth-client.js — 长尾专业按需生成前端 (Hybrid v1: CF Pages Function)
 *
 * 用户在 major-search.js miss CTA 触发后, 调 /api/synth/generate
 *   → 拿 run_id → polling /api/synth/status
 *   → done 跳页 / failed 还原
 *
 * API base URL 配置:
 *   - 默认: 同源 /api/synth
 *   - 可通过 <meta name="synth-api" content="https://..."> 覆盖 (跨域部署)
 *
 * 公开 API (window.SynthClient):
 *   start(query, resultsEl, email?)  用户点 CTA 时调用
 *   getApiBase()                     内部用, 也可外部覆盖
 *
 * 状态机: idle → queued → running(轮询) → done(跳页) | failed(还原)
 *
 * 时延: 5-20 分钟 (1min cron + 5-15min Python + 30s 部署)
 * 邮箱: 可选, 完成后理论上发邮件 (v1 占位: 存 D1 不发, 改 polling)
 * ==================================================================== */

(function (global) {
  "use strict";

  // ── 配置 ──
  function getApiBase() {
    const meta = document.querySelector('meta[name="synth-api"]');
    if (meta) return meta.getAttribute("content");
    return global.location.origin + "/api/synth";
  }

  function _slugify(q) {
    return q.toLowerCase().replace(/\s+/g, "-").slice(0, 64);
  }

  function _setProgress(resultsEl, state, msg) {
    const box = resultsEl.querySelector(".ms-synth-progress");
    if (!box) return;
    box.hidden = false;
    const stages = ["验证", "搜索", "路由", "合成", "渲染", "入仓"];
    let pct = 0;
    if (state === "queued") pct = 5;
    else if (state === "running") {
      const step = box.dataset.step || "validate";
      const i = stages.indexOf(step);
      pct = Math.min(95, 10 + i * 16);
    } else if (state === "done") pct = 100;
    box.innerHTML =
      '<div class="ms-synth-bar"><div class="ms-synth-bar-fill" style="width:' + pct + '%"></div></div>' +
      '<div class="ms-synth-msg">' + (msg || state) + '</div>';
  }

  // ── 主入口 ──
  async function start(query, resultsEl, email) {
    if (!query || !resultsEl) return;

    // 禁用按钮 + 邮箱框, 隐藏 CTA
    const btn = resultsEl.querySelector(".ms-synth-btn");
    if (btn) btn.disabled = true;
    const emailInput = resultsEl.querySelector(".ms-synth-email");
    if (emailInput) emailInput.disabled = true;
    const cta = resultsEl.querySelector(".ms-synth-cta");
    if (cta) cta.style.opacity = "0.6";

    _setProgress(resultsEl, "queued", "排队中, 已加入合成队列 ...");

    const api = getApiBase();
    const slug = _slugify(query);

    let resp;
    try {
      const body = { title: query, slug: slug };
      if (email) body.email = email;
      resp = await fetch(api + "/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    } catch (e) {
      _setProgress(resultsEl, "failed",
        "网络异常, 请稍后重试 (Hybrid 后端可能未部署)");
      console.error("synth generate network error", e);
      return;
    }

    if (resp.status === 404) {
      _setProgress(resultsEl, "failed",
        "按需生成功能暂未上线 (404), 请留邮箱催更");
      return;
    }
    if (resp.status === 503) {
      const t = await resp.text();
      _setProgress(resultsEl, "failed", "后端暂不可用: " + t.slice(0, 100));
      return;
    }
    if (!resp.ok) {
      let t = "";
      try { t = await resp.text(); } catch (_) {}
      _setProgress(resultsEl, "failed", "服务异常 " + resp.status + ": " + t.slice(0, 100));
      return;
    }

    const data = await resp.json();
    if (!data.run_id) {
      _setProgress(resultsEl, "failed", "未拿到 run_id: " + JSON.stringify(data).slice(0, 100));
      return;
    }

    // ── dedupe: 同 slug 已 done → 直接跳 ──
    if (data.status === "done" && data.output_url) {
      _setProgress(resultsEl, "done", "✅ 已合成, 跳转中 ...");
      setTimeout(() => {
        global.location.href = data.output_url;
      }, 600);
      return;
    }
    // ── dedupe: 同 slug 正在跑 → 提示后继续 poll ──
    if (data.deduped && (data.status === "running" || data.status === "queued")) {
      _setProgress(resultsEl, "running", "⏳ 同名专业正在合成中, 继续等待 ...");
    }

    // ── 异步: 拿到 run_id 后 polling status (Hybrid 默认) ──
    _setProgress(resultsEl, "running", "⏳ 正在合成, 约 5-20 分钟 (可关闭页面, 邮箱通知)");
    await _poll(data.run_id, api, resultsEl, slug);
  }

  async function _poll(runId, api, resultsEl, slug) {
    const STEP_LABELS = {
      validate: "校验专业名",
      search: "搜索资料",
      route_style: "选主题",
      synthesize: "合成 JSON",
      render: "渲染 HTML",
      manifest: "入仓",
      complete: "完成",
    };
    let tries = 0;
    const maxTries = 1800; // 1800 × 2s = 60min, Hybrid 5-20min 一般够

    while (tries < maxTries) {
      tries++;
      // 第 1 分钟每 2s 查, 1 分钟后每 5s 查, 5 分钟后每 10s 查
      let delay = 2000;
      if (tries > 30) delay = 5000;
      if (tries > 150) delay = 10000;
      await new Promise((r) => setTimeout(r, delay));

      let st;
      try {
        const r = await fetch(api + "/status?run_id=" + encodeURIComponent(runId));
        if (r.status === 404) {
          _setProgress(resultsEl, "failed", "run_id 已过期或不存在");
          return;
        }
        st = await r.json();
      } catch (e) {
        _setProgress(resultsEl, "running", "⏳ 轮询中 (网络抖动) ...");
        continue;
      }
      if (!st || !st.status) {
        _setProgress(resultsEl, "running", "⏳ 轮询中 ...");
        continue;
      }
      // 更新 step 给 progress bar 用
      const box = resultsEl.querySelector(".ms-synth-progress");
      if (box && st.step) box.dataset.step = st.step;

      const stepLabel = STEP_LABELS[st.step] || st.step || "处理中";
      const pct = Math.round((st.progress || 0) * 100);
      _setProgress(resultsEl, st.status,
        st.status === "running" ? "⏳ " + stepLabel + " (" + pct + "%)"
                                 : st.status === "done" ? "✅ 完成, 跳转中 ..."
                                 : st.status === "dead" ? "💀 重试 3 次仍失败: " + (st.error || "未知")
                                 : "❌ " + (st.error || "失败"));

      if (st.status === "done") {
        setTimeout(() => {
          global.location.href = "/" + (st.output_url || slug + ".html");
        }, 600);
        return;
      }
      if (st.status === "failed" || st.status === "dead") {
        return;
      }
    }
    _setProgress(resultsEl, "failed", "❌ 等待超时 (60min), 请刷新重试");
  }

  // ── 暴露 ──
  global.SynthClient = {
    start: start,
    getApiBase: getApiBase,
  };
})(window);
