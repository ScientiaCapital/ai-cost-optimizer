"use client"

import { useCallback, useMemo, useRef, useState } from 'react'
import { decodeNDJSONStream, type OllamaStreamChunk } from '@/lib/ndjson'

export type ChatMessage = { role: 'user' | 'assistant' | 'system'; content: string }

export const useStreamChat = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [hasError, setHasError] = useState<string | null>(null)

  const controllerRef = useRef<AbortController | null>(null)

  const handleReset = useCallback(() => {
    controllerRef.current?.abort()
    controllerRef.current = null
    setMessages([])
    setHasError(null)
    setIsLoading(false)
  }, [])

  const handleSend = useCallback(async (input: string) => {
    if (!input.trim()) return
    setHasError(null)
    setIsLoading(true)

    const userMsg: ChatMessage = { role: 'user', content: input }
    setMessages((prev) => [...prev, userMsg, { role: 'assistant', content: '' }])

    const controller = new AbortController()
    controllerRef.current = controller

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: [...messages, userMsg], stream: true, think: true }),
        signal: controller.signal,
      })
      if (!res.ok || !res.body) throw new Error('Request failed')

      await decodeNDJSONStream(res.body, (chunk: OllamaStreamChunk) => {
        const delta = chunk.message?.content || chunk.message?.thinking || ''
        if (!delta) return
        setMessages((prev) => {
          const next = [...prev]
          const lastIdx = next.length - 1
          if (lastIdx >= 0 && next[lastIdx].role === 'assistant') {
            next[lastIdx] = { role: 'assistant', content: next[lastIdx].content + delta }
          }
          return next
        })
      })
    } catch (e: any) {
      setHasError(e?.message || 'Unknown error')
    } finally {
      setIsLoading(false)
      controllerRef.current = null
    }
  }, [messages])

  const state = useMemo(() => ({ messages, isLoading, hasError }), [messages, isLoading, hasError])
  return { ...state, handleSend, handleReset }
}
