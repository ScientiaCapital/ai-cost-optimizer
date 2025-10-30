import type { NextRequest } from 'next/server'

const OLLAMA_HOST = process.env.OLLAMA_HOST ?? 'http://localhost:11434'
const OLLAMA_API_KEY = process.env.OLLAMA_API_KEY
const EMBEDDING_MODEL = process.env.OLLAMA_EMBEDDINGS_MODEL ?? 'nomic-embed-text'

export const runtime = 'nodejs'

// Simple in-memory store (per server instance). Replace with a DB/vector store for production.
const memoryStore: { id: string; text: string; embedding: number[] }[] = []

export async function POST(req: NextRequest) {
  const { action, id, text, query } = await req.json()

  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (OLLAMA_API_KEY && OLLAMA_HOST.includes('ollama.com')) {
    headers['Authorization'] = `Bearer ${OLLAMA_API_KEY}`
  }

  const embed = async (input: string) => {
    const res = await fetch(`${OLLAMA_HOST}/api/embeddings`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ model: EMBEDDING_MODEL, input }),
    })
    if (!res.ok) throw new Error('Embedding failed')
    const data = await res.json()
    return data?.embedding as number[]
  }

  if (action === 'index') {
    if (!id || !text) return new Response('Missing id/text', { status: 400 })
    const embedding = await embed(text)
    const existingIdx = memoryStore.findIndex((d) => d.id === id)
    if (existingIdx >= 0) memoryStore.splice(existingIdx, 1)
    memoryStore.push({ id, text, embedding })
    return Response.json({ ok: true })
  }

  if (action === 'search') {
    if (!query) return new Response('Missing query', { status: 400 })
    const q = await embed(query)
    const sim = (a: number[], b: number[]) => {
      let dot = 0, na = 0, nb = 0
      for (let i = 0; i < a.length; i++) { dot += a[i] * b[i]; na += a[i] * a[i]; nb += b[i] * b[i] }
      const denom = Math.sqrt(na) * Math.sqrt(nb)
      return denom === 0 ? 0 : dot / denom
    }
    const ranked = memoryStore
      .map((d) => ({ ...d, score: sim(q, d.embedding) }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 5)
    return Response.json({ results: ranked })
  }

  return new Response('Invalid action', { status: 400 })
}
