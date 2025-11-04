# AI Cost Optimizer

> Smart multi-LLM routing system that automatically selects the most cost-efficient model based on prompt complexity.

## What It Does

Analyzes your prompts and routes them to the optimal LLM:
- **Simple queries** (< 100 tokens, no complexity keywords) → **Gemini Flash** (free tier)
- **Complex queries** (long prompts, technical keywords) → **Claude Haiku** (quality/cost balance)
- **Fallback** → **OpenRouter** (aggregator for 40+ models)

Tracks all costs in SQLite database so you always know your spend.

### Key Features

- **Learning Intelligence (Phase 1)**: Smart routing recommendations based on historical performance data
- **Model Abstraction**: Black-box tier labels protect competitive intelligence while delivering customer value
- **CLI Dashboards**: Visual learning progress and savings projections (customer-safe and admin versions)
- **Agent-Powered Analysis**: Natural language cost optimization queries via Claude Agent SDK
- **Real-Time Cost Tracking**: SQLite database tracks every request, cost, and performance metric

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
        "/ABSOLUTE/PATH/TO/ai-cost-optimizer/mcp/server.py"
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

## Security: Customer vs Admin Dashboards

The system implements a **two-tier architecture** for competitive protection:

### Customer-Safe Distribution

**ALWAYS distribute:** `agent/customer_dashboard.py`
- Shows ONLY tier labels (Economy Tier, Premium Tier, etc.)
- NEVER exposes actual model names or providers
- Safe for external users, customers, public demos

### Internal Use Only

**NEVER distribute:** `agent/admin_dashboard.py`
- Shows actual model names (e.g., "openrouter/deepseek-coder", "claude/claude-3-haiku")
- Exposes internal routing logic and model selection strategy
- Contains competitive intelligence
- For development, debugging, and internal analysis ONLY

### Why This Matters

**Competitive Protection:**
- Your model selection strategy is valuable intellectual property
- Hard-won knowledge about which models work best for each task type
- Cost optimization approach is a competitive advantage

**Customer Value:**
- Customers still get full optimization benefits
- Recommendations show tier performance and savings
- Transparent about quality and cost without exposing strategy

### File Security Matrix

| File | Distribution | Shows Models? | Purpose |
|------|--------------|---------------|---------|
| `customer_dashboard.py` | ✅ External OK | ❌ No - Tiers only | Customer dashboards, demos |
| `admin_dashboard.py` | ⛔ Internal ONLY | ✅ Yes - Full details | Dev, debugging, analysis |
| `model_abstraction.py` | ⛔ Internal ONLY | ✅ Contains mapping | Core abstraction logic |
| Agent tools (mode="external") | ✅ External OK | ❌ No - Tiers only | Customer-facing recommendations |
| Agent tools (mode="internal") | ⛔ Internal ONLY | ✅ Yes - Full details | Admin analysis |

**Before sharing ANY code or dashboard:**
1. Check if it contains actual model names
2. Verify it only shows tier labels
3. Confirm it's the customer_dashboard.py version
4. Never share admin_dashboard.py or model_abstraction.py

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
