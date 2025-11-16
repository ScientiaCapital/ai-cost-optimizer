# AI Cost Optimizer - Architecture (v2.0.0)

## System Overview

**Purpose**: Intelligent LLM routing service that optimizes cost through learning-based model selection

**Status**: Production Ready (Phase 2 Complete - Nov 1, 2025)

## Three-Layer Architecture

```
┌─────────────────────────────────────────┐
│         FastAPI Layer                   │
│         app/main.py                     │
│  HTTP endpoints, validation, responses  │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         Service Layer                   │
│  app/services/routing_service.py        │
│  Orchestration, cache, cost tracking    │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         Core Routing Layer              │
│     app/routing/engine.py (Facade)      │
│                                         │
│  ┌─────────────┐    ┌────────────────┐ │
│  │ Strategies  │    │ Metrics        │ │
│  ├─────────────┤    ├────────────────┤ │
│  │ Complexity  │    │ Collector      │ │
│  │ Learning    │    │ Analyzer       │ │
│  │ Hybrid      │    │                │ │
│  └─────────────┘    └────────────────┘ │
└─────────────────────────────────────────┘
```

## Key Components

### RoutingEngine (`app/routing/engine.py`)
- **Pattern**: Facade
- **Responsibility**: Strategy selection and orchestration
- **Logic**: `auto_route=true` → HybridStrategy, `auto_route=false` → ComplexityStrategy

### RoutingService (`app/services/routing_service.py`)
- **Pattern**: Service Layer
- **Responsibility**: Business logic orchestration
- **Methods**:
  - `route_and_complete()` - Full flow with cache/routing/execution
  - `get_recommendation()` - Routing decision only
  - `get_routing_metrics()` - Analytics

### Routing Strategies (`app/routing/strategy.py`)
- **Pattern**: Strategy Pattern
- **ComplexityStrategy**: Baseline keyword + length scoring
- **LearningStrategy**: Pure historical performance data
- **HybridStrategy**: Learning with complexity validation (production default)

### MetricsCollector (`app/routing/metrics.py`)
- **Pattern**: Observer
- **Responsibility**: Track all routing decisions for ROI analysis
- **Data**: strategy, confidence, provider, model, cost, timestamp

### QueryPatternAnalyzer (`app/learning.py`)
- **Responsibility**: Analyze historical performance by pattern
- **Returns**: Recommendations with confidence levels

## API Endpoints

### Core Endpoints
- `POST /complete` - Route and execute with caching
- `GET /recommendation` - Get routing decision (no execution)
- `GET /health` - Service health + version

### Phase 2 Endpoints
- `GET /routing/metrics` - Performance analytics and ROI
- `GET /routing/decision` - Detailed routing explanation

### Legacy Endpoints
- `GET /stats` - Usage statistics
- `POST /feedback` - Quality feedback
- `GET /cache/stats` - Cache performance
- `GET /quality/stats` - Quality metrics
- `GET /insights` - DEPRECATED (use /routing/metrics)

## Database Schema

### response_cache (Phase 1)
```sql
- prompt_hash, prompt_normalized
- provider, model, complexity
- response_text, tokens_in, tokens_out, cost
- quality_score, upvotes, downvotes
- hit_count, invalidated
- created_at, last_used_at
```

### routing_metrics (Phase 2)
```sql
- prompt_hash
- strategy, confidence
- provider, model
- cost, baseline_cost
- timestamp
```

## Request Flow (auto_route=true)

```
1. POST /complete {"prompt": "...", "auto_route": true}
2. FastAPI validates → routing_service.route_and_complete()
3. Check cache → CostTracker.check_cache()
   ├─ HIT  → Return cached ($0 cost)
   └─ MISS → Continue
4. routing_engine.route(auto_route=true)
5. HybridStrategy selected
   ├─ Query learning analyzer
   ├─ Check confidence (HIGH/MEDIUM/LOW)
   └─ Validate against complexity
6. RoutingDecision returned
7. Execute: provider.send_message()
8. Track: MetricsCollector.track_decision()
9. Log: CostTracker.log_request() + store_in_cache()
10. Return response with metadata
```

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Strategy Pattern** | Enables pluggable routing algorithms |
| **Hybrid as Default** | Balances learning with validation |
| **auto_route Parameter** | Gradual rollout, A/B testing ready |
| **Service Layer** | Separation of concerns, testable |
| **SQLite** | Simple, embedded, sufficient for scale |
| **Facade Pattern** | Clean interface to complex routing |

## Key Files to Know

### Critical Files
- `app/main.py` - FastAPI endpoints (474 lines)
- `app/services/routing_service.py` - Service layer (200+ lines)
- `app/routing/engine.py` - RoutingEngine facade (150+ lines)
- `app/routing/strategy.py` - 3 strategies (378 lines)
- `app/routing/metrics.py` - MetricsCollector (269 lines)
- `app/database.py` - CostTracker (cache + logging)
- `app/learning.py` - QueryPatternAnalyzer

