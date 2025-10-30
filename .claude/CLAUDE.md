# Claude Instructions for AI Cost Optimizer

## Project Overview

AI Cost Optimizer is a multi-LLM routing system that automatically selects the most cost-efficient model based on task complexity. Built as a learning project and personal tool that others might find useful.

**GitHub**: https://github.com/ScientiaCapital/ai-cost-optimizer

## Project Philosophy

- **GTME (Give This to ME)**: Learning by building tools for personal use
- **Scratch Your Own Itch**: Solving real problems (unpredictable AI costs)
- **Share What Works**: Open source for others who face the same challenges
- **Practical Over Perfect**: Ship working solutions, iterate based on usage

## Tech Stack

- **Backend**: FastAPI + Python 3.11
- **Routing**: Custom complexity analysis algorithm
- **Database**: SQLite (development) / Persistent volume (production)
- **Integration**: Model Context Protocol (MCP) for Claude Desktop
- **Deployment**: Docker + RunPod
- **Providers**: Anthropic, Google, Cerebras, DeepSeek, OpenRouter, HuggingFace, Cartesia

## Project Structure

```
ai-cost-optimizer/
├── main.py                 # FastAPI application entry point
├── router.py               # Smart routing logic (complexity → model selection)
├── provider_manager.py     # Provider abstraction layer
├── cost_tracker.py         # Cost calculation and tracking
├── budget.py               # Budget management and alerts
├── config.py               # Configuration with smart DB path detection
├── providers/              # LLM provider implementations
│   ├── __init__.py        # Base classes
│   ├── anthropic_provider.py
│   ├── google_provider.py
│   ├── cerebras_provider.py
│   ├── deepseek_provider.py
│   ├── openrouter.py
│   ├── cartesia_provider.py
│   └── huggingface_provider.py
├── mcp/                    # Claude Desktop integration
│   ├── server.py          # MCP protocol implementation
│   ├── mcp.json           # Server manifest
│   └── README.md          # Setup instructions
├── skill-package/          # Marketplace distribution
│   ├── SKILL.md           # Marketplace listing
│   ├── deployment/        # RunPod deployment files
│   └── screenshots/       # Demo assets (to be added)
└── Dockerfile             # Production container

```

## Key Concepts

### Complexity Scoring (0.0 - 1.0)

The router analyzes prompts and assigns complexity scores:
- **0.0-0.2 (Free)**: Simple facts, definitions → Gemini Flash
- **0.2-0.4 (Cheap)**: Code snippets, summaries → Cerebras, DeepSeek, Haiku
- **0.4-0.7 (Medium)**: Analysis, explanations → Gemini Pro, Sonnet
- **0.7-1.0 (Premium)**: Architecture, research → Opus, GPT-4

**Factors**:
- Prompt length
- Technical keywords
- Code presence
- Structural complexity

### Cost Tiers

See `config.py` MODEL_TIERS for the complete mapping of (provider, model) → tier.

### Provider Architecture

Each provider implements:
- `complete(model, prompt, max_tokens)` → CompletionResult
- `get_models()` → List[ModelInfo]
- `calculate_cost(model, input_tokens, output_tokens)` → float

The `ProviderManager` auto-initializes providers based on available API keys.

## Development Guidelines

### Adding a New Provider

1. **Create provider file** in `providers/`:
   ```python
   from . import LLMProvider, CompletionResult, ModelInfo

   class NewProvider(LLMProvider):
       def __init__(self, api_key: str):
           self.api_key = api_key

       async def complete(...) -> CompletionResult:
           # Implementation

       def get_models(self) -> List[ModelInfo]:
           # Return model list with pricing
   ```

2. **Update `config.py`**:
   - Add to `PROVIDER_CONFIGS`
   - Add models to `PROVIDER_MODELS`
   - Add to appropriate `MODEL_TIERS`

3. **Update `provider_manager.py`**:
   - Import the provider
   - Add initialization logic

4. **Test**:
   ```bash
   export NEW_PROVIDER_API_KEY=your-key
   python main.py
   curl http://localhost:8000/v1/providers
   ```

### Modifying Complexity Analysis

The routing logic is in `router.py`:
- `analyze_complexity(prompt)` → float
- `route_request(prompt, budget_limit)` → (provider, model, complexity)

**Be careful**: Changes affect all routing decisions!

### Adding MCP Tools

To add a new tool to the Claude Desktop integration:

1. **Update `mcp/mcp.json`**: Add tool definition
2. **Update `mcp/server.py`**:
   - Add tool in `list_tools()`
   - Implement handler method
   - Add case in `call_tool()`
3. **Test with Claude Desktop**

## Working with This Project

### Common Tasks

**Start service locally**:
```bash
python main.py
# Visit http://localhost:8000/docs
```

