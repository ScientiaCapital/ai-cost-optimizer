import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}

// Types for Supabase tables
export interface Request {
  id: string
  user_id: string
  prompt_hash: string
  prompt_text: string
  provider: string
  model: string
  tokens_used: number
  cost_cents: number
  response_time_ms: number
  created_at: string
}

export interface RoutingMetric {
  id: string
  user_id: string
  prompt_complexity: number
  selected_provider: string
  confidence_score: number
  was_correct: boolean | null
  feedback_rating: number | null
  created_at: string
}

export interface CacheEntry {
  id: string
  user_id: string
  prompt_embedding: number[]
  prompt_hash: string
  response_text: string
  provider: string
  quality_score: number
  hit_count: number
  created_at: string
}
