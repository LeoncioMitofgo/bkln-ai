create extension if not exists vector;

create table if not exists sources (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  source_url text,
  content text not null,
  embedding vector(3072),
  created_at timestamptz not null default now()
);

create or replace function search_sources(query_embedding vector(3072), match_limit int default 6)
returns table (id uuid, title text, source_url text, content text, similarity real)
language sql stable
as $$
  select s.id, s.title, s.source_url, s.content,
    1 - (s.embedding <=> query_embedding) as similarity
  from sources s
  where s.embedding is not null
  order by s.embedding <=> query_embedding
  limit match_limit;
$$;

alter table sources enable row level security;
