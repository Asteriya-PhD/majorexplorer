-- migrations/0001_init.sql — synth_jobs 队列表
-- 适用: Cloudflare D1 (SQLite 兼容)
-- 跑法:  wrangler d1 execute <db-name> --file=./migrations/0001_init.sql

CREATE TABLE IF NOT EXISTS synth_jobs (
  run_id        TEXT PRIMARY KEY,
  status        TEXT NOT NULL DEFAULT 'queued',  -- queued|running|done|failed|dead
  step          TEXT NOT NULL DEFAULT 'init',    -- init|validate|search|route_style|synthesize|render|manifest|complete
  progress      REAL NOT NULL DEFAULT 0.0,        -- 0.0 - 1.0
  title         TEXT NOT NULL,
  slug          TEXT NOT NULL,
  style         TEXT,                              -- cs/eng/medicine/.../gongan/business
  email         TEXT,                              -- 通知邮箱 (可选)
  error         TEXT,                              -- 失败原因
  attempts      INTEGER NOT NULL DEFAULT 0,        -- 跑过几次
  output_url    TEXT,                              -- done 时填, e.g. "/translation.html"
  html_size     INTEGER,                           -- 字节数
  quality_score REAL,                              -- 0-1
  cost_cny      REAL,                              -- 累计成本
  started_at    TEXT,                              -- 第一次 pickup
  updated_at    TEXT,                              -- 最近一次状态变更
  finished_at   TEXT,                              -- done/failed 时间
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- GH Action 拉取用: status='queued' AND attempts < 3, 按 created_at 升序
CREATE INDEX IF NOT EXISTS idx_queued ON synth_jobs(status, attempts, created_at);

-- 前端 status 查询: run_id 已知, 走 PK
-- 前端 by-slug 查询 (前端静态 fallback): slug + status='done'
CREATE INDEX IF NOT EXISTS idx_slug_done ON synth_jobs(slug, status);
