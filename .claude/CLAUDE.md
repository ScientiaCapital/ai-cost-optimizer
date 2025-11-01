# CLAUDE.md - AI Cost Optimizer

## 1. Project Status & Overview

**Current Status**: Production Ready - Phase 2 Complete ✅
**Version**: 2.0.0
**Type**: AI/ML Cost Optimization Service with Learning Intelligence

The AI Cost Optimizer is a FastAPI-based service that intelligently routes LLM prompts to optimal AI models using learning-based intelligence with hybrid validation. It serves as both a standalone API and an MCP (Model Context Protocol) server for Claude Desktop integration.

**Phase 2 Features** (NEW):
- **Intelligent Auto-Routing**: Learning-based model selection with hybrid validation
- **Strategy Pattern Architecture**: Pluggable routing strategies (complexity, learning, hybrid)
- **Metrics & Analytics**: Comprehensive routing performance tracking and ROI analysis
- **Three-Layer Architecture**: Clean separation (FastAPI → RoutingService → RoutingEngine)

**Core Features**:
- Multi-provider support (Gemini, Claude, Cerebras, OpenRouter)
- Real-time cost tracking and savings analysis
- Response caching for instant results
- Claude Desktop MCP integration
- Fallback routing for reliability

## 2. Technology Stack

### Core Framework & Runtime
- **Language**: Python 3.8+
- **Web Framework**: FastAPI (with automatic OpenAPI docs)
- **ASGI Server**: Uvicorn with standard extras
- **Environment Management**: python-dotenv

### Data & Validation
- **Data Validation**: Pydantic v2
- **Database**: SQLite with sqlite3
- **HTTP Client**: httpx for async API calls

### AI/ML Components (Phase 2 Architecture)
- **Primary Providers**: Google Gemini, Anthropic Claude, Cerebras, OpenRouter
- **RoutingEngine**: Strategy pattern-based routing orchestrator
  - **ComplexityStrategy**: Keyword + length-based scoring (baseline)
  - **LearningStrategy**: Learning-based recommendations from performance data
  - **HybridStrategy**: Learning with complexity validation (default for auto_route=true)
- **MetricsCollector**: Tracks routing decisions, costs, confidence levels
- **QueryPatternAnalyzer**: Analyzes historical performance by query patterns
- **Token Counting**: Custom token estimation logic

### Development & Testing
- **Testing**: pytest
- **Containerization**: Docker & Docker Compose
- **Code Quality**: Pre-commit hooks (if configured)

## 3. Development Workflow

### Initial Setup
```bash
# Clone and setup
git clone <repository>
cd ai-cost-optimizer

# Environment setup
cp .env.example .env
# Edit .env with your API keys

# Install dependencies
pip install -r requirements.txt
pip install -r mcp/requirements.txt
```

### Running the Application

**Development Mode**:
```bash
# Run FastAPI with auto-reload
python app/main.py
# or
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production Mode**:
```bash
# Using Docker
docker-compose up --build

# Or directly
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_routing.py -v
```

### Building & Deployment
```bash
# Build Docker image
docker build -t ai-cost-optimizer .

# Run with Docker
docker run -p 8000:8000 --env-file .env ai-cost-optimizer
```

## 4. Environment Variables

Create a `.env` file with:

### Required (at least one provider)
```env
# Gemini (Recommended for free tier)
GOOGLE_API_KEY=your_gemini_key

# Anthropic Claude  
ANTHROPIC_API_KEY=your_claude_key

# OpenRouter (Fallback)
OPENROUTER_API_KEY=your_openrouter_key
```

### Optional Configuration
```env
# Service Configuration
COST_OPTIMIZER_API_URL=http://localhost:8000
DATABASE_URL=sqlite:///./costs.db
LOG_LEVEL=INFO

