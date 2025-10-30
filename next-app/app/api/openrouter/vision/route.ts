import type { NextRequest } from 'next/server'
import { callVision } from '@/lib/openrouter/multimodal'

export const runtime = 'nodejs'

export async function POST(req: NextRequest) {
  const { prompt, imageUrl } = await req.json()
  if (!prompt || !imageUrl) return new Response('Missing prompt/imageUrl', { status: 400 })

  try {
    const res = await callVision(prompt, imageUrl, {
      model: 'openai/gpt-4o',
      temperature: 0.2,
      stream: false,
    })
    return Response.json(res)
  } catch (e: any) {
    return new Response(e?.message || 'Upstream error', { status: 502 })
  }
}
