"use client"
import { useCallback, useRef, useState } from 'react'

export type ChatMessage = { role: 'user' | 'assistant'; content: string }

export const useStreamedChat = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  const handleSend = useCallback(async (input: string) => {
    if (!input.trim()) return
    setMessages((m) => [...m, { role: 'user', content: input }])
    setIsLoading(true)

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: [...messages, { role: 'user', content: input }], stream: true }),
        signal: controller.signal,
      })
      if (!res.ok || !res.body) throw new Error('Network error')

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let assistant = ''
      setMessages((m) => [...m, { role: 'assistant', content: '' }])

      for (;;) {
        const { value, done } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        // Expect NDJSON lines; try to parse each
        const lines = chunk.split('\n').filter(Boolean)
        for (const line of lines) {
          try {
            const obj = JSON.parse(line)
            const text = obj?.message?.content ?? obj?.response ?? ''
            if (text) {
              assistant += text
              setMessages((m) => {
                const copy = [...m]
                const last = copy[copy.length - 1]
                if (last && last.role === 'assistant') {
                  copy[copy.length - 1] = { ...last, content: assistant }
                }
                return copy
              })
            }
          } catch {
            // ignore partial lines
          }
        }
      }
    } catch {
      // swallow for demo; surface in UI if needed
    } finally {
      setIsLoading(false)
      abortRef.current = null
    }
  }, [messages])

  const handleAbort = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  return { messages, isLoading, handleSend, handleAbort }
}