# MCP Server (for Claude Desktop)
MCP_SERVER_PORT=8001
```

## 5. Key Files & Their Purposes

### Core Application
- `app/main.py` - FastAPI application entry point, route definitions
- `app/routing/` - Prompt analysis and model routing logic
- `app/providers/` - API clients for different LLM providers
- `app/database/` - SQLite cost tracking and database operations
- `app/models/` - Pydantic models for request/response schemas

### MCP Integration
- `mcp/server.py` - MCP server implementation for Claude Desktop
- `mcp/requirements.txt` - MCP-specific dependencies

### Configuration & Deployment
- `requirements.txt` - Main application dependencies
- `Dockerfile` - Containerization configuration
- `docker-compose.yml` - Multi-service setup
- `.env.example` - Environment template

### Testing
- `tests/` - Test suite with unit and integration tests
- `tests/test_routing.py` - Routing logic tests
- `tests/test_providers.py` - Provider API tests

## 6. Testing Approach

### Test Structure
```python
# Example test pattern
def test_prompt_routing_simple():
    """Test that simple prompts route to Gemini"""
    prompt = "Hello, how are you?"
    result = router.analyze_prompt(prompt)
    assert result.provider == "gemini"
    assert result.is_complex == False

def test_provider_fallback():
    """Test fallback behavior when primary provider fails"""
    # Mock primary provider to fail
    # Verify fallback to OpenRouter
```

### Running Tests
```bash
# Complete test suite
pytest

# Specific test category
pytest tests/test_routing.py
pytest tests/test_providers.py

# With verbose output
pytest -v --tb=short

# Test coverage report
pytest --cov=app --cov-report=html
```

### Test Data
- Mock API responses for providers
- Sample prompts of varying complexity
- Database state management with fixtures

## 7. Deployment Strategy

### Local Development
- Direct Python execution with auto-reload
- SQLite for cost tracking
- Local environment variables

### Docker Deployment
```bash
# Development
docker-compose -f docker-compose.dev.yml up

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### Production Considerations
- Use PostgreSQL instead of SQLite for production
- Implement proper secret management
- Add monitoring and health checks
- Configure reverse proxy (nginx) for SSL termination

## 8. Coding Standards

### FastAPI Specific Standards
```python
# Use Pydantic v2 style
from pydantic import BaseModel, Field

class PromptRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000)
    user_id: str | None = Field(None, description="Optional user identifier")

# Use async/await for I/O operations
@app.post("/chat")
async def chat_endpoint(request: PromptRequest):
    result = await router.route_prompt(request.prompt)
    return ChatResponse(**result.dict())
```

### Project-Specific Conventions
- Provider classes must implement `send_message()` method
- All cost calculations in USD cents for precision
- Use dependency injection for API clients
- Log all routing decisions and costs

### Error Handling Pattern
```python
try:
    response = await provider.send_message(prompt)
except ProviderError as e:
    logger.warning(f"Provider {provider.name} failed: {e}")
    return await fallback_provider.send_message(prompt)
```

## 9. Common Tasks & Commands

### Development Tasks
```bash
# Start development server
python app/main.py

# Run tests
pytest

# Check code style (if configured)
flake8 app/ tests/

# Format code (if configured)
black app/ tests/
```

### MCP Server Management
```bash
# Test MCP server directly
python mcp/server.py

# Update Claude Desktop config
# Edit: ~/Library/Application Support/Claude/claude_desktop_config.json
```

### Database Operations
```bash
# View cost tracking data
sqlite3 costs.db "SELECT * FROM api_costs ORDER BY timestamp DESC LIMIT 10;"

# Reset cost tracking (development)
rm costs.db
```

### Debugging Commands
```bash
# Check API health
curl http://localhost:8000/health

# Test routing directly
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain quantum computing"}'
```

## 10. Troubleshooting Tips

### Common Issues

**MCP Server Not Connecting**:
- Verify absolute path in Claude Desktop config
- Check `COST_OPTIMIZER_API_URL` environment variable
- Restart Claude Desktop completely (don't just relaunch)

**Provider API Errors**:
- Verify API keys in `.env` file
- Check provider service status
- Review API rate limits and quotas

**Database Issues**:
- Ensure write permissions in project directory
- Check SQLite file isn't locked by another process

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set in environment
LOG_LEVEL=DEBUG
```

### Health Check Endpoints
- `GET /health` - Service status
- `GET /providers` - Available provider status
- `GET /costs/summary` - Cost tracking summary

### Performance Monitoring
- Monitor response times in logs
- Track token usage patterns
- Review cost per provider in database

---

**Maintenance Note**: Regularly update provider API clients as LLM providers frequently change their interfaces and pricing structures.