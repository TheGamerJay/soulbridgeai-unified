-- SoulBridge Mini Studio Database Schema
-- Professional music production with real AI models

CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  plan TEXT DEFAULT 'trial',
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS credits (
  user_id TEXT PRIMARY KEY REFERENCES users(id),
  credits_remaining INT NOT NULL DEFAULT 60,
  last_refreshed TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS projects (
  id UUID PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  name TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS assets (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id),
  user_id TEXT NOT NULL REFERENCES users(id),
  kind TEXT NOT NULL CHECK (kind IN ('lyrics','beat','vocal','mix','midi')),
  path TEXT NOT NULL,
  mime TEXT NOT NULL,
  bytes BIGINT NOT NULL,
  origin TEXT NOT NULL CHECK (origin IN ('internal','external')),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vocal_jobs (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id),
  user_id TEXT NOT NULL REFERENCES users(id),
  lyrics_asset UUID REFERENCES assets(id),
  beat_asset UUID REFERENCES assets(id),
  midi_asset UUID REFERENCES assets(id),
  cost_credits INT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('queued','running','done','error')) DEFAULT 'queued',
  result_asset UUID REFERENCES assets(id),
  error TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_assets_project_id ON assets(project_id);
CREATE INDEX IF NOT EXISTS idx_assets_user_id ON assets(user_id);
CREATE INDEX IF NOT EXISTS idx_vocal_jobs_user_id ON vocal_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_vocal_jobs_status ON vocal_jobs(status);