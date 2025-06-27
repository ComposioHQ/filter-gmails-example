# Supabase Database Setup

This guide walks through setting up the required database tables and Row Level Security (RLS) policies for the Gmail Reaper application.

## Prerequisites

1. Create a new Supabase project at [supabase.com](https://supabase.com)
2. Navigate to the SQL Editor in your Supabase dashboard

## Database Tables

### 1. Connections Table

Stores Gmail connection information for each user.

```sql
CREATE TABLE public.connections (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  user_id uuid NOT NULL,
  connected_account_id text NOT NULL,
  connection_status text NOT NULL,
  CONSTRAINT connections_pkey PRIMARY KEY (id),
  CONSTRAINT connections_user_id_fkey FOREIGN KEY (user_id) 
    REFERENCES auth.users (id) ON DELETE CASCADE
) TABLESPACE pg_default;

-- Index for faster user lookups
CREATE INDEX IF NOT EXISTS idx_connections_user_id 
  ON public.connections USING btree (user_id) TABLESPACE pg_default;
```

### 2. Prompts Table

Stores user-defined prompts for email categorization.

```sql
CREATE TABLE public.prompts (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NULL,
  prompt text NOT NULL,
  created_at timestamp with time zone NULL DEFAULT now(),
  updated_at timestamp with time zone NULL DEFAULT now(),
  CONSTRAINT prompts_pkey PRIMARY KEY (id),
  CONSTRAINT prompts_user_id_fkey FOREIGN KEY (user_id) 
    REFERENCES auth.users (id) ON DELETE CASCADE
) TABLESPACE pg_default;

-- Index for faster user lookups
CREATE INDEX IF NOT EXISTS idx_prompts_user_id 
  ON public.prompts USING btree (user_id) TABLESPACE pg_default;
```

## Row Level Security (RLS)

Enable RLS on both tables to ensure users can only access their own data.

### Enable RLS

```sql
-- Enable RLS on both tables
ALTER TABLE public.connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.prompts ENABLE ROW LEVEL SECURITY;
```

### RLS Policies for Connections Table

```sql
-- Users can view their own connections
CREATE POLICY "Users can select their own connections" 
  ON connections FOR SELECT TO authenticated 
  USING ((SELECT auth.uid()) = user_id);

-- Users can create their own connections
CREATE POLICY "Users can insert their own connections" 
  ON connections FOR INSERT TO authenticated 
  WITH CHECK ((SELECT auth.uid()) = user_id);

-- Users can update their own connections
CREATE POLICY "Users can update their own connections" 
  ON connections FOR UPDATE TO authenticated 
  USING ((SELECT auth.uid()) = user_id) 
  WITH CHECK ((SELECT auth.uid()) = user_id);

-- Users can delete their own connections
CREATE POLICY "Users can delete their own connections" 
  ON connections FOR DELETE TO authenticated 
  USING ((SELECT auth.uid()) = user_id);
```

### RLS Policies for Prompts Table

```sql
-- Users can manage their own prompts (all operations)
CREATE POLICY "Users can manage own prompts" 
  ON prompts FOR ALL TO public 
  USING (auth.uid() = user_id);
```

## Quick Setup Script

Run this complete script in your Supabase SQL Editor to set up everything at once:

```sql
-- Create connections table
CREATE TABLE public.connections (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  user_id uuid NOT NULL,
  connected_account_id text NOT NULL,
  connection_status text NOT NULL,
  CONSTRAINT connections_pkey PRIMARY KEY (id),
  CONSTRAINT connections_user_id_fkey FOREIGN KEY (user_id) 
    REFERENCES auth.users (id) ON DELETE CASCADE
) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_connections_user_id 
  ON public.connections USING btree (user_id) TABLESPACE pg_default;

-- Create prompts table
CREATE TABLE public.prompts (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NULL,
  prompt text NOT NULL,
  created_at timestamp with time zone NULL DEFAULT now(),
  updated_at timestamp with time zone NULL DEFAULT now(),
  CONSTRAINT prompts_pkey PRIMARY KEY (id),
  CONSTRAINT prompts_user_id_fkey FOREIGN KEY (user_id) 
    REFERENCES auth.users (id) ON DELETE CASCADE
) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_prompts_user_id 
  ON public.prompts USING btree (user_id) TABLESPACE pg_default;

-- Enable RLS
ALTER TABLE public.connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.prompts ENABLE ROW LEVEL SECURITY;

-- RLS policies for connections
CREATE POLICY "Users can select their own connections" 
  ON connections FOR SELECT TO authenticated 
  USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can insert their own connections" 
  ON connections FOR INSERT TO authenticated 
  WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update their own connections" 
  ON connections FOR UPDATE TO authenticated 
  USING ((SELECT auth.uid()) = user_id) 
  WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can delete their own connections" 
  ON connections FOR DELETE TO authenticated 
  USING ((SELECT auth.uid()) = user_id);

-- RLS policy for prompts
CREATE POLICY "Users can manage own prompts" 
  ON prompts FOR ALL TO public 
  USING (auth.uid() = user_id);
```

## Verification

After running the setup, verify everything is working:

1. Check tables exist:
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('connections', 'prompts');
```

2. Check RLS is enabled:
```sql
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('connections', 'prompts');
```

3. Check policies are created:
```sql
SELECT schemaname, tablename, policyname 
FROM pg_policies 
WHERE schemaname = 'public' 
AND tablename IN ('connections', 'prompts');
```

## Important Notes

- The `user_id` field references Supabase Auth users
- All operations require authentication
- Users can only access their own data thanks to RLS
- The `connection_status` field stores Composio status values: INITIATED, ACTIVE, FAILED, EXPIRED, REVOKED
- The backend uses the service role key to bypass RLS when needed
- The frontend uses the anon key and relies on RLS for security