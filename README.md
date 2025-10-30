# AI Cost Optimizer

> Smart multi-LLM routing system that automatically selects the most cost-efficient model based on prompt complexity.

## What It Does

Analyzes your prompts and routes them to the optimal LLM:
- **Simple queries** (< 100 tokens, no complexity keywords) → **Gemini Flash** (free tier)
- **Complex queries** (long prompts, technical keywords) → **Claude Haiku** (quality/cost balance)
- **Fallback** → **OpenRouter** (aggregator for 40+ models)

Tracks all costs in SQLite database so you always know your spend.

## Quick Start

### 1. Get API Keys

You need at least **one** of these:

- **Google Gemini** (recommended - free tier): https://aistudio.google.com/app/apikey
- **Anthropic Claude**: https://console.anthropic.com/
- **OpenRouter** (all models): https://openrouter.ai/keys

### 2. Setup

```bash
# Clone or navigate to project
cd ai-cost-optimizer

# Copy environment template
cp .env.example .env

# Edit .env and add your API key(s)
nano .env

# Install dependencies
pip install -r requirements.txt
pip install -r mcp/requirements.txt
```

### 3. Start FastAPI Service

```bash
# Run the service
python app/main.py

# You should see:
# "AI Cost Optimizer initialized with providers: ['gemini']"
# "Uvicorn running on http://0.0.0.0:8000"
```

Keep this terminal running!

### 4. Configure Claude Desktop

Edit your Claude Desktop config:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add the MCP server:

```json
{
  "mcpServers": {
    "ai-cost-optimizer": {
      "command": "python3",
      "args": [
        "/Users/tmkipper/Desktop/tk_projects/ai-cost-optimizer/mcp/server.py"
      ],
      "env": {
        "COST_OPTIMIZER_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

**Important**: Use the absolute path to `mcp/server.py` on your system!

### 5. Restart Claude Desktop

- Completely quit Claude Desktop (Cmd+Q on Mac)
- Relaunch Claude Desktop

### 6. Test It!

In Claude Desktop:

```
Please use the cost optimizer to answer: What is quantum computing?
```

You should see:
- Response from Gemini Flash (simple query)
- Cost breakdown: ~$0.000001
- Total cost tracking

Try a complex query:

```
Please use the cost optimizer to explain: Design a microservices architecture for a real-time analytics platform
```

Should route to Claude Haiku for better quality.

## How It Works

### Complexity Scoring

```python
# Simple: < 100 tokens + no keywords
"What is AI?" → Gemini Flash ($0.075 per 1M tokens)

# Complex: Long OR has keywords like explain, analyze, design
"Explain the architecture..." → Claude Haiku ($0.25 per 1M tokens)
```

### Cost Tracking

All requests logged to `optimizer.db`:

```bash
# View usage
curl http://localhost:8000/stats

# Check total cost
curl http://localhost:8000/stats | jq '.overall.total_cost'
```

## Project Structure

```
ai-cost-optimizer/
├── app/
│   ├── main.py           # FastAPI service
│   ├── complexity.py     # Token counter + keyword detector
│   ├── router.py         # Model selection logic
│   ├── providers.py      # API clients (Gemini, Claude, OpenRouter)
│   └── database.py       # SQLite cost tracker
├── mcp/
│   ├── server.py         # MCP tool for Claude Desktop
│   └── requirements.txt
├── .env                  # Your API keys
├── optimizer.db         # Cost database (auto-created)
└── README.md
```

## API Endpoints

### Complete Prompt

```bash
curl -X POST http://localhost:8000/complete \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is AI?", "max_tokens": 1000}'
```

Response:
```json
{
  "response": "AI is artificial intelligence...",
  "provider": "gemini",
  "model": "gemini-1.5-flash",
  "complexity": "simple",
  "tokens_in": 4,
  "tokens_out": 50,
  "cost": 0.000015,
  "total_cost_today": 0.000015
}
```

### Get Stats

```bash
curl http://localhost:8000/stats
```

### Get Recommendation

```bash
curl "http://localhost:8000/recommendation?prompt=What+is+AI"
```

### List Providers

```bash
curl http://localhost:8000/providers
```

## Configuration

### Environment Variables

```bash
# Provider API keys
GOOGLE_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here
OPENROUTER_API_KEY=your-key-here
CEREBRAS_API_KEY=your-key-here

# Optional
DATABASE_PATH=optimizer.db  # Database location
PORT=8000                   # Server port
LOG_LEVEL=INFO              # Logging verbosity
```

## Cerebras + CePO

- Next.js Cerebras endpoint: `next-app/app/api/cerebras/chat/route.ts` (set `CEREBRAS_API_KEY`).
- CePO experiment: see `experiments/README.md` and run `experiments/cepo_experiment.py`.

### Pricing

**Gemini Flash** (simple queries):
- Input: $0.075 per 1M tokens
- Output: $0.30 per 1M tokens
- Free tier available

**Claude Haiku** (complex queries):
- Input: $0.25 per 1M tokens
- Output: $1.25 per 1M tokens

**OpenRouter** (fallback):
- Pricing varies by model

## Troubleshooting

### Service won't start

```bash
# Check if port 8000 is in use
lsof -i :8000

# Check API keys are set
cat .env
```

### MCP tool not appearing in Claude Desktop

1. Verify absolute path in `claude_desktop_config.json`
2. Check FastAPI service is running (`curl http://localhost:8000/health`)
3. Restart Claude Desktop completely
4. Check Claude Desktop logs

### Wrong model selected

Check complexity score:
```bash
curl "http://localhost:8000/recommendation?prompt=your+prompt+here"
```

## Development

### Running Tests

```bash
# Test complexity scorer
python -c "from app.complexity import score_complexity; print(score_complexity('What is AI?'))"

# Test database
python -c "from app.database import CostTracker; t = CostTracker(); print(t.get_total_cost())"
```

### Adding a Provider

1. Add provider class in `app/providers.py`
2. Add to `init_providers()` function
3. Update routing logic in `app/router.py`

## License

MIT - do whatever you want with it!

## Questions?

This is a learning project built with the "GTME" philosophy (Give This to ME). Feel free to fork, modify, and make it yours!
