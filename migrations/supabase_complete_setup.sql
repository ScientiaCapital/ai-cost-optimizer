-- ============================================================================
-- SUPABASE COMPLETE SETUP for AI Cost Optimizer
-- ============================================================================
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard/project/nhjhzzkcqtsmfgvairos/sql
--
-- This script:
-- 1. Enables required extensions (pgvector, pg_trgm, uuid-ossp)
-- 2. Verifies extensions are installed
-- 3. Adds user_id columns for multi-tenancy
-- 4. Adds embedding column for semantic caching
-- 5. Creates indexes for performance
-- 6. Enables Row-Level Security (RLS)
-- 7. Creates RLS policies for user isolation
-- 8. Creates pgvector semantic search function
-- ============================================================================

-- ============================================================================
-- PART 1: ENABLE EXTENSIONS
-- ============================================================================

-- pgvector: Enables semantic search with embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- pg_trgm: Enables text similarity and fuzzy matching
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- uuid-ossp: Enables UUID generation functions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Verify extensions are enabled
SELECT
    extname AS extension_name,
    extversion AS version,
    CASE
        WHEN extname = 'vector' THEN '✅ Semantic search enabled'
        WHEN extname = 'pg_trgm' THEN '✅ Text similarity enabled'
        WHEN extname = 'uuid-ossp' THEN '✅ UUID generation enabled'
        ELSE 'Other extension'
    END AS status
FROM pg_extension
WHERE extname IN ('vector', 'pg_trgm', 'uuid-ossp')
ORDER BY extname;

-- ============================================================================
-- PART 2: SCHEMA EXTENSIONS (Add user_id and embedding columns)
-- ============================================================================

-- NOTE: These ALTER TABLE commands will only work AFTER you run Alembic migrations
-- If tables don't exist yet, these will fail gracefully
-- Run Alembic migrations first, then run this script

-- Add user_id to requests table (for multi-tenant cost tracking)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'requests') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name = 'requests' AND column_name = 'user_id') THEN
            ALTER TABLE requests ADD COLUMN user_id UUID REFERENCES auth.users(id);
            RAISE NOTICE '✅ Added user_id to requests table';
        ELSE
            RAISE NOTICE 'ℹ️  user_id already exists in requests table';
        END IF;
    ELSE
        RAISE NOTICE '⚠️  requests table does not exist yet - run Alembic migrations first';
    END IF;
END $$;

-- Add user_id to response_cache table (for user-specific caching)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'response_cache') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name = 'response_cache' AND column_name = 'user_id') THEN
            ALTER TABLE response_cache ADD COLUMN user_id UUID REFERENCES auth.users(id);
            RAISE NOTICE '✅ Added user_id to response_cache table';
        ELSE
            RAISE NOTICE 'ℹ️  user_id already exists in response_cache table';
        END IF;
    ELSE
        RAISE NOTICE '⚠️  response_cache table does not exist yet - run Alembic migrations first';
    END IF;
END $$;

-- Add user_id to routing_metrics table (for analytics)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'routing_metrics') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name = 'routing_metrics' AND column_name = 'user_id') THEN
            ALTER TABLE routing_metrics ADD COLUMN user_id UUID REFERENCES auth.users(id);
            RAISE NOTICE '✅ Added user_id to routing_metrics table';
        ELSE
            RAISE NOTICE 'ℹ️  user_id already exists in routing_metrics table';
        END IF;
    ELSE
        RAISE NOTICE '⚠️  routing_metrics table does not exist yet - run Alembic migrations first';
    END IF;
END $$;

-- Add embedding column to response_cache for semantic search
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'response_cache') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name = 'response_cache' AND column_name = 'embedding') THEN
            -- Using 384 dimensions for sentence-transformers/all-MiniLM-L6-v2
            -- Change to vector(1536) if using OpenAI text-embedding-ada-002
            ALTER TABLE response_cache ADD COLUMN embedding vector(384);
            RAISE NOTICE '✅ Added embedding column to response_cache (384 dimensions for MiniLM)';
        ELSE
            RAISE NOTICE 'ℹ️  embedding column already exists in response_cache table';
        END IF;
    ELSE
        RAISE NOTICE '⚠️  response_cache table does not exist yet - run Alembic migrations first';
    END IF;
