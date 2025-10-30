import type { NextRequest } from 'next/server'
import { ttsBytes } from '@/lib/cartesia/client'

export const runtime = 'nodejs'

export async function POST(req: NextRequest) {
  const { transcript, model_id, voice, output_format } = await req.json()
  if (!transcript || !voice || !output_format) return new Response('Missing transcript/voice/output_format', { status: 400 })

  try {
    const audio = await ttsBytes({ transcript, model_id, voice, output_format })
    const ext = output_format.container === 'mp3' ? 'mp3' : 'wav'
    return new Response(audio, {
      headers: {
        'Content-Type': output_format.container === 'mp3' ? 'audio/mpeg' : 'audio/wav',
        'Content-Disposition': `attachment; filename="tts.${ext}"`,
        'Cache-Control': 'no-store',
      },
    })
  } catch (e: any) {
    return new Response(e?.message || 'Upstream error', { status: 502 })
  }
}
