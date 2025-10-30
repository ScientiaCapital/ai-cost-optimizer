# AI Cost Optimizer

**Stop overpaying for AI.** Automatically route prompts to the cheapest suitable model and save 40-70% on LLM costs.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)

> 🎓 **GTME Learning Project** - Built to scratch my own itch and learn by doing. Useful for real work, shared openly for others who face the same problem.

## The Problem

AI costs are unpredictable. What starts as $50/month can spiral to $5,000 when experimenting. You're either:
- Using GPT-4 for everything (expensive)
- Using GPT-3.5 for everything (quality suffers)
- Manually picking models (tedious)

## The Solution

**Smart routing:** Analyze complexity → Pick optimal model → Save money.

- Simple task? Free model (Gemini Flash, Ollama)
- Complex reasoning? Premium model (Claude Opus, GPT-4)
- Everything in between? Cost-efficient options

**Result:** Use GPT-4 when you need it, not by default.

## Features

- ⚡ **Smart Routing**: Automatic complexity analysis (0.0-1.0 score) → optimal model selection
- 💰 **Cost Tracking**: Real-time cost calculation with per-request breakdowns
- 🎯 **Budget Management**: Set limits, get alerts at 50%, 80%, 90% thresholds
- 🔌 **Multi-Provider**: 40+ models across 8 providers (Anthropic, Google, Cerebras, DeepSeek, OpenRouter, HuggingFace, Ollama)
- 🖥️ **Claude Desktop Integration**: Native MCP protocol support (5 tools)
- 🐳 **Production Ready**: Docker, health checks, metrics, structured logging
- 📊 **Transparent**: See exactly which model was chosen and why

## Supported Providers
- **OpenRouter** (40+ models)
- **Anthropic** (Claude 3.5, Opus)
- **Google** (Gemini 1.5, 2.0)
- **Cerebras** (Llama 3.1)
- **Deepseek** (Chat, Coder)
- **Ollama** (Local/Free)
- **HuggingFace** (Open models)

## Quick Start

### 1. Setup
```bash
cd ai-cost-optimizer
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Configure Providers
Edit `.env` and add API keys for providers you want to use:
```bash
OPENROUTER_API_KEY=sk-or-v1-...     # Start here (easiest)
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
# Add others as needed
```

Get API keys:
- OpenRouter: https://openrouter.ai/keys
- Anthropic: https://console.anthropic.com
- Google: https://aistudio.google.com/apikey
- Others: See provider websites

### 3. Run
```bash
python main.py  # Starts at http://localhost:8000
```

### 4. Test
```bash
curl -X POST http://localhost:8000/v1/complete \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain AI in simple terms", "max_tokens": 200}'
```

## How It Works

**Automatic Routing**: Analyzes prompt complexity → Selects cheapest suitable model → Routes to provider

**Cost Tiers**:
- Free: Ollama (local), Gemini 2.0
- Cheap: Cerebras, Deepseek ($0.1-1/M tokens)
- Medium: Claude Sonnet, Gemini Pro ($1-5/M)
- Premium: Claude Opus ($15-75/M)

## API Endpoints

```bash
POST /v1/complete      # Main completion endpoint
GET  /v1/models        # List all available models
GET  /v1/providers     # List enabled providers
GET  /v1/usage         # Get usage stats
POST /v1/budget        # Set budget limits
```

## Force Specific Provider/Model
```bash
curl -X POST http://localhost:8000/v1/complete \
  -d '{"prompt": "test", "provider": "anthropic", "model": "claude-3-5-sonnet-20241022"}'
```

## Cost Savings Example
- Simple task via GPT-4: $0.030
- Same task via router (Gemini Flash): $0.0003
- **Savings: 99%**

## Documentation

- **[CONTEXT.md](./CONTEXT.md)** - Project origin, goals, current state, roadmap
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Technical architecture and system design
- **[.claude/CLAUDE.md](./.claude/CLAUDE.md)** - Instructions for AI assistants working on this project
- **[skill-package/](./skill-package/)** - Claude Desktop marketplace package

## About This Project

This is a **GTME (Give This to ME) learning project** - built to solve a real problem I face daily while learning new skills:

**Learning Goals**:
- FastAPI and async Python
- LLM provider integration (8 different APIs!)
- Cost optimization algorithms
- Docker and cloud deployment (RunPod)
- MCP protocol for Claude Desktop
- Production monitoring and observability

**Personal Value**:
- Save money on AI experimentation
- Understand which models are actually needed
- Data on spending patterns
- No anxiety about costs

**For Others**:
- Open source and MIT licensed
- Real solution to a common problem
- Simple, practical, no framework bloat
- Works out of the box

## Roadmap

### v1.0 (Current - MVP)
- ✅ Core routing logic
- ✅ 8 provider integrations
- ✅ Cost tracking (in-memory)
- ✅ Budget management
- ✅ Claude Desktop integration (MCP)
- ✅ Docker + RunPod deployment

### v1.1 (Next - 2 Weeks)
- [ ] Database persistence (SQLite)
- [ ] Budget alert notifications (email/webhook)
- [ ] Streamlit dashboard
- [ ] Usage analytics

### v1.2 (Later - 1-2 Months)
- [ ] ML-based complexity prediction
- [ ] Response quality scoring
- [ ] A/B testing framework
- [ ] More providers (Groq, Mistral, Cohere)

### v2.0 (Future - 3+ Months)
- [ ] Team collaboration features
- [ ] Shared budgets
- [ ] Cost vs quality optimization
- [ ] Advanced analytics

## Contributing

This is a personal learning project, but PRs welcome for:
- Bug fixes
- New provider integrations
- Improved complexity analysis
- Documentation improvements

Keep it simple - this is a tool first, not a framework.

## License

MIT License - Free for personal and commercial use

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com) - Modern Python web framework
- [MCP SDK](https://modelcontextprotocol.io) - Claude Desktop integration
- Provider APIs: Anthropic, Google, Cerebras, DeepSeek, OpenRouter, HuggingFace, Ollama

## Support

- **Issues**: https://github.com/ScientiaCapital/ai-cost-optimizer/issues
- **Discussions**: https://github.com/ScientiaCapital/ai-cost-optimizer/discussions

---

**Built by a dev, for devs.** Stop overpaying for AI. Start optimizing. 🚀
