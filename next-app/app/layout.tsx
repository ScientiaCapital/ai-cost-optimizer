import './globals.css'
import type { ReactNode } from 'react'

export const metadata = {
  title: 'Ollama Next App',
  description: 'Streaming chat, structured outputs, embeddings demo',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased">{children}</body>
    </html>
  )
}
