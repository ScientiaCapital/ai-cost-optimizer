# AI Cost Optimizer - Claude Desktop Skill Package

This package contains everything needed to use the AI Cost Optimizer with Claude Desktop.

## Package Contents

```
skill-package/
├── SKILL.md                      # Marketplace manifest and documentation
├── README.md                     # This file
├── ICON-REQUIREMENTS.md          # Instructions for creating the skill icon
├── mcp/                          # MCP server for Claude Desktop integration
│   ├── mcp.json                  # Server manifest
│   ├── server.py                 # MCP server implementation
│   ├── requirements.txt          # Python dependencies
│   ├── README.md                 # Setup instructions
│   └── .env.example              # Environment template
├── deployment/                   # Production deployment files
│   ├── Dockerfile                # Container definition
│   ├── .dockerignore             # Docker build exclusions
│   ├── runpod_config.json        # RunPod configuration
│   └── DEPLOYMENT-GUIDE.md       # Complete deployment guide
└── screenshots/                  # Marketplace screenshots (to be added)
    └── README.md                 # Screenshot guidelines
```

## Quick Start

### Option 1: Install from Claude Desktop Marketplace (Recommended)

1. Open Claude Desktop
2. Go to Skills Marketplace
3. Search for "AI Cost Optimizer"
4. Click "Install"
5. Follow the setup wizard

### Option 2: Manual Installation from Package

1. **Extract this package** to a permanent location
2. **Deploy the FastAPI service**:
   - Local: See main repository README
   - Cloud: See `deployment/DEPLOYMENT-GUIDE.md`
3. **Install MCP dependencies**:
   ```bash
   cd mcp
   pip install -r requirements.txt
   ```