**Test routing**:
```bash
curl -X POST http://localhost:8000/v1/complete \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is AI?", "max_tokens": 100}'
```

**Check available models**:
```bash
curl http://localhost:8000/v1/models
```

**Build Docker image**:
```bash
docker build -t ai-cost-optimizer:latest .
```

### Configuration

**Environment Variables**:
- Provider API keys: `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, etc.
- Budget: `DEFAULT_MONTHLY_BUDGET=100.0`
- Database: `DATABASE_URL` (auto-detected if unset)
- Logging: `LOG_LEVEL=INFO`

**Smart defaults**:
- Database: Uses `/data/optimizer.db` in production, `./optimizer.db` locally
- Providers: Auto-enabled based on available API keys
- Budget: $100/month default

## Current State

### What Works ✅

- FastAPI service with 6 endpoints
- Smart routing based on complexity
- 7 provider integrations (Anthropic, Google, Cerebras, DeepSeek, OpenRouter, HuggingFace, Cartesia)
- Cost tracking and budget management
- Full SQLite persistence (cost tracking, response caching, quality feedback)
- MCP server for Claude Desktop (5 tools)
- Docker containerization
- RunPod deployment configuration
- Health checks and metrics endpoints
- Production logging

### What's Stubbed 🚧

- Email/webhook alerts (budget alerts stubbed)
- Advanced analytics and reporting

### What's Missing ❌

- Icon for marketplace (512x512 PNG needed)
- Screenshots for marketplace (3-5 needed)
- Actual usage in production (needs testing)
- Dashboard UI (Streamlit planned)

## Known Issues

1. **Budget alerts**: Thresholds calculated but no actual alerting
2. **OpenRouter**: Some models may have different pricing
3. **Complexity**: Heuristic-based, not ML-powered (yet)

## Future Plans

**v1.1** (Next):
- Implement budget alert notifications (email, webhook, logging)
- Add interactive CLI testing tool
- Add Streamlit dashboard

**v1.2** (Later):
- ML-based complexity prediction
- A/B testing framework
- Response quality scoring

**v2.0** (Future):
- Cost vs quality optimization curves
- Team collaboration features
- Advanced analytics

## Testing with Claude Desktop

After making changes:

1. **Restart FastAPI service**:
   ```bash
   python main.py
   ```

2. **Restart Claude Desktop**: Completely quit and reopen

3. **Test in conversation**:
   ```
   Please use the cost optimizer to complete: "What is quantum computing?"
   ```

4. **Check logs**:
   - FastAPI: Terminal output
   - MCP Server: Claude Desktop logs

## Debugging Tips

**Service not starting**:
- Check API keys are set
- Verify Python version >= 3.10
- Check port 8000 is available

**MCP server not appearing**:
- Verify absolute path in `claude_desktop_config.json`
- Check Python is in PATH
- Look at Claude Desktop logs

**Wrong model selected**:
- Check complexity score in response
- Review `router.py` analyze_complexity()
- Verify model is in correct tier in `config.py`

**Provider errors**:
- Check API key is valid
- Verify provider is enabled in response to `/v1/providers`
- Check provider's rate limits

## Code Style

- **Async/await**: Use for all I/O operations
- **Type hints**: Required for function signatures
- **Docstrings**: Use for public methods
- **Error handling**: Be specific, provide helpful messages
- **Logging**: Use `logger.info/error` not `print()`

## Important Notes

- **No API keys in code**: Always use environment variables
- **Smart defaults**: The app should work with minimal config
- **User-friendly errors**: Help users fix problems
- **Cost awareness**: Default to cheaper models when uncertain
- **Fail gracefully**: Handle provider outages elegantly

## Questions to Ask

When working on this project, consider:

1. **Does this save users money?** The core value proposition
2. **Is the routing decision clear?** Users should understand why a model was chosen
3. **Does it handle failures well?** Providers go down, API keys expire
4. **Is the cost tracking accurate?** Users need to trust the numbers
5. **Can someone deploy this easily?** Minimize friction

## Learning Goals

This project teaches:
- FastAPI and async Python
- LLM provider integration
- Cost optimization algorithms
- Docker and cloud deployment
- MCP protocol implementation
- API design and versioning
- Production monitoring and logging

## Contributing

This is a personal learning project, but PRs welcome for:
- Bug fixes
- New provider integrations
- Improved complexity analysis
- Better documentation
- Test coverage

**Keep it simple**: This is a tool first, not a framework.

## Resources

- **FastAPI**: https://fastapi.tiangolo.com
- **MCP Protocol**: https://modelcontextprotocol.io
- **RunPod**: https://docs.runpod.io
- **Provider APIs**: See each provider's documentation

---

**Remember**: This is about solving a real problem (unpredictable AI costs) in a practical way. Keep it working, keep it simple, keep it useful.
