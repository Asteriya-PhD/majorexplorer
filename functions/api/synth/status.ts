/**
 * functions/api/synth/status.ts — GET /api/synth/status?run_id=xxx
 *
 * 查 D1 返 1 个 job 状态.
 *
 * 部署: Cloudflare Pages Functions, env.DB = D1 binding
 */

import type { PagesFunction } from "@cloudflare/workers-types";
import { getJob, type D1Env } from "../_synth/d1";

function json(body: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(body), {
    ...init,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Cache-Control": "no-store",
      ...(init.headers ?? {}),
    },
  });
}

export const onRequest: PagesFunction<D1Env> = async ({ request, env }) => {
  if (request.method === "OPTIONS") {
    return json({ ok: true });
  }

  const url = new URL(request.url);
  const runId = url.searchParams.get("run_id")?.trim();
  if (!runId) {
    return json({ ok: false, error: "run_id 必填" }, { status: 400 });
  }

  const job = await getJob(env.DB, runId);
  if (!job) {
    return json({ ok: false, error: "run_id not found" }, { status: 404 });
  }

  // 直接返整行 (前端只要 .status / .step / .progress)
  return json({
    ok: true,
    run_id: job.run_id,
    status: job.status,
    step: job.step,
    progress: job.progress,
    title: job.title,
    slug: job.slug,
    style: job.style,
    output_url: job.output_url,
    quality_score: job.quality_score,
    cost_cny: job.cost_cny,
    error: job.error,
    started_at: job.started_at,
    updated_at: job.updated_at,
    finished_at: job.finished_at,
  });
};
