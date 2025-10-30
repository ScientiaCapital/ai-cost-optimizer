import type { NextRequest } from 'next/server'
import { cerebrasChat, cerebrasChatStream } from '@/lib/cerebras/client'
import type { ChatMessage } from '@/lib/openrouter/types'

export const runtime = 'nodejs'

export async function POST(req: NextRequest) {
  const { messages, stream = true, model } = await req.json()
  if (!Array.isArray(messages)) return new Response('Invalid messages', { status: 400 })

  const msgs: ChatMessage[] = messages

  if (stream) {
    try {
      const body = await cerebrasChatStream(msgs, {
        stream: true,
        temperature: 0.3,
        model,
      })
      return new Response(body, { headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-store' } })
    } catch (e: any) {
      return new Response(e?.message || 'Upstream error', { status: 502 })
    }
  }

  try {
    const json = await cerebrasChat(msgs, {
      temperature: 0.3,
      model,
      stream: false,
    })
    return Response.json(json)
  } catch (e: any) {
    return new Response(e?.message || 'Upstream error', { status: 502 })
  }
}


