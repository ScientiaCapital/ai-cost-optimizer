import type { NextRequest } from 'next/server'
import { z } from 'zod'
import { SYSTEM_BASE, ROUTING_FAST_CHEAP } from '@/lib/openrouter/presets'
import type { ChatMessage } from '@/lib/openrouter/types'
import { requestStructured } from '@/lib/openrouter/structured'

export const runtime = 'nodejs'

const CountrySchema = z.object({
  name: z.string(),
  capital: z.string(),
  languages: z.array(z.string()).min(1),
})

export async function POST(req: NextRequest) {
  const { topic } = await req.json()
  if (!topic || typeof topic !== 'string') return new Response('Invalid topic', { status: 400 })

  const messages: ChatMessage[] = [
    SYSTEM_BASE,
    { role: 'user', content: `Return details for: ${topic}` },
  ]

  const result = await requestStructured(messages, CountrySchema, {
    temperature: 0,
    ...ROUTING_FAST_CHEAP,
    maxRetries: 1,
  })

  if (!result.ok) return new Response(result.error, { status: 422 })
  return Response.json(result.data)
}
