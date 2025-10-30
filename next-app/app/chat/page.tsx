"use client"

import { useEffect, useMemo, useRef, useState } from 'react'
import { useStreamChat } from '@/hooks/useStreamChat'
import { MessageBubble } from '@/components/MessageBubble'

export default function ChatPage() {
  const inputRef = useRef<HTMLInputElement | null>(null)
  const { messages, isLoading, hasError, handleSend, handleReset } = useStreamChat()
  const [draft, setDraft] = useState('')

  const handleSubmit = async () => {
    await handleSend(draft)
    setDraft('')
    inputRef.current?.focus()
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-4 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Chat (Streaming)</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={handleReset}
            className="rounded-md bg-gray-200 px-3 py-1.5 text-sm hover:bg-gray-300"
            aria-label="Reset conversation"
          >
            Reset
          </button>
        </div>
      </div>

      <div className="flex-1 space-y-3 rounded-lg border bg-white p-4">
        {messages.length === 0 && (
          <p className="text-sm text-gray-500">Ask anything to start the stream.</p>
        )}
        {messages.map((m, i) => (
          <MessageBubble key={i} role={m.role === 'user' ? 'user' : 'assistant'}>
            {m.content}
          </MessageBubble>
        ))}
      </div>

      {hasError && <div className="rounded-md bg-red-50 p-2 text-sm text-red-700">{hasError}</div>}

      <div className="flex items-center gap-2">
        <input
          ref={inputRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit() }}
          aria-label="Chat input"
          placeholder="Type your message..."
          className="w-full rounded-md border px-3 py-2 text-sm"
        />
        <button
          onClick={handleSubmit}
          disabled={isLoading || draft.trim().length === 0}
          className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-60"
          aria-label="Send message"
        >
          {isLoading ? 'Streaming...' : 'Send'}
        </button>
      </div>
    </main>
  )
}