END $$;

-- ============================================================================
-- PART 3: CREATE INDEXES FOR PERFORMANCE
-- ============================================================================

-- pgvector index for fast semantic search (IVFFlat algorithm)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'response_cache') THEN
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'response_cache_embedding_idx') THEN
            CREATE INDEX response_cache_embedding_idx ON response_cache
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
            RAISE NOTICE '✅ Created pgvector index for semantic search';
        ELSE
            RAISE NOTICE 'ℹ️  pgvector index already exists';
        END IF;
    END IF;
END $$;

-- Index on user_id for fast user-scoped queries
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'requests') THEN
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'requests_user_id_idx') THEN
            CREATE INDEX requests_user_id_idx ON requests(user_id);
            RAISE NOTICE '✅ Created index on requests.user_id';
        END IF;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'response_cache') THEN
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'response_cache_user_id_idx') THEN
            CREATE INDEX response_cache_user_id_idx ON response_cache(user_id);
            RAISE NOTICE '✅ Created index on response_cache.user_id';
        END IF;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'routing_metrics') THEN
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'routing_metrics_user_id_idx') THEN
            CREATE INDEX routing_metrics_user_id_idx ON routing_metrics(user_id);
            RAISE NOTICE '✅ Created index on routing_metrics.user_id';
        END IF;
    END IF;
END $$;

-- ============================================================================
-- PART 4: ENABLE ROW-LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all tables for multi-tenant isolation
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'requests') THEN
        ALTER TABLE requests ENABLE ROW LEVEL SECURITY;
        RAISE NOTICE '✅ Enabled RLS on requests table';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'response_cache') THEN
        ALTER TABLE response_cache ENABLE ROW LEVEL SECURITY;
        RAISE NOTICE '✅ Enabled RLS on response_cache table';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'routing_metrics') THEN
        ALTER TABLE routing_metrics ENABLE ROW LEVEL SECURITY;
        RAISE NOTICE '✅ Enabled RLS on routing_metrics table';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'value_metrics') THEN
        ALTER TABLE value_metrics ENABLE ROW LEVEL SECURITY;
        RAISE NOTICE '✅ Enabled RLS on value_metrics table';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'experiments') THEN
        ALTER TABLE experiments ENABLE ROW LEVEL SECURITY;
        RAISE NOTICE '✅ Enabled RLS on experiments table';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'experiment_results') THEN
        ALTER TABLE experiment_results ENABLE ROW LEVEL SECURITY;
        RAISE NOTICE '✅ Enabled RLS on experiment_results table';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'routing_feedback') THEN
        ALTER TABLE routing_feedback ENABLE ROW LEVEL SECURITY;
        RAISE NOTICE '✅ Enabled RLS on routing_feedback table';
    END IF;
END $$;

-- ============================================================================
-- PART 5: CREATE RLS POLICIES (User-scoped access)
-- ============================================================================

-- DROP existing policies if they exist (idempotent)
DROP POLICY IF EXISTS "Users can view own requests" ON requests;
DROP POLICY IF EXISTS "Users can insert own requests" ON requests;
DROP POLICY IF EXISTS "Users can view own cache" ON response_cache;
DROP POLICY IF EXISTS "Users can insert own cache" ON response_cache;
DROP POLICY IF EXISTS "Users can update own cache" ON response_cache;
DROP POLICY IF EXISTS "Users can view own metrics" ON routing_metrics;
DROP POLICY IF EXISTS "Users can insert own metrics" ON routing_metrics;
DROP POLICY IF EXISTS "Users can view own value metrics" ON value_metrics;
DROP POLICY IF EXISTS "Users can insert own value metrics" ON value_metrics;
DROP POLICY IF EXISTS "Users can view own experiments" ON experiments;
DROP POLICY IF EXISTS "Users can insert own experiments" ON experiments;
DROP POLICY IF EXISTS "Users can view own experiment results" ON experiment_results;
DROP POLICY IF EXISTS "Users can insert own experiment results" ON experiment_results;
DROP POLICY IF EXISTS "Users can view own feedback" ON routing_feedback;
DROP POLICY IF EXISTS "Users can insert own feedback" ON routing_feedback;

