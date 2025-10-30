import type { NextRequest } from 'next/server'
import { ttsSSEStream } from '@/lib/cartesia/client'

export const runtime = 'nodejs'

export async function POST(req: NextRequest) {
  const { transcript, model_id, voice, pcm_sample_rate } = await req.json()
  if (!transcript || !voice) return new Response('Missing transcript/voice', { status: 400 })

  try {
    const body = await ttsSSEStream({ transcript, model_id, voice, pcm_sample_rate })
    return new Response(body, { headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-store' } })
  } catch (e: any) {
    return new Response(e?.message || 'Upstream error', { status: 502 })
  }
}