### Test Files
- `tests/test_routing_service.py` - Service layer tests (5)
- `tests/test_routing_engine.py` - Engine tests (6)
- `tests/test_*_strategy.py` - Strategy tests (20)
- `tests/test_metrics.py` - Metrics tests (5)
- Total: 42 tests, 0.09s execution

### Documentation
- `.claude/CLAUDE.md` - Project instructions
- `.claude/architecture.md` - This architecture (408 lines)
- `.claude/context.md` - Current state (265 lines)
- `docs/plans/2025-01-11-*-design.md` - Design docs
- `docs/plans/2025-01-11-*-implementation.md` - Implementation plans

## Provider Configuration

### Supported Providers
- **Gemini** (Google) - Free tier available, fast for simple queries
- **Claude** (Anthropic) - Best quality/cost for complex queries
- **Cerebras** - Ultra-fast inference
- **OpenRouter** - Fallback aggregator

### Routing Logic

**ComplexityStrategy:**
- Simple → Gemini Flash / Cerebras 8B
- Complex → Claude Haiku / Cerebras 70B
- Fallback → OpenRouter

**HybridStrategy:**
1. Query learning for recommendation
2. Validate against complexity
3. Use learning if confidence HIGH + reasonable
4. Fallback to complexity if issues

## Performance Characteristics

- **Cache hit**: <10ms
- **Complexity routing**: 20-50ms
- **Hybrid routing**: 30-70ms
- **Provider execution**: 500-3000ms
- **Current capacity**: 10-50 req/sec (single process)

## Environment Variables

```bash
# Required (at least one)
GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=...
CEREBRAS_API_KEY=...
OPENROUTER_API_KEY=...

# Optional
DATABASE_PATH=optimizer.db
DEFAULT_AUTO_ROUTE=false
PORT=8000
LOG_LEVEL=INFO
```

## Testing Strategy

- **TDD**: RED-GREEN-REFACTOR enforced
- **Mocking**: AsyncMock for async provider calls
- **Coverage**: 100% of new Phase 2 code
- **Integration**: Full flow tests with cache/routing/execution
- **Command**: `pytest -v` (42 passed in 0.09s)

## Known Limitations

1. **SQLite** - Not for high concurrency (use PostgreSQL in production)
2. **No Authentication** - Add for production
3. **No Rate Limiting** - Add per-user limits
4. **Local Deployment** - Deploy to cloud for scale

## Technical Debt

1. `/insights` endpoint deprecated (use `/routing/metrics`)
2. Backward compatibility fields (complexity in response)
3. No automated E2E tests (manual via Swagger)
4. Some private method access patterns could be cleaner

## Evolution Path

### ✅ Phase 1 Complete
- Learning infrastructure
- Quality feedback
- Pattern analysis

### ✅ Phase 2 Complete  
- Intelligent routing
- Strategy pattern
- Comprehensive metrics

### 🔮 Phase 3 (Options)
- Production deployment (AWS/GCP + PostgreSQL)
- Monitoring dashboard (visualize metrics)
- A/B testing framework
- Advanced caching (Redis)
- Revenue model (usage-based pricing)
- Multi-region deployment

## Quick Commands

```bash
# Start server
python app/main.py

# Run tests
pytest -v

# Test auto-routing
curl -X POST http://localhost:8000/complete \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain Python", "auto_route": true}'

# Check metrics
curl http://localhost:8000/routing/metrics

# Health check
curl http://localhost:8000/health

# Swagger UI
open http://localhost:8000/docs
```

## Code Patterns to Follow

### Async Functions
```python
async def route_and_complete(self, prompt: str, auto_route: bool, max_tokens: int):
    # Always use async for I/O operations
    response = await provider.send_message(prompt, max_tokens)
    return response
```

### Error Handling
```python
try:
    result = await routing_service.route_and_complete(...)
    return CompleteResponse(**result)
except Exception as e:
    logger.error(f"Error: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))
```

### Strategy Pattern
```python
def route(self, prompt: str, auto_route: bool, context: RoutingContext):
    if auto_route:
        return self.hybrid_strategy.route(prompt, context)
    else:
        return self.complexity_strategy.route(prompt, context)
```

## When Modifying This System

1. **Add new provider**: Create client in `app/providers/`, add to `init_providers()`
2. **Add new strategy**: Extend `RoutingStrategy` in `app/routing/strategy.py`
3. **Add new endpoint**: Add to `app/main.py`, update `RoutingService` if needed
4. **Modify routing logic**: Update strategy classes, keep RoutingEngine as facade
5. **Change metrics**: Update `MetricsCollector` in `app/routing/metrics.py`

## Important: Always Run Tests Before Pushing

```bash
pytest -v  # Must see: 42 passed in 0.09s
```

Last Updated: November 1, 2025 (Phase 2 Complete)
