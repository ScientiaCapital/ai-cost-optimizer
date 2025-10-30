import type { NextRequest } from 'next/server'

export const runtime = 'nodejs'

// Returns connection details for clients to establish a direct streaming STT session with Cartesia.
// Clients should request an access token first, then connect to Cartesia's WS/SSE endpoints directly.
export async function POST(_req: NextRequest) {
  // In a production setup, you might configure region or features here.
  return Response.json({
    ws: {
      // Documented WS endpoint path varies; clients should use official docs.
      url: 'wss://api.cartesia.ai/stt/stream',
    },
    notes: 'Obtain a short-lived access token from /api/cartesia/token and use it to authenticate the WebSocket connection per Cartesia docs.',
  })
}
