# Cost Optimization Agent

> AI Spending Analyst powered by Claude Agent SDK

An intelligent agent that analyzes your AI/LLM usage patterns, identifies cost-saving opportunities, and provides actionable recommendations for optimizing spending.

## Features

### 🔍 **Analysis Tools**
- **Usage Statistics**: Total costs, request counts, provider breakdowns
- **Cost Patterns**: Spending trends, peak usage times, daily analysis
- **Recent Requests**: Query-level analysis for pattern identification

### 💰 **Optimization Tools**
- **Smart Recommendations**: Prioritized opportunities with estimated savings
- **Cache Analysis**: Hit rates, savings tracking, popular queries
- **Provider Comparison**: Cost and quality metrics across providers

### 🎯 **Key Capabilities**
- Natural language queries ("How much did I spend this week?")
- Actionable, data-driven recommendations
- Business-friendly explanations with specific metrics
- Interactive session mode for deep analysis

## Quick Start

### Prerequisites

1. **Python 3.10+** (Check: `python3 --version`)
2. **Anthropic API Key** ([Get one here](https://console.anthropic.com/))
3. **Parent project setup** (AI Cost Optimizer FastAPI service with data)

### Installation

```bash
# Navigate to agent directory
cd agent

# Activate virtual environment (if not already active)
source .venv/bin/activate

# Install dependencies (already done during setup)
pip install -r requirements.txt
```

### Set API Key

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY='your-api-key-here'

# Or add to ~/.zshrc or ~/.bashrc for persistence:
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

## Usage

### Interactive Session Mode (Recommended)

```bash
python cost_optimizer_agent.py
```

This starts an interactive conversation with the agent:

```
🤖 Cost Optimization Agent (Session Mode)
============================================================
Type 'exit' or 'quit' to end the session

You: How much have I spent this week?
🤖 Agent: Let me analyze your spending for the past week...
[Agent analyzes and responds]

You: Where can I save money?
🤖 Agent: I've identified 3 optimization opportunities...
[Agent provides recommendations]

You: exit
👋 Session ended. Happy optimizing!
```

### Single Query Mode

For one-off questions:

```bash
python cost_optimizer_agent.py "How much did I spend this month?"
python cost_optimizer_agent.py "Analyze my last 100 queries"
python cost_optimizer_agent.py "Compare provider costs"
```

## Example Queries

### Cost Analysis
```
"How much have I spent this week?"
"What's my average cost per request?"
"Show me spending trends for the last 30 days"
"What was my most expensive day?"
```

### Optimization
```
"Where can I save money?"
"Generate cost optimization recommendations"
"What's my biggest cost driver?"
"How can I reduce my Claude costs?"
```

### Cache Analysis
```
"Is my cache working well?"
"How much am I saving with caching?"
"What are my most popular cached queries?"
"What's my cache hit rate?"
```

### Provider Comparison
```
"Compare Gemini vs Claude costs"
"Which provider am I using most?"
"Show me provider performance"
"What's the cost difference between providers?"
```

### Deep Analysis
```
"Analyze my last 100 queries for patterns"
"Find inefficiencies in my recent requests"
"Why are my costs increasing?"
"Review my complexity distribution"
```

## Architecture

### File Structure

```
agent/
├── cost_optimizer_agent.py    # Main agent application
├── tools.py                    # 6 custom analysis tools
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── .venv/                      # Virtual environment
```

### Custom Tools

The agent has 6 specialized tools:

1. **`get_usage_stats()`** - Overall usage and cost statistics
2. **`analyze_cost_patterns(days)`** - Spending trends over time
3. **`get_recommendations()`** - Prioritized optimization opportunities
4. **`query_recent_requests(limit)`** - Recent request analysis
5. **`check_cache_effectiveness()`** - Cache performance metrics
6. **`compare_providers()`** - Provider cost/quality comparison

### Agent Capabilities

- **Natural Language Understanding**: Ask questions in plain English
- **Multi-Tool Reasoning**: Combines multiple tools for complex analysis
- **Context Awareness**: Remembers conversation history in session mode
- **Data-Driven**: All recommendations backed by actual usage data
- **Cost-Conscious**: Uses Claude 3.5 Sonnet for optimal quality/cost

## Advanced Usage

### Custom Time Ranges

```bash
python cost_optimizer_agent.py "Analyze cost patterns for the last 14 days"
```

The agent will use `analyze_cost_patterns(days=14)` automatically.

### Targeted Analysis

```bash
python cost_optimizer_agent.py "Analyze my last 50 Claude requests"
```

The agent combines `query_recent_requests(50)` with provider filtering.

### Comprehensive Review

In interactive mode:
```
You: Give me a complete cost audit
Agent: [Uses multiple tools]
  1. Overall stats
  2. Provider comparison
  3. Cache effectiveness
  4. Optimization recommendations
```

## Troubleshooting

### "ANTHROPIC_API_KEY not found"

```bash
# Set the API key
export ANTHROPIC_API_KEY='your-key'

# Verify it's set
echo $ANTHROPIC_API_KEY
```

### "No module named 'app'"

The agent imports from `../app/`. Make sure you're running from the `agent/` directory and the parent project structure is intact.

### "Database not found"

The agent looks for `../optimizer.db`. Make sure:
1. The FastAPI service has been run at least once
2. You have some usage data in the database
3. The database file exists at the project root

### "Virtual environment not activated"

```bash
cd agent
source .venv/bin/activate
```

## Tips for Best Results

1. **Use Session Mode** for exploratory analysis
2. **Be Specific** in your questions for better responses
3. **Request Comparisons** to understand trade-offs
4. **Ask for Recommendations** regularly to stay optimized
5. **Provide Context** (e.g., "last week", "high-cost queries")

## Performance

- **Response Time**: 2-10 seconds depending on query complexity
- **Tool Calls**: Agent may use 1-3 tools per query
- **Cost**: ~$0.001-0.01 per query (uses Claude 3.5 Sonnet)
- **Data Access**: Direct SQLite queries for fast analysis

## Next Steps

### Integrate with Your Workflow

```python
# Use in your own Python scripts
from cost_optimizer_agent import run_agent

# Single query
await run_agent("What's my total spend?")

# Session
await run_agent("Let's analyze", session_mode=True)
```

### Scheduled Reports

Create a cron job for daily/weekly cost reports:

```bash
# Daily cost report at 9 AM
0 9 * * * cd /path/to/agent && python cost_optimizer_agent.py "Generate daily cost report" >> reports.log
```

### API Integration

Build a web interface that calls the agent for cost dashboards.

## Support

For issues related to:
- **Agent functionality**: Check this README and tool implementations
- **Claude Agent SDK**: https://docs.claude.com/en/api/agent-sdk/python
- **AI Cost Optimizer**: See parent project README

## What's Next?

Consider these enhancements:
- 📊 **Export reports** to PDF/CSV
- 📧 **Email alerts** for budget thresholds
- 📈 **Visualization** with charts and graphs
- 🔄 **Auto-optimization** that updates routing rules
- 👥 **Multi-user** analysis for team usage

---

**Built with Claude Agent SDK v0.1.6**

Need help? Run the agent and ask: "What can you help me with?"
