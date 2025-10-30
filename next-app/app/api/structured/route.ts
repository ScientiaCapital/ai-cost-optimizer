import { z } from 'zod'
import type { NextRequest } from 'next/server'

const DEFAULT_MODEL = process.env.OLLAMA_MODEL ?? 'gpt-oss'
const OLLAMA_HOST = process.env.OLLAMA_HOST ?? 'http://localhost:11434'
const OLLAMA_API_KEY = process.env.OLLAMA_API_KEY

export const runtime = 'nodejs'

const CountrySchema = z.object({
  name: z.string(),
  capital: z.string(),
  languages: z.array(z.string()).min(1),
})

export async function POST(req: NextRequest) {
  const { topic } = await req.json()
  if (!topic || typeof topic !== 'string') {
    return new Response('Invalid topic', { status: 400 })
  }

  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (OLLAMA_API_KEY && OLLAMA_HOST.includes('ollama.com')) {
    headers['Authorization'] = `Bearer ${OLLAMA_API_KEY}`
  }

  const upstream = await fetch(`${OLLAMA_HOST}/api/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      model: DEFAULT_MODEL,
      stream: false,
      messages: [
        { role: 'system', content: 'Respond ONLY with JSON matching the provided schema.' },
        { role: 'user', content: `Return details for: ${topic}` },
      ],
      format: CountrySchema.toJSON(),
      options: { temperature: 0.2 },
    }),
  })

  if (!upstream.ok) {
    const text = await upstream.text().catch(() => '')
    return new Response(text || 'Upstream error', { status: upstream.status || 502 })
  }

  const data = await upstream.json()
  // Some Ollama servers return { message: { content } } others return content directly in 'response'
  const raw = data?.message?.content ?? data?.response
  try {
    const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
    const result = CountrySchema.parse(parsed)
    return Response.json(result)
  } catch (err) {
    return new Response('Schema validation failed', { status: 422 })
  }
}
