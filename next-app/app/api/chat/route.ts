import type { NextRequest } from 'next/server'

const DEFAULT_MODEL = process.env.OLLAMA_MODEL ?? 'qwen3'
const OLLAMA_HOST = process.env.OLLAMA_HOST ?? 'http://localhost:11434'
const OLLAMA_API_KEY = process.env.OLLAMA_API_KEY

export const runtime = 'nodejs'

export async function POST(req: NextRequest) {
  const { messages, stream = true, think } = await req.json()

  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (OLLAMA_API_KEY && OLLAMA_HOST.includes('ollama.com')) {
    headers['Authorization'] = `Bearer ${OLLAMA_API_KEY}`
  }

  const upstream = await fetch(`${OLLAMA_HOST}/api/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      model: DEFAULT_MODEL,
      messages,
      stream: true,
      ...(typeof think !== 'undefined' ? { think } : {}),
    }),
  })

  if (!upstream.ok || !upstream.body) {
    const text = await upstream.text().catch(() => '')
    return new Response(text || 'Upstream error', { status: upstream.status || 502 })
  }

  // Proxy streamed chunks verbatim
  return new Response(upstream.body, {
    headers: {
      'Content-Type': 'application/x-ndjson',
      'Cache-Control': 'no-store',
    },
  })
}
