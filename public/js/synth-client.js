/* ====================================================================
 * synth-client.js — 长尾专业按需生成前端轮询
 *
 * 在 major-search.js miss CTA 触发后, 调 SCF /synth/generate
 * → 拿 run_id → 轮询 /synth/status → done 跳页 / failed 还原
 *
 * API base URL 配置:
 *   - 默认: 部署时通过 <meta name="synth-api" content="..."> 注入
 *   - fallback: 同源 /synth
 *
 * 公开 API (window.SynthClient):
 *   start(query, resultsEl)    用户点 CTA 时调用
 *   getApiBase()               内部用, 也可外部覆盖
 *
 * 状态机: idle → queued → running(轮询) → done(跳页) | failed(还原)
 * ==================================================================== */

(function (global) {
  "use strict";

  // ── 配置 ──
  function getApiBase() {
    const meta = document.querySelector('meta[name="synth-api"]');
    if (meta) return meta.getAttribute("content");
    return global.location.origin + "/synth";
  }

  function _slugify(q) {
    // 与 SCF 端一致: 非英文小写 → 保留中文字符
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
  async function start(query, resultsEl) {
    if (!query || !resultsEl) return;

    // 禁用按钮, 隐藏 CTA
    const btn = resultsEl.querySelector(".ms-synth-btn");
    if (btn) btn.disabled = true;
    const cta = resultsEl.querySelector(".ms-synth-cta");
    if (cta) cta.style.opacity = "0.4";

    _setProgress(resultsEl, "queued", "排队中, 准备调用 LLM ...");

    const api = getApiBase();
    const slug = _slugify(query);

    let resp;
    try {
      resp = await fetch(api + "/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: query, slug: slug }),
      });
    } catch (e) {
      _setProgress(resultsEl, "failed",
        "服务暂未上线 (SCF 未部署), 请留邮箱催更");
      console.error("synth generate network error", e);
      return;
    }

    if (resp.status === 404) {
      _setProgress(resultsEl, "failed",
        "按需生成功能暂未上线 (404), 留邮箱催更 → " + (api));
      return;
    }
    if (!resp.ok) {
      const t = await resp.text();
      _setProgress(resultsEl, "failed", "服务异常 " + resp.status + ": " + t.slice(0, 80));
      return;
    }

    const data = await resp.json();
    if (!data.run_id) {
      _setProgress(resultsEl, "failed", "未拿到 run_id");
      return;
    }

    // ── 同步模式: SCF 在 POST 内跑完才返回 (≤15min)
    //    data.status 已是最终状态
    if (data.status === "done") {
      _setProgress(resultsEl, "done", "✅ 完成, 正在跳转 ...");
      setTimeout(() => {
        global.location.href = "/" + (data.output_url || slug + ".html");
      }, 600);
      return;
    }

    if (data.status === "failed") {
      _setProgress(resultsEl, "failed", "❌ " + (data.error || "合成失败"));
      return;
    }

    // ── 异步 fallback: 拿到 run_id 后轮询 ──
    _setProgress(resultsEl, "running", "正在合成, 约 5-15 分钟 ...");
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
    const maxTries = 200; // 200 × 5s = 16min, 略超 SCF 15min 安全垫

    while (tries < maxTries) {
      tries++;
      await new Promise((r) => setTimeout(r, 5000));
      let st;
      try {
        const r = await fetch(api + "/status?run_id=" + encodeURIComponent(runId));
        st = await r.json();
      } catch (e) {
        _setProgress(resultsEl, "running", "轮询中 (网络抖动) ...");
        continue;
      }
      if (!st || !st.status) {
        _setProgress(resultsEl, "running", "轮询中 ...");
        continue;
      }
      const stepLabel = STEP_LABELS[st.step] || st.step || "处理中";
      _setProgress(resultsEl, st.status,
        st.status === "running" ? "⏳ " + stepLabel + " (" + Math.round((st.progress || 0) * 100) + "%)"
                                 : st.status === "done" ? "✅ 完成, 跳转中 ..."
                                 : "❌ " + (st.error || "失败"));

      if (st.status === "done") {
        setTimeout(() => {
          global.location.href = "/" + (st.output_url || slug + ".html");
        }, 600);
        return;
      }
      if (st.status === "failed") {
        return;
      }
    }
    _setProgress(resultsEl, "failed", "❌ 等待超时, 请刷新重试");
  }

  // ── 暴露 ──
  global.SynthClient = {
    start: start,
    getApiBase: getApiBase,
  };
})(window);
