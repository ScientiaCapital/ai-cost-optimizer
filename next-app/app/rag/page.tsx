"use client"

import { useState } from 'react'

type SearchResult = { id: string; text: string; score: number }

export default function RagPage() {
  const [docId, setDocId] = useState('doc-1')
  const [docText, setDocText] = useState('Ollama cloud models let you run huge models via remote host.')
  const [query, setQuery] = useState('What are cloud models?')
  const [results, setResults] = useState<SearchResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [hasError, setHasError] = useState<string | null>(null)

  const handleIndex = async () => {
    setIsLoading(true)
    setHasError(null)
    try {
      const res = await fetch('/api/embeddings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'index', id: docId, text: docText }),
      })
      if (!res.ok) throw new Error(await res.text())
    } catch (e: any) {
      setHasError(e?.message || 'Unknown error')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = async () => {
    setIsLoading(true)
    setHasError(null)
    setResults([])
    try {
      const res = await fetch('/api/embeddings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'search', query }),
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setResults(data.results ?? [])
    } catch (e: any) {
      setHasError(e?.message || 'Unknown error')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="mx-auto max-w-3xl space-y-6 p-6">
      <h1 className="text-xl font-semibold">RAG (Embeddings)</h1>

      <section className="space-y-2 rounded-lg border bg-white p-4">
        <h2 className="font-medium">Index a document</h2>
        <div className="flex items-center gap-2">
          <input
            value={docId}
            onChange={(e) => setDocId(e.target.value)}
            className="w-40 rounded-md border px-3 py-2 text-sm"
            aria-label="Document ID"
          />
          <textarea
            value={docText}
            onChange={(e) => setDocText(e.target.value)}
            className="w-full rounded-md border px-3 py-2 text-sm"
            rows={3}
            aria-label="Document text"
          />
        </div>
        <button
          onClick={handleIndex}
          disabled={isLoading}
          className="rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700 disabled:opacity-60"
          aria-label="Index document"
        >
          Index
        </button>
      </section>

      <section className="space-y-2 rounded-lg border bg-white p-4">
        <h2 className="font-medium">Semantic search</h2>
        <div className="flex items-center gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full rounded-md border px-3 py-2 text-sm"
            aria-label="Query"
          />
          <button
            onClick={handleSearch}
            disabled={isLoading}
            className="rounded-md bg-gray-800 px-4 py-2 text-white hover:bg-black disabled:opacity-60"
            aria-label="Search"
          >
            Search
          </button>
        </div>

        {hasError && <div className="rounded-md bg-red-50 p-2 text-sm text-red-700">{hasError}</div>}
        <ul className="space-y-2">
          {results.map((r) => (
            <li key={r.id} className="rounded-md border bg-gray-50 p-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium">{r.id}</span>
                <span className="text-gray-500">{r.score.toFixed(4)}</span>
              </div>
              <p className="mt-1 text-gray-700">{r.text}</p>
            </li>
          ))}
        </ul>
      </section>
    </main>
  )
}
