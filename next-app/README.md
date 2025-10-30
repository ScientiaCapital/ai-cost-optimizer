# Ollama + Next.js Demos

Streaming chat, structured outputs (Zod-validated), and minimal embeddings-based RAG.

## Prereqs
- Node.js 18+
- Local Ollama or Ollama Cloud (preview)
  - Cloud: `ollama signin` and create API key. See [Ollama Cloud docs](https://docs.ollama.com/cloud)

## Setup
```bash
cd next-app
cp .env.example .env.local
pnpm i # or npm i / yarn
pnpm dev
```

If using local Ollama, ensure server is running:
```bash
ollama serve
```

If using Cloud as a remote host set in `.env.local`:
```
OLLAMA_HOST=https://ollama.com
OLLAMA_API_KEY=…
```

## Endpoints
- `POST /api/chat` — Proxies streaming chat to Ollama (`/api/chat`), supports `think` field per streaming guidance. See [Streaming](https://docs.ollama.com/capabilities/streaming).
- `POST /api/structured` — Non-streamed response with `format` set to Zod schema. See [Structured Outputs](https://docs.ollama.com/capabilities/structured-outputs).
- `POST /api/embeddings` — Simple in-memory index/search via `/api/embeddings`.

## UI Pages
- `/chat` — Streaming chat demo with incremental rendering.
- `/structured` — Zod-validated structured output for a topic.
- `/rag` — Index simple texts and perform cosine-similarity search.

## Notes
- Thinking-capable streaming chunks may emit `message.thinking`; we accumulate any `thinking` or `content` fields. See [Streaming thinking](https://docs.ollama.com/capabilities/streaming).
- For Cloud models list/reference, see [Cloud Models](https://docs.ollama.com/cloud).

## Optional: OpenRouter integration
You can extend this project to use OpenRouter with the OpenAI SDK or direct API.
- Quickstart: [OpenRouter Quickstart](https://openrouter.ai/docs/quickstart)
- Model routing: [Model Routing](https://openrouter.ai/docs/features/model-routing)
- Provider routing: [Provider Routing](https://openrouter.ai/docs/features/provider-routing)
