/**
 * functions/api/_synth/d1.ts — D1 客户端封装 + 类型定义
 *
 * Pages Functions 注入: env.DB (D1Database binding)
 * Worker (GH Action) 注入: 同 schema, 用 HTTP REST API
 *
 * Schema 跟 migrations/0001_init.sql 一致, 改一处要改两处.
 */

export interface SynthJob {
  run_id: string;
  status: "queued" | "running" | "done" | "failed" | "dead";
  step: string;
  progress: number;
  title: string;
  slug: string;
  style: string | null;
  email: string | null;
  error: string | null;
  attempts: number;
  output_url: string | null;
  html_size: number | null;
  quality_score: number | null;
  cost_cny: number | null;
  started_at: string | null;
  updated_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface D1Env {
  DB: D1Database;
}

const COLS = `run_id, status, step, progress, title, slug, style, email,
              error, attempts, output_url, html_size, quality_score, cost_cny,
              started_at, updated_at, finished_at, created_at`;

/** INSERT 新 job. */
export async function createJob(
  db: D1Database,
  job: Pick<SynthJob, "run_id" | "title" | "slug" | "email" | "style">,
): Promise<void> {
  const now = new Date().toISOString();
  await db
    .prepare(
      `INSERT INTO synth_jobs (run_id, title, slug, style, email, status, step, progress, attempts, created_at, updated_at)
       VALUES (?1, ?2, ?3, ?4, ?5, 'queued', 'init', 0.0, 0, ?6, ?6)`,
    )
    .bind(job.run_id, job.title, job.slug, job.style ?? null, job.email ?? null, now)
    .run();
}

/** 读 1 个 job. */
export async function getJob(
  db: D1Database,
  runId: string,
): Promise<SynthJob | null> {
  const row = await db
    .prepare(`SELECT ${COLS} FROM synth_jobs WHERE run_id = ?1`)
    .bind(runId)
    .first<SynthJob>();
  return row ?? null;
}

/** 按 slug 查最近 1 个 done 的 job (前端 by-slug fallback 用). */
export async function getJobBySlug(
  db: D1Database,
  slug: string,
): Promise<SynthJob | null> {
  const row = await db
    .prepare(
      `SELECT ${COLS} FROM synth_jobs WHERE slug = ?1 AND status = 'done' ORDER BY finished_at DESC LIMIT 1`,
    )
    .bind(slug)
    .first<SynthJob>();
  return row ?? null;
}

/** 原子抢占: status='queued' AND attempts<3 → 'running', attempts+1, started_at=now. 返回行数. */
export async function claimNext(
  db: D1Database,
): Promise<SynthJob | null> {
  // SQLite 单实例 OK, D1 也会串行化
  const picked = await db
    .prepare(
      `SELECT ${COLS} FROM synth_jobs
       WHERE status = 'queued' AND attempts < 3
       ORDER BY created_at ASC LIMIT 1`,
    )
    .first<SynthJob>();
  if (!picked) return null;
  const now = new Date().toISOString();
  const res = await db
    .prepare(
      `UPDATE synth_jobs
       SET status = 'running', attempts = attempts + 1, started_at = COALESCE(started_at, ?2), updated_at = ?2
       WHERE run_id = ?1 AND status = 'queued'`,
    )
    .bind(picked.run_id, now)
    .run();
  if (!res.meta || res.meta.changes === 0) {
    // 已被其他 worker 抢走
    return null;
  }
  return { ...picked, status: "running", attempts: picked.attempts + 1, started_at: picked.started_at ?? now, updated_at: now };
}

/** 状态/进度更新 (worker 跑过程调用). */
export async function updateJob(
  db: D1Database,
  runId: string,
  patch: Partial<Pick<SynthJob, "status" | "step" | "progress" | "error" | "output_url" | "html_size" | "quality_score" | "cost_cny" | "finished_at">>,
): Promise<void> {
  const fields: string[] = [];
  const values: unknown[] = [];
  let i = 1;
  for (const [k, v] of Object.entries(patch)) {
    fields.push(`${k} = ?${i++}`);
    values.push(v);
  }
  fields.push(`updated_at = ?${i++}`);
  values.push(new Date().toISOString());
  values.push(runId);
  await db
    .prepare(`UPDATE synth_jobs SET ${fields.join(", ")} WHERE run_id = ?${i}`)
    .bind(...values)
    .run();
}

/** 列出最近 N 个 job (debug 用). */
export async function listRecent(db: D1Database, limit = 20): Promise<SynthJob[]> {
  const { results } = await db
    .prepare(`SELECT ${COLS} FROM synth_jobs ORDER BY created_at DESC LIMIT ?1`)
    .bind(limit)
    .all<SynthJob>();
  return results ?? [];
}
