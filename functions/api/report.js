// functions/api/report.js — 接收 user 反馈/未收录报告, 创建 GitHub Issue
//
// 用途:
//   POST /api/report
//   {type: "missing-major" | "feedback", name?: string, text?: string, source: "pc"|"mobile"}
//
// 返回:
//   {ok: true, issue_url: "https://github.com/.../issues/N", number: N}
//   {ok: false, error: "..."} + HTTP 4xx/5xx
//
// 安全 / 防滥用:
//   - 60s 1 次 / IP (in-memory Map, CF cold start 时会重置, 起步可接受)
//   - 长度校验: name ≤ 50, text ≤ 1000
//   - 不收 PII, 只存 type/name/text/source/ua/uuid/ts
//
// 凭据:
//   env.GITHUB_TOKEN (server 端, 来自 `wrangler pages secret put` 或 dashboard)
//   env.GITHUB_REPO (可选, 默认 Asteriya-PhD/majorexplorer)

const REPO_DEFAULT = "Asteriya-PhD/majorexplorer";
const RATE_LIMIT_MS = 60_000;
const MAX_RL_ENTRIES = 1000;

// 进程内 rate limit (per IP)
const _rl = new Map();

function rateLimited(ip) {
  const now = Date.now();
  const last = _rl.get(ip);
  if (last && now - last < RATE_LIMIT_MS) return true;
  _rl.set(ip, now);
  // GC: 防止 Map 无限增长
  if (_rl.size > MAX_RL_ENTRIES) {
    const cutoff = now - 120_000;
    for (const [k, t] of _rl) if (t < cutoff) _rl.delete(k);
  }
  return false;
}

function json(obj, status = 200, extra = {}) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      ...extra,
    },
  });
}

async function createIssue(env, payload) {
  const repo = env.GITHUB_REPO || REPO_DEFAULT;
  if (!env.GITHUB_TOKEN) {
    return { ok: false, status: 500, detail: "GITHUB_TOKEN missing on server" };
  }
  let res;
  try {
    res = await fetch(`https://api.github.com/repos/${repo}/issues`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
        "Accept": "application/vnd.github+json",
        "User-Agent": "MajorExplorer-Report/1.0",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  } catch (e) {
    return { ok: false, status: 502, detail: `fetch failed: ${String(e && e.message || e).slice(0, 200)}` };
  }
  let text;
  try {
    text = await res.text();
  } catch (e) {
    return { ok: false, status: 502, detail: `read body failed: ${String(e && e.message || e).slice(0, 200)}` };
  }
  if (!res.ok) {
    return { ok: false, status: res.status, detail: text.slice(0, 500) };
  }
  try {
    const gh = JSON.parse(text);
    return { ok: true, issue_url: gh.html_url, number: gh.number };
  } catch (e) {
    return { ok: false, status: 502, detail: "github response not JSON: " + text.slice(0, 200) };
  }
}

export async function onRequestPost(ctx) {
  const { request, env } = ctx;

  // 1. parse + validate
  let body;
  try {
    body = await request.json();
  } catch (e) {
    return json({ ok: false, error: "invalid JSON body" }, 400);
  }
  if (!body || typeof body !== "object") {
    return json({ ok: false, error: "body must be object" }, 400);
  }
  const { type, name, text, source } = body;
  if (type !== "missing-major" && type !== "feedback") {
    return json({ ok: false, error: "type must be 'missing-major' or 'feedback'" }, 400);
  }
  if (source !== "pc" && source !== "mobile") {
    return json({ ok: false, error: "source must be 'pc' or 'mobile'" }, 400);
  }
  if (type === "missing-major" && (!name || typeof name !== "string" || name.length > 50)) {
    return json({ ok: false, error: "missing-major requires name (1-50 chars)" }, 400);
  }
  if (type === "feedback" && text && (typeof text !== "string" || text.length > 1000)) {
    return json({ ok: false, error: "feedback text max 1000 chars" }, 400);
  }

  // 2. rate limit
  const ip = request.headers.get("cf-connecting-ip")
    || request.headers.get("x-forwarded-for")?.split(",")[0]?.trim()
    || "anon";
  if (rateLimited(ip)) {
    return json(
      { ok: false, error: "请求太频繁, 1 分钟后再试" },
      429,
      { "Retry-After": "60" }
    );
  }

  // 3. build GH issue payload
  const ts = new Date().toISOString();
  const ua = request.headers.get("user-agent") || "n/a";
  const uuid = crypto.randomUUID();
  const src = source === "pc" ? "PC" : "Mobile";

  let title, labels, bodyText;
  if (type === "missing-major") {
    const safeName = name.replace(/[\r\n]/g, " ").slice(0, 50);
    title = `[missing-major] ${safeName}`;
    labels = ["user-request", source];
    bodyText = [
      `## 用户报告: 尚未收录「${safeName}」`,
      ``,
      `## 详情`,
      ``,
      `- **来源**: ${src}`,
      `- **时间**: ${ts}`,
      `- **UA**: ${ua}`,
      `- **关联 ID**: ${uuid}`,
      ``,
      `> 用户搜了「${safeName}」没找到结果, 点击报告给我们.`,
    ].join("\n");
  } else {
    const cleanText = (text || "(用户未填内容)").replace(/\r\n/g, "\n").slice(0, 1000);
    const firstLine = cleanText.split("\n")[0].slice(0, 60);
    title = `[feedback] ${firstLine}`;
    labels = ["user-feedback", source];
    bodyText = [
      `## 用户反馈`,
      ``,
      cleanText,
      ``,
      `---`,
      ``,
      `- **来源**: ${src}`,
      `- **时间**: ${ts}`,
      `- **UA**: ${ua}`,
      `- **关联 ID**: ${uuid}`,
    ].join("\n");
  }

  // 4. POST GH Issues API
  if (!env.GITHUB_TOKEN) {
    return json({ ok: false, error: "GITHUB_TOKEN not configured on server" }, 500);
  }
  const result = await createIssue(env, { title, labels, body: bodyText });
  if (!result.ok) {
    return json(
      {
        ok: false,
        error: `github ${result.status}`,
        detail: result.detail,
      },
      502
    );
  }
  return json({ ok: true, issue_url: result.issue_url, number: result.number });
}

// 405 for other methods
export async function onRequest(ctx) {
  if (ctx.request.method !== "POST") {
    return json({ ok: false, error: "POST only" }, 405);
  }
  return onRequestPost(ctx);
}
