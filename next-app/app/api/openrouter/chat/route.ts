import type { NextRequest } from 'next/server'
import { openrouterChatStream } from '@/lib/openrouter/client'
import { SYSTEM_BASE, ROUTING_FAST_CHEAP, PROVIDER_LOW_LATENCY } from '@/lib/openrouter/presets'
import type { ChatMessage } from '@/lib/openrouter/types'

export const runtime = 'nodejs'

export async function POST(req: NextRequest) {
  const { messages, stream = true } = await req.json()
  if (!Array.isArray(messages)) return new Response('Invalid messages', { status: 400 })

  const msgs: ChatMessage[] = [SYSTEM_BASE, ...messages]

  if (stream) {
    try {
      const body = await openrouterChatStream(msgs, {
        stream: true,
        temperature: 0.3,
        ...ROUTING_FAST_CHEAP,
        ...PROVIDER_LOW_LATENCY,
      })
      return new Response(body, { headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-store' } })
    } catch (e: any) {
      return new Response(e?.message || 'Upstream error', { status: 502 })
    }
  }

  try {
    const json = await openrouterChat(msgs, {
      temperature: 0.3,
      ...ROUTING_FAST_CHEAP,
      ...PROVIDER_LOW_LATENCY,
      stream: false,
    })
    return Response.json(json)
  } catch (e: any) {
    return new Response(e?.message || 'Upstream error', { status: 502 })
  }
}
