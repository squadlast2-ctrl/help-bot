-- Запускать в Supabase SQL Editor
-- https://app.supabase.com → SQL Editor → New query

-- ─────────────────────────────────────
-- Таблица: записи помощи
-- ─────────────────────────────────────
create table if not exists help_entries (
  id            bigserial primary key,
  user_id       bigint        not null,
  username      text          default '',
  full_name     text          not null,
  text          text          default '',
  media_url     text,                        -- file_id из Telegram
  media_type    text,                        -- photo | video | video_note | voice | document
  is_closed     boolean       default false, -- закрыта ли запись (возврат привязан)
  created_at    timestamptz   default now()
);

create index if not exists help_entries_user_id_idx on help_entries(user_id);
create index if not exists help_entries_created_at_idx on help_entries(created_at desc);

-- ─────────────────────────────────────
-- Таблица: возвраты
-- ─────────────────────────────────────
create table if not exists return_entries (
  id             bigserial primary key,
  user_id        bigint        not null,
  username       text          default '',
  full_name      text          not null,
  text           text          default '',
  help_entry_id  bigint        references help_entries(id) on delete set null,
  media_url      text,
  media_type     text,
  created_at     timestamptz   default now()
);

create index if not exists return_entries_user_id_idx on return_entries(user_id);
create index if not exists return_entries_created_at_idx on return_entries(created_at desc);

-- ─────────────────────────────────────
-- Row Level Security — отключаем для сервисного ключа
-- (бот использует service_role key — видит всё)
-- ─────────────────────────────────────
alter table help_entries enable row level security;
alter table return_entries enable row level security;

-- Политика: сервисный ключ обходит RLS автоматически.
-- Если хочешь использовать anon key — раскомментируй:
-- create policy "allow all" on help_entries for all using (true);
-- create policy "allow all" on return_entries for all using (true);
