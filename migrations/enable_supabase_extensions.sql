-- Enable Supabase Extensions for AI Cost Optimizer
-- Run this in Supabase SQL Editor or via: psql $DATABASE_URL -f migrations/enable_supabase_extensions.sql

-- ============================================================================
-- PGVECTOR EXTENSION (for semantic caching with embeddings)
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- PG_TRGM EXTENSION (for text similarity and fuzzy matching)
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================================
-- UUID-OSSP EXTENSION (for generating UUIDs)
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- VERIFY EXTENSIONS
-- ============================================================================
SELECT
    extname AS extension_name,
    extversion AS version,
    CASE
        WHEN extname = 'vector' THEN 'Enables pgvector for semantic search with embeddings'
        WHEN extname = 'pg_trgm' THEN 'Enables text similarity and fuzzy matching'
        WHEN extname = 'uuid-ossp' THEN 'Enables UUID generation functions'
        ELSE 'Other extension'
    END AS description
FROM pg_extension
WHERE extname IN ('vector', 'pg_trgm', 'uuid-ossp')
ORDER BY extname;

-- Expected output: 3 rows showing all extensions are enabled
