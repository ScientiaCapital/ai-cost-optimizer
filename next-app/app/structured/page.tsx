"use client"

import { useState } from 'react'

export default function StructuredPage() {
  const [topic, setTopic] = useState('Canada')
  const [result, setResult] = useState<any | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [hasError, setHasError] = useState<string | null>(null)

  const handleFetch = async () => {
    setIsLoading(true)
    setHasError(null)
    setResult(null)
    try {
      const res = await fetch('/api/structured', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic }),
      })
      if (!res.ok) throw new Error(await res.text())
      setResult(await res.json())
    } catch (e: any) {
      setHasError(e?.message || 'Unknown error')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="mx-auto max-w-3xl p-6 space-y-4">
      <h1 className="text-xl font-semibold">Structured Outputs</h1>
      <div className="flex items-center gap-2">
        <input
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          className="w-full rounded-md border px-3 py-2 text-sm"
          aria-label="Topic"
          placeholder="Enter a topic"
        />
        <button
          onClick={handleFetch}
          disabled={isLoading}
          className="rounded-md bg-emerald-600 px-4 py-2 text-white hover:bg-emerald-700 disabled:opacity-60"
          aria-label="Fetch structured output"
        >
          {isLoading ? 'Loading...' : 'Fetch'}
        </button>
      </div>
      {hasError && <div className="rounded-md bg-red-50 p-2 text-sm text-red-700">{hasError}</div>}
      {result && (
        <pre className="overflow-auto rounded-lg border bg-white p-4 text-xs">
{JSON.stringify(result, null, 2)}
        </pre>
      )}
    </main>
  )
}