4. **Configure Claude Desktop**:
   Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "ai-cost-optimizer": {
         "command": "python",
         "args": ["/absolute/path/to/skill-package/mcp/server.py"],
         "env": {
           "COST_OPTIMIZER_API_URL": "http://localhost:8000"
         }
       }
     }
   }
   ```
5. **Restart Claude Desktop**

## What's Included

### 1. MCP Server (`mcp/`)

The Model Context Protocol server that enables Claude Desktop to interact with the AI Cost Optimizer API.

**Features**:
- 5 tools: complete_prompt, check_model_costs, get_recommendation, query_usage, set_budget
- Intelligent error handling
- Connection management
- Formatted responses

**Setup**: See `mcp/README.md`

### 2. Deployment Files (`deployment/`)

Everything needed to deploy to RunPod or other cloud platforms:

- **Dockerfile**: Container definition for the FastAPI service
- **.dockerignore**: Optimizes Docker build
- **runpod_config.json**: RunPod-specific configuration
- **DEPLOYMENT-GUIDE.md**: Step-by-step deployment instructions

### 3. Marketplace Assets

- **SKILL.md**: Complete marketplace listing with features, pricing, examples
- **ICON-REQUIREMENTS.md**: Guidelines for creating the 512x512 icon
- **screenshots/README.md**: Instructions for capturing demo screenshots

## System Requirements

### For MCP Server (Local)

- Python 3.10 or higher
- 50MB disk space
- Network access to AI Cost Optimizer API

### For FastAPI Service (Deployment)

**Local Development**:
- Python 3.10+
- 100MB disk space
- At least one LLM provider API key

**RunPod Production**:
- Docker Hub account (free)
- RunPod account (free signup)
- 2-4 vCPU, 4-8GB RAM recommended
- 5GB persistent storage
- Cost: ~$50-150/month for 24/7 operation

## Configuration

### API Keys

You'll need at least one provider API key. Options:

**Free Tier**:
- Google Gemini: 1M requests/month free

**Paid Options**:
- Anthropic Claude: $3-15/M tokens
- Cerebras: $0.10-0.60/M tokens
- DeepSeek: $0.14-0.28/M tokens
- OpenRouter: Gateway to 100+ models
- HuggingFace: Open models

Configure in the main service's `.env` file (not included in this package).

### Environment Variables

**For MCP Server** (in Claude Desktop config):
```json
"env": {
  "COST_OPTIMIZER_API_URL": "http://localhost:8000",
  "COST_OPTIMIZER_API_KEY": ""
}
```

**For FastAPI Service** (in service `.env`):
```bash
GOOGLE_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
DEFAULT_MONTHLY_BUDGET=100.00
```

## Usage Examples

Once installed, use these commands in Claude Desktop:

### Smart Routing
```
Please use the cost optimizer to answer: "What is machine learning?"
```

### Check Costs
```
Show me all available models and their pricing
```

### Get Recommendations
```
Analyze this prompt and recommend a model:
"Design a distributed system architecture"
```

### Monitor Spending
```
What's my AI spending this month?
```

### Set Budget
```
Set my monthly AI budget to $50 with alerts at 50%, 80%, and 90%
```

## Troubleshooting

### "Cannot connect to AI Cost Optimizer service"

**Cause**: FastAPI service not running
**Solution**: Start the service or verify the URL in MCP config

### "MCP server not appearing in Claude Desktop"

**Causes**:
1. Incorrect path in config (must be absolute)
2. Claude Desktop not restarted
3. Python not in PATH

**Solutions**:
1. Use absolute path: `/Users/you/path/to/server.py`
2. Completely quit and restart Claude Desktop
3. Test: `python --version` in terminal

### "No providers available"

**Cause**: No API keys configured in service
**Solution**: Add at least one API key to service `.env` file

## File Manifest

**This Package** (ready to use):
- ✅ MCP server code
- ✅ Deployment configurations
- ✅ Documentation
- ⚠️ Icon (needs creation - see ICON-REQUIREMENTS.md)
- ⚠️ Screenshots (needs creation - see screenshots/README.md)

**Not Included** (from main repository):
- FastAPI service code (router.py, main.py, etc.)
- Provider implementations
- Cost tracking logic
- Budget management code

**Reason**: The package contains integration files only. The main service should be deployed from the full repository.

## Getting the Full Project

This skill package is for Claude Desktop integration only. To deploy the FastAPI service, you need the full repository:

```bash
git clone https://github.com/yourusername/ai-cost-optimizer.git
```

Or download the complete project from:
https://github.com/yourusername/ai-cost-optimizer

## Support

- **GitHub Issues**: https://github.com/yourusername/ai-cost-optimizer/issues
- **Documentation**: Full README in main repository
- **Deployment Help**: See `deployment/DEPLOYMENT-GUIDE.md`
- **MCP Setup**: See `mcp/README.md`

## License

MIT License - Free for personal and commercial use

## Version History

### 1.0.0 (Current)
- Initial release
- 5 MCP tools for Claude Desktop
- RunPod deployment support
- Budget management and cost tracking
- Support for 8 LLM providers

## Next Steps

1. **Before Marketplace Submission**:
   - [ ] Create icon.png (512x512) - see ICON-REQUIREMENTS.md
   - [ ] Capture 3-5 screenshots - see screenshots/README.md
   - [ ] Update author information in SKILL.md
   - [ ] Update GitHub URLs throughout
   - [ ] Test installation process end-to-end

2. **For Testing**:
   - [ ] Deploy FastAPI service (local or RunPod)
   - [ ] Install MCP server in Claude Desktop
   - [ ] Test all 5 tools work correctly
   - [ ] Verify cost tracking and budget management

3. **For Distribution**:
   - [ ] Create final ZIP: `ai-cost-optimizer-skill-v1.0.0.zip`
   - [ ] Submit to Claude Desktop Skills Marketplace
   - [ ] Share with early adopters for feedback

## Feedback Welcome

We're constantly improving! Please report:
- Bugs or issues
- Feature requests
- Documentation improvements
- Integration suggestions

Thank you for using AI Cost Optimizer! 🚀
