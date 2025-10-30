import Link from 'next/link'

export default function HomePage() {
  return (
    <main className="mx-auto max-w-3xl p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Ollama Integration Demos</h1>
      <p className="text-sm text-gray-600">Streaming chat, structured outputs, and embeddings-based RAG.</p>
      <ul className="space-y-3">
        <li>
          <Link href="/chat" className="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700" aria-label="Go to Chat demo">
            Chat (Streaming)
          </Link>
        </li>
        <li>
          <Link href="/structured" className="inline-flex items-center rounded-md bg-emerald-600 px-4 py-2 text-white hover:bg-emerald-700" aria-label="Go to Structured Outputs demo">
            Structured Outputs
          </Link>
        </li>
        <li>
          <Link href="/rag" className="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700" aria-label="Go to RAG demo">
            RAG (Embeddings)
          </Link>
        </li>
      </ul>
    </main>
  )
}
