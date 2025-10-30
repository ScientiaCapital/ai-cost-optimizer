import type { NextRequest } from 'next/server'
import { issueAccessToken } from '@/lib/cartesia/client'

export const runtime = 'nodejs'

export async function POST(req: NextRequest) {
  const { grants, ttlSeconds } = await req.json().catch(() => ({}))
  if (!Array.isArray(grants) || grants.length === 0) return new Response('Missing grants', { status: 400 })
  try {
    const token = await issueAccessToken({ grants, ttlSeconds })
    return Response.json(token)
  } catch (e: any) {
    return new Response(e?.message || 'Token issuance failed', { status: 500 })
  }
}