-- Service role (bypass RLS for admin operations)
DROP POLICY IF EXISTS "Service role has full access" ON requests;
DROP POLICY IF EXISTS "Service role has full access" ON response_cache;
DROP POLICY IF EXISTS "Service role has full access" ON routing_metrics;

-- requests table policies
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'requests') THEN
        -- Users can view their own requests
        CREATE POLICY "Users can view own requests"
        ON requests FOR SELECT
        USING (auth.uid() = user_id);

        -- Users can insert their own requests
        CREATE POLICY "Users can insert own requests"
        ON requests FOR INSERT
        WITH CHECK (auth.uid() = user_id);

        -- Service role bypasses RLS (for migrations, admin ops)
        CREATE POLICY "Service role has full access"
        ON requests FOR ALL
        USING (auth.jwt() ->> 'role' = 'service_role');

        RAISE NOTICE '✅ Created RLS policies for requests table';
    END IF;
END $$;

-- response_cache table policies
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'response_cache') THEN
        CREATE POLICY "Users can view own cache"
        ON response_cache FOR SELECT
        USING (auth.uid() = user_id);

        CREATE POLICY "Users can insert own cache"
        ON response_cache FOR INSERT
        WITH CHECK (auth.uid() = user_id);

        CREATE POLICY "Users can update own cache"
        ON response_cache FOR UPDATE
        USING (auth.uid() = user_id);

        CREATE POLICY "Service role has full access"
        ON response_cache FOR ALL
        USING (auth.jwt() ->> 'role' = 'service_role');

        RAISE NOTICE '✅ Created RLS policies for response_cache table';
    END IF;
END $$;

-- routing_metrics table policies
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'routing_metrics') THEN
        CREATE POLICY "Users can view own metrics"
        ON routing_metrics FOR SELECT
        USING (auth.uid() = user_id);

        CREATE POLICY "Users can insert own metrics"
        ON routing_metrics FOR INSERT
        WITH CHECK (auth.uid() = user_id);

        CREATE POLICY "Service role has full access"
        ON routing_metrics FOR ALL
        USING (auth.jwt() ->> 'role' = 'service_role');

        RAISE NOTICE '✅ Created RLS policies for routing_metrics table';
    END IF;
END $$;

-- value_metrics table policies (already has user_id from Alembic)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'value_metrics') THEN
        CREATE POLICY "Users can view own value metrics"
        ON value_metrics FOR SELECT
        USING (auth.uid() = user_id::uuid);

        CREATE POLICY "Users can insert own value metrics"
        ON value_metrics FOR INSERT
        WITH CHECK (auth.uid() = user_id::uuid);

        RAISE NOTICE '✅ Created RLS policies for value_metrics table';
    END IF;
END $$;

-- experiments table policies
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'experiments') THEN
        CREATE POLICY "Users can view own experiments"
        ON experiments FOR SELECT
        USING (auth.uid()::text = created_by);

        CREATE POLICY "Users can insert own experiments"
        ON experiments FOR INSERT
        WITH CHECK (auth.uid()::text = created_by);

        RAISE NOTICE '✅ Created RLS policies for experiments table';
    END IF;
END $$;

-- experiment_results table policies (has user_id from Alembic)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'experiment_results') THEN
        CREATE POLICY "Users can view own experiment results"
        ON experiment_results FOR SELECT
        USING (auth.uid()::text = user_id);

        CREATE POLICY "Users can insert own experiment results"
        ON experiment_results FOR INSERT
        WITH CHECK (auth.uid()::text = user_id);

        RAISE NOTICE '✅ Created RLS policies for experiment_results table';
    END IF;
END $$;

