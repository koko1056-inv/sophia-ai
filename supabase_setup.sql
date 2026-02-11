-- ===================================
-- ソフィアAIチャットボット Supabase セットアップ
-- Supabase SQL Editor で実行してください
-- ===================================

-- 1. pgvector 拡張を有効化
create extension if not exists vector with schema extensions;

-- 2. ドキュメント（ナレッジ）テーブル
create table if not exists documents (
  id bigserial primary key,
  content text not null,
  source text default '',
  embedding vector(768),  -- Gemini text-embedding-004 は 768 次元
  created_at timestamptz default now()
);

-- 3. FAQ テーブル
create table if not exists faq (
  id bigserial primary key,
  question text not null,
  answer text not null,
  created_at timestamptz default now()
);

-- 4. ベクトル類似度検索関数
create or replace function match_documents(
  query_embedding vector(768),
  match_count int default 3
)
returns table (
  id bigint,
  content text,
  source text,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    d.id,
    d.content,
    d.source,
    1 - (d.embedding <=> query_embedding) as similarity
  from documents d
  order by d.embedding <=> query_embedding
  limit match_count;
end;
$$;

-- 5. (任意) サンプルFAQデータ
insert into faq (question, answer) values
  ('営業時間を教えてください', '営業時間は平日9:00〜18:00です。土日祝日はお休みをいただいております。'),
  ('お問い合わせ方法は？', 'お電話（03-XXXX-XXXX）またはメール（info@sophia-example.co.jp）にてお問い合わせいただけます。'),
  ('サービスの料金体系は？', 'サービスの料金はプランによって異なります。詳しくは営業担当までお問い合わせください。'),
  ('会社の所在地は？', '東京都に本社がございます。詳しい住所はお問い合わせください。');
