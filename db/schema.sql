create table if not exists keywords (
  id text primary key,
  keyword text not null,
  target_entity text not null check (target_entity in ('bni_sekuritas','bions')),
  platform text not null,
  is_active boolean default true,
  created_at timestamp default current_timestamp
);

create table if not exists collection_runs (
  id text primary key,
  platform text not null,
  keyword_id text references keywords(id),
  status text not null,
  started_at timestamp default current_timestamp,
  finished_at timestamp,
  error_message text
);

create table if not exists raw_social_items (
  id text primary key,
  run_id text references collection_runs(id),
  platform text not null,
  source_type text not null,
  source_id text not null,
  parent_source_id text,
  conversation_id text,
  keyword_id text references keywords(id),
  target_entity text not null,
  author_id text,
  author_username text,
  author_display_name text,
  text text not null,
  language text,
  source_url text,
  posted_at timestamp,
  collected_at timestamp default current_timestamp,
  metrics text default '{}',
  raw_payload text not null,
  content_hash text not null,
  unique(platform, source_id)
);

create table if not exists processed_comments (
  id text primary key,
  raw_item_id text references raw_social_items(id),
  cleaned_text text not null,
  normalized_text text not null,
  is_spam boolean default false,
  spam_reason text,
  processed_at timestamp default current_timestamp
);

create table if not exists sentiment_results (
  id text primary key,
  processed_comment_id text references processed_comments(id),
  label text not null check (label in ('positive','neutral','negative')),
  score real not null check (score >= -1 and score <= 1),
  confidence real not null check (confidence >= 0 and confidence <= 1),
  method text not null,
  model_version text,
  topics text default '[]',
  explanation text,
  analyzed_at timestamp default current_timestamp
);