-- routing_feedback table policies (already has user_id from Alembic)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'routing_feedback') THEN
        CREATE POLICY "Users can view own feedback"
        ON routing_feedback FOR SELECT
        USING (auth.uid()::text = user_id);

        CREATE POLICY "Users can insert own feedback"
        ON routing_feedback FOR INSERT
        WITH CHECK (auth.uid()::text = user_id);

        RAISE NOTICE '✅ Created RLS policies for routing_feedback table';
    END IF;
END $$;

-- ============================================================================
-- PART 6: PGVECTOR SEMANTIC SEARCH FUNCTION
-- ============================================================================

-- Function to find semantically similar cached responses
-- Uses cosine similarity with pgvector
CREATE OR REPLACE FUNCTION match_cache_entries(
    query_embedding vector(384),      -- Embedding of the search query
    match_threshold float DEFAULT 0.95, -- Similarity threshold (0.0-1.0)
    match_count int DEFAULT 1,          -- Number of results to return
    target_user_id uuid DEFAULT NULL    -- Filter by user_id (for RLS)
)
RETURNS TABLE (
    cache_key text,
    prompt_normalized text,
    response text,
    provider text,
    model text,
    similarity float,
    hit_count int,
    quality_score float
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT
        rc.cache_key,
        rc.prompt_normalized,
        rc.response,
        rc.provider,
        rc.model,
        -- Cosine similarity: 1 - distance (higher is better)
        (1 - (rc.embedding <=> query_embedding))::float as similarity,
        rc.hit_count,
        rc.quality_score
    FROM response_cache rc
    WHERE
        -- Only return non-invalidated entries
        (rc.invalidated IS NULL OR rc.invalidated = 0)
        -- Filter by user if specified (RLS enforcement)
        AND (target_user_id IS NULL OR rc.user_id = target_user_id)
        -- Only return entries above similarity threshold
        AND (1 - (rc.embedding <=> query_embedding)) > match_threshold
    ORDER BY
        -- Sort by similarity (best matches first)
        rc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION match_cache_entries TO authenticated;
GRANT EXECUTE ON FUNCTION match_cache_entries TO service_role;

-- ============================================================================
-- PART 7: HELPER FUNCTION - Get User's Cache Stats
-- ============================================================================

CREATE OR REPLACE FUNCTION get_user_cache_stats(target_user_id uuid)
RETURNS TABLE (
    total_entries bigint,
    total_hits bigint,
    avg_quality_score float,
    cache_size_bytes bigint
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::bigint as total_entries,
        COALESCE(SUM(hit_count), 0)::bigint as total_hits,
        COALESCE(AVG(quality_score), 0.0)::float as avg_quality_score,
        COALESCE(SUM(LENGTH(response)), 0)::bigint as cache_size_bytes
    FROM response_cache
    WHERE user_id = target_user_id
        AND (invalidated IS NULL OR invalidated = 0);
END;
$$;

GRANT EXECUTE ON FUNCTION get_user_cache_stats TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_cache_stats TO service_role;

-- ============================================================================
-- VERIFICATION & SUMMARY
-- ============================================================================

-- Show enabled extensions
SELECT '📊 EXTENSIONS ENABLED:' as section;
SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector', 'pg_trgm', 'uuid-ossp');

-- Show RLS status
SELECT '🔒 ROW-LEVEL SECURITY STATUS:' as section;
SELECT
    schemaname,
    tablename,
    CASE WHEN rowsecurity THEN '✅ Enabled' ELSE '❌ Disabled' END as rls_status
FROM pg_tables
WHERE schemaname = 'public'
    AND tablename IN ('requests', 'response_cache', 'routing_metrics',
                      'value_metrics', 'experiments', 'experiment_results', 'routing_feedback')
ORDER BY tablename;

-- Show created functions
SELECT '⚙️  CUSTOM FUNCTIONS:' as section;
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
    AND routine_name IN ('match_cache_entries', 'get_user_cache_stats')
ORDER BY routine_name;

-- Final message
SELECT '✅ SUPABASE SETUP COMPLETE!' as status,
       'Next step: Run Alembic migrations to create tables' as next_action;
