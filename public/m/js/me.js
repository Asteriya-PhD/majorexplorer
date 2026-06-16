/* me.js — 浏览历史 + 收藏统计 */
(async () => {
  await M.init();
  const HKEY = "m.history.v1";
  const WKEY = "m.wishlist.v1";
  const histRoot = document.getElementById("history");
  if (!histRoot) return;

  function load(k) { try { return JSON.parse(localStorage.getItem(k) || "[]"); } catch { return []; } }
  function save(k, v) { localStorage.setItem(k, JSON.stringify(v)); }

  // 头部统计
  const histCount = load(HKEY);
  const wishCount = load(WKEY);
  document.getElementById("hist-count").textContent = histCount.length;
  document.getElementById("wish-count").textContent = wishCount.length;

  // 历史列表
  if (!histCount.length) {
    histRoot.innerHTML = `<div class="hist-row">
      <div class="hist-body">
        <div class="hist-cat">—</div>
        <div class="hist-title" style="color: var(--muted);">还没读过任何专业</div>
      </div>
    </div>`;
  } else {
    histRoot.innerHTML = histCount.slice(0, 10).map(h => {
      const m = M.manifestBySlug[h.slug];
      if (!m) return "";
      return `<a class="hist-row" href="majors/${m.slug}.html" style="--theme: ${M.styleColor(m.style)};">
        <div class="hist-body">
          <div class="hist-cat">${m.category}${h.star ? '<span class="star">★</span>' : ''}</div>
          <div class="hist-title">${m.title}</div>
        </div>
        <div class="hist-time">${h.t || ''}</div>
      </a>`;
    }).join("");
  }

  // 清空
  const clr = document.getElementById("hist-clear");
  if (clr) clr.addEventListener("click", () => {
    if (!confirm("清空所有浏览记录?")) return;
    save(HKEY, []);
    location.reload();
  });

  // ── 反馈 modal (→ /api/report type: feedback) ──
  const fbBtn = document.getElementById("feedback-btn");
  const fbModal = document.getElementById("feedback-modal");
  const fbBg = document.getElementById("feedback-modal-bg");
  const fbCancel = document.getElementById("fb-cancel");
  const fbSend = document.getElementById("fb-send");
  const fbText = document.getElementById("feedback-text");
  function openFb() { if (fbModal) { fbModal.hidden = false; fbText.value = ""; fbText.focus(); } }
  function closeFb() { if (fbModal) { fbModal.hidden = true; } }
  if (fbBtn) fbBtn.addEventListener("click", openFb);
  if (fbBg) fbBg.addEventListener("click", closeFb);
  if (fbCancel) fbCancel.addEventListener("click", closeFb);
  if (fbSend) {
    fbSend.addEventListener("click", async () => {
      const text = (fbText.value || "").trim();
      fbSend.disabled = true; fbText.disabled = true; fbCancel.disabled = true;
      const oldText = fbSend.textContent;
      fbSend.textContent = "发送中...";
      try {
        const r = await fetch("/api/report", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ type: "feedback", text, source: "mobile" }),
        });
        const d = await r.json().catch(() => ({}));
        if (r.ok && d.ok) {
          fbSend.textContent = "✓ 已收到, 谢谢!";
          fbSend.classList.add("sent");
          setTimeout(closeFb, 1400);
        } else {
          throw new Error(d.error || `HTTP ${r.status}`);
        }
      } catch (e) {
        fbSend.textContent = "✕ 失败, 邮件 major.explorer.feedback@gmail.com";
        fbSend.classList.add("failed");
        fbSend.disabled = false; fbText.disabled = false; fbCancel.disabled = false;
        console.error("[me.js] feedback failed", e);
        // 3 秒后恢复原状, 让用户重试
        setTimeout(() => {
          fbSend.textContent = oldText; fbSend.classList.remove("failed");
        }, 3000);
      }
    });
  }
})();
