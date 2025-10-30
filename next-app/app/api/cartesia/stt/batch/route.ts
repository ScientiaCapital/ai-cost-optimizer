import type { NextRequest } from 'next/server'
import { sttBatch } from '@/lib/cartesia/client'

export const runtime = 'nodejs'

export async function POST(req: NextRequest) {
  const form = await req.formData().catch(() => null)
  if (!form) return new Response('Expected multipart/form-data', { status: 400 })
  const file = form.get('file')
  if (!(file instanceof Blob)) return new Response('Missing file', { status: 400 })

  try {
    const result = await sttBatch(file)
    return Response.json(result)
  } catch (e: any) {
    return new Response(e?.message || 'Upstream error', { status: 502 })
  }
}
