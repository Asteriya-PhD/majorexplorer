/**
 * functions/api/synth/generate.ts — POST /api/synth/generate
 *
 * 入队 (不入 D1 写耗时):
 *   body: { title: "翻译", slug?: "translation", style?: "humanities", email?: "x@y.z" }
 *   行为:
 *     1. 校验 title (1-40 字, 必填)
 *     2. slug 没传则用 title slugify
 *     3. 查 D1: 同 slug 24h 内 done → 直接返 output_url
 *     4. 查 D1: 同 slug 已 queued/running → 返原 run_id (去重)
 *     5. 生成 run_id = uuid hex[16]
 *     6. INSERT status='queued' → 返 { run_id, status_url }
 *
 *   耗时: < 5ms (D1 put)
 *
 * 部署: Cloudflare Pages Functions, env.DB = D1 binding
 */

import type { PagesFunction } from "@cloudflare/workers-types";
import { createJob, getJob, getJobBySlug, type D1Env } from "../_synth/d1";

interface GenerateReq {
  title?: string;
  slug?: string;
  style?: string;
  email?: string;
}

const VALID_STYLES = new Set([
  "cs", "eng", "medicine", "education", "finance", "law",
  "humanities", "sci", "administration", "agri", "arts",
  "gongan", "business",
]);

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function json(body: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(body), {
    ...init,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Cache-Control": "no-store",
      ...(init.headers ?? {}),
    },
  });
}

function slugify(title: string): string {
  return title
    .toLowerCase()
    .replace(/[\s_]+/g, "-")
    .replace(/[^\p{Letter}\p{Number}-]+/gu, "")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 64);
}

function newRunId(): string {
  // 16 hex chars, 用 crypto.randomUUID() 截前 16
  return crypto.randomUUID().replace(/-/g, "").slice(0, 16);
}

export const onRequest: PagesFunction<D1Env> = async ({ request, env }) => {
  if (request.method === "OPTIONS") {
    return json({ ok: true });
  }
  if (request.method !== "POST") {
    return json({ ok: false, error: "method not allowed" }, { status: 405 });
  }

  // ── 1. 解析 body ──
  let body: GenerateReq;
  try {
    body = (await request.json()) as GenerateReq;
  } catch {
    return json({ ok: false, error: "body 不是 JSON" }, { status: 400 });
  }

  const title = (body.title ?? "").trim();
  if (!title) {
    return json({ ok: false, error: "title 必填" }, { status: 400 });
  }
  if (title.length > 40) {
    return json({ ok: false, error: "title 过长 (≤40 字)" }, { status: 400 });
  }

  const slug = (body.slug ?? "").trim() || slugify(title);
  if (!slug) {
    return json({ ok: false, error: "slug 派生失败" }, { status: 400 });
  }

  let style: string | null = (body.style ?? "").trim() || null;
  if (style && !VALID_STYLES.has(style)) {
    return json({ ok: false, error: `style 不合法: ${style}` }, { status: 400 });
  }

  const email = (body.email ?? "").trim() || null;
  if (email && !EMAIL_RE.test(email)) {
    return json({ ok: false, error: "email 格式错误" }, { status: 400 });
  }

  // ── 2. 去重: 同 slug 已 done → 直接返 output_url ──
  const existing = await getJobBySlug(env.DB, slug);
  if (existing) {
    return json({
      ok: true,
      run_id: existing.run_id,
      status: "done",
      output_url: existing.output_url,
      quality_score: existing.quality_score,
      deduped: true,
    });
  }

  // ── 3. 去重: 同 slug 正在跑 → 返原 run_id ──
  //    (注: getJob 走 run_id, 这里临时跑 by-slug + status in (queued/running))
  //    D1 没复合索引时, 这里扫表 OK (D1 单 zone 几千行毫无压力)
  const { results: inFlight } = await env.DB
    .prepare(
      `SELECT run_id, status FROM synth_jobs
       WHERE slug = ?1 AND status IN ('queued', 'running')
       ORDER BY created_at DESC LIMIT 1`,
    )
    .bind(slug)
    .all<{ run_id: string; status: string }>();
  if (inFlight && inFlight.length > 0) {
    return json({
      ok: true,
      run_id: inFlight[0].run_id,
      status: inFlight[0].status,
      status_url: `/api/synth/status?run_id=${inFlight[0].run_id}`,
      deduped: true,
    });
  }

  // ── 4. 生成 run_id + 入队 ──
  const run_id = newRunId();
  await createJob(env.DB, { run_id, title, slug, style, email });

  return json({
    ok: true,
    run_id,
    status: "queued",
    status_url: `/api/synth/status?run_id=${run_id}`,
  });
};
