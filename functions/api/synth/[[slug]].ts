/**
 * functions/api/synth/[[slug]].ts — GET /api/synth/{slug}
 *
 * 查 D1: 该 slug 是否有 status='done' 的 job.
 *   - 有: 读 public/{slug}.html (已被 git push 到 Pages), 直接 serve
 *   - 没有: 404, 让前端 fallback 到 synth-client.js
 *
 * 走 Pages 静态优先:
 *   - /{slug}.html 静态存在 → 静态命中 (300ms 内 CDN)
 *   - 用户命中长尾 → 跳 /api/synth/{slug} → 本函数查 D1 + 返动态 HTML
 *
 * 部署: Cloudflare Pages Functions, env.DB = D1 binding
 */

import type { PagesFunction } from "@cloudflare/workers-types";
import { getJobBySlug, type D1Env } from "../_synth/d1";

export const onRequest: PagesFunction<D1Env> = async ({ request, env, params }) => {
  const slug = (params.slug as string | undefined)?.replace(/\.html$/, "");
  if (!slug) {
    return new Response("slug required", { status: 400 });
  }

  const job = await getJobBySlug(env.DB, slug);
  if (!job) {
    return new Response("major not synthesized yet", {
      status: 404,
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  }

  // 走 ASSETS binding (Pages 自带), 不用 fetch 自身
  try {
    const html = await env.ASSETS.fetch(`/${slug}.html`);
    if (html.status === 200) {
      return new Response(html.body, {
        status: 200,
        headers: {
          "Content-Type": "text/html; charset=utf-8",
          "Cache-Control": "public, max-age=60",
          "X-Synth-Source": "dynamic-fallback",
        },
      });
    }
  } catch {
    // ASSETS 不可用时回退 KV
  }

  // 静态还没部署完, 兜底 JSON
  return new Response(
    JSON.stringify({
      ok: true,
      run_id: job.run_id,
      status: job.status,
      output_url: job.output_url,
      message: "major 已合成, 静态资源尚未部署完成, 请稍后重试或访问 /api/synth/status",
    }),
    {
      status: 202,
      headers: { "Content-Type": "application/json; charset=utf-8" },
    },
  );
};
