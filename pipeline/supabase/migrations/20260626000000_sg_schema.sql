-- sg_skills: default (user_id IS NULL) and user-owned skills
create table sg_skills (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  name text not null,
  description text not null default '',
  ai_prompt text not null,
  integration_actions jsonb not null default '[]',
  is_default boolean not null default false,
  created_at timestamptz not null default now()
);

-- sg_modes: user-owned ordered bundles of skills
create table sg_modes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  skill_ids uuid[] not null default '{}',
  created_at timestamptz not null default now()
);

-- sg_jobs: one row per pipeline run
create table sg_jobs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  mode_id uuid references sg_modes(id),
  drive_file_id text not null,
  status text not null default 'submitted',
  plan_json jsonb,
  checkpoint_json jsonb,
  error text,
  created_at timestamptz not null default now()
);

-- sg_speakers: detected speakers per job, confirmed by user at checkpoint
create table sg_speakers (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null references sg_jobs(id) on delete cascade,
  label text not null,
  confirmed_name text,
  talk_time_pct float,
  created_at timestamptz not null default now()
);

-- sg_utterances: one row per Whisper segment, merged with diarization
create table sg_utterances (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null references sg_jobs(id) on delete cascade,
  start_sec float not null,
  end_sec float not null,
  text text not null,
  speaker_id uuid references sg_speakers(id),
  confirmed_by_user boolean not null default false,
  avg_logprob float,
  created_at timestamptz not null default now()
);

-- sg_transcript_raw: full Whisper + pyannote output for debugging
create table sg_transcript_raw (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null references sg_jobs(id) on delete cascade,
  whisper_json jsonb,
  diarize_json jsonb,
  created_at timestamptz not null default now()
);

-- sg_skill_results: one row per skill per job
create table sg_skill_results (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null references sg_jobs(id) on delete cascade,
  skill_id uuid references sg_skills(id),
  skill_name text not null,
  output_json jsonb,
  output_markdown text,
  status text not null default 'pending',
  created_at timestamptz not null default now()
);

-- sg_action_logs: one row per integration action per job
create table sg_action_logs (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null references sg_jobs(id) on delete cascade,
  skill_id uuid references sg_skills(id),
  action_type text not null,
  destination text,
  payload_json jsonb,
  status text not null default 'pending',
  fired_at timestamptz,
  error text,
  created_at timestamptz not null default now()
);

-- Seed default skills
insert into sg_skills (name, description, ai_prompt, is_default) values
  ('Summary', 'Concise meeting summary', 'Summarize the transcript into a clear, concise paragraph covering the main topics discussed.', true),
  ('Action Items', 'Extract tasks and owners', 'Extract all action items from the transcript. For each item return: text (the task), owner (speaker name if mentioned, else null). Return as JSON array: [{"text":"...","owner":"..."}]', true),
  ('Decisions', 'Key decisions made', 'List all decisions made during the conversation. Return as a JSON array of strings: ["Decision 1","Decision 2"]', true),
  ('Sentiment', 'Speaker tone analysis', 'Analyse the tone of each speaker. Return JSON: {"Speaker A": "positive|neutral|negative", "Speaker B": "positive|neutral|negative"}', true);

-- Indexes on high-query FK columns
create index on sg_jobs (user_id);
create index on sg_speakers (job_id);
create index on sg_utterances (job_id);
create index on sg_utterances (speaker_id);
create index on sg_skill_results (job_id);
create index on sg_action_logs (job_id);
