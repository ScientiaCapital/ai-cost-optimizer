# AI Cost Optimizer - Quick Start Guide

## ✅ What We Built

Simplified AI Cost Optimizer with:
- **Smart Routing**: Auto-selects cheapest model based on complexity
- **5 Providers**:  (free), Cerebras (fast), Gemini (free tier), Claude (quality), OpenRouter (fallback)
- **SQLite Tracking**: Persistent cost history
- **MCP Integration**: Works with Claude Desktop

## 🚀 Setup (5 minutes)

### 1. Add Your API Keys

Edit `.env` in your project directory:

```bash
# Pick at least ONE provider:

# FREE (if you have local )

# ULTRA-FAST & CHEAP
CEREBRAS_API_KEY=your-key-from-cloud.cerebras.ai

# FREE TIER (recommended to start)
GOOGLE_API_KEY=your-key-from-aistudio.google.com

# BEST QUALITY
ANTHROPIC_API_KEY=your-key-from-console.anthropic.com

# FALLBACK (access all models)
OPENROUTER_API_KEY=your-key-from-openrouter.ai
```

### 2. Start the Service

```bash
cd /path/to/ai-cost-optimizer
python app/main.py
```

You should see:
```
INFO: AI Cost Optimizer initialized with providers: ['cerebras', 'gemini', 'claude']
INFO: Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal running!**

### 3. Test It Works

In another terminal:

```bash
# Test simple query (should use cheapest available)
curl -X POST http://localhost:8000/complete \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is AI?", "max_tokens": 100}'

# Check stats
curl http://localhost:8000/stats | jq '.overall.total_cost'
```

### 4. Add to Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

**Restart Claude Desktop** (Cmd+Q, then relaunch)

### 5. Test in Claude Desktop

```
Use the cost optimizer to answer: What is quantum computing?
```

Expected response:
- Answer from optimal provider (/Cerebras/Gemini based on what's configured)
- Cost breakdown
- Provider used

## 🎯 Routing Logic

**Simple queries** (< 100 tokens, no keywords):
1.  (FREE) → 2. Cerebras ($0.10/1M) → 3. Gemini (FREE tier) → 4. OpenRouter

**Complex queries** (long or keywords like "explain", "analyze"):
1. Claude Haiku ($0.25/1M) → 2. Cerebras 70B ($0.60/1M) → 3. OpenRouter

## 📊 Provider Comparison

| Provider | Speed | Cost | Best For |
|----------|-------|------|----------|
| **** | Medium | FREE | Local testing, privacy |
| **Cerebras** | ⚡ FASTEST | $0.10/1M | Speed matters, simple queries |
| **Gemini** | Fast | FREE tier | Testing, light usage |
| **Claude** | Medium | $0.25/1M | Complex queries, best quality |
| **OpenRouter** | Varies | Varies | Fallback, access all models |

## 🔧 Configuration

Get API keys:
- **Cerebras**: https://cloud.cerebras.ai/
- **Google Gemini**: https://aistudio.google.com/app/apikey
- **Anthropic Claude**: https://console.anthropic.com/
- **OpenRouter**: https://openrouter.ai/keys

For :
```bash
# Install 

# Pull a model

# Start server (runs automatically on Mac)
```

## 💡 Tips

**Start with Google Gemini** - Free tier, no credit card needed

**Add Cerebras** - Super fast, very cheap

**Use ** - Completely free if you have a decent Mac (M1+)

**Claude for quality** - When you need best reasoning

## 🐛 Troubleshooting

**Service won't start:**
- Check `.env` has at least one API key
- Check port 8000 not in use: `lsof -i :8000`

**MCP not appearing:**
- Verify absolute path in Claude Desktop config
- Check service is running: `curl http://localhost:8000/health`
- Completely quit and restart Claude Desktop

**Wrong provider selected:**
- Check which providers are enabled: `curl http://localhost:8000/providers`
- See routing decision: `curl "http://localhost:8000/recommendation?prompt=test"`

## 📁 Project Structure

```
app/
├── main.py          # FastAPI service
├── complexity.py    # Token counter + keyword detector
├── router.py        # Smart routing logic
├── providers.py     # 5 provider implementations
└── database.py      # SQLite cost tracker

mcp/
└── server.py        # Claude Desktop integration

.env                 # Your API keys (YOU EDIT THIS)
optimizer.db         # Cost database (auto-created)
```

## 🎓 Next Steps

Once this works:
1. Test with different query types
2. Check cost tracking: `http://localhost:8000/stats`
3. Experiment with provider priorities in `router.py`
4. Add more providers or custom routing logic

## ❓ Questions?

This is a GTME (Give This to ME) learning project. Fork it, break it, make it yours!

Key files to understand:
- `app/complexity.py` - How complexity is scored
- `app/router.py` - How providers are selected
- `app/providers.py` - How APIs are called
