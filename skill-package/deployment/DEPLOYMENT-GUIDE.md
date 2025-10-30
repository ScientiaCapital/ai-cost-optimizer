# AI Cost Optimizer - RunPod Deployment Guide

This guide covers deploying the AI Cost Optimizer FastAPI service to RunPod for production use.

## Why RunPod?

- **Cost-Effective**: CPU-only workload, no GPU needed ($0.20-0.50/hour)
- **Persistent Storage**: 5GB volume for SQLite database
- **Easy Deployment**: Docker-based with one-click setup
- **HTTPS Endpoints**: Automatic SSL/TLS
- **Auto-restart**: Health checks with automatic recovery

## Prerequisites

- Docker installed locally (for testing)
- Docker Hub account (free)
- RunPod account (https://runpod.io)
- API keys for at least one LLM provider

## Step 1: Prepare Docker Image

### 1.1 Test Locally

From the ai-cost-optimizer directory:

```bash
# Build the image
docker build -t ai-cost-optimizer:latest .

# Test locally
docker run -d \
  -p 8000:8000 \
  -e GOOGLE_API_KEY=your-key-here \
  -e DEFAULT_MONTHLY_BUDGET=100.0 \
  -v $(pwd)/data:/data \
  --name cost-optimizer-test \
  ai-cost-optimizer:latest

# Check health
curl http://localhost:8000/health

# Test completion
curl -X POST http://localhost:8000/v1/complete \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is AI?",
    "max_tokens": 100
  }'

# Check logs
docker logs cost-optimizer-test

# Stop and remove
docker stop cost-optimizer-test
docker rm cost-optimizer-test
```

### 1.2 Push to Docker Hub

```bash
# Login to Docker Hub
docker login

# Tag image
docker tag ai-cost-optimizer:latest \
  your-dockerhub-username/ai-cost-optimizer:latest

# Push to Docker Hub
docker push your-dockerhub-username/ai-cost-optimizer:latest
```

**Note**: Replace `your-dockerhub-username` with your actual Docker Hub username throughout this guide.

## Step 2: Deploy to RunPod

### 2.1 Via Web UI (Recommended)

1. **Login to RunPod**: https://www.runpod.io/
2. **Navigate to Pods**: Click "Pods" in the sidebar
3. **Deploy New Pod**: Click "Deploy" button
4. **Select Pod Type**: Choose "Deploy Custom Container"

**Configuration**:
- **Container Image**: `your-dockerhub-username/ai-cost-optimizer:latest`
- **Container Disk**: 5 GB (for code)
- **Volume Disk**: 5 GB (for persistent data)
- **Volume Mount Path**: `/data`
- **Expose HTTP Ports**: `8000`
- **Container Start Command**: Leave empty (uses CMD from Dockerfile)

**Environment Variables** (click "Environment Variables"):

```
GOOGLE_API_KEY=your-google-api-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
CEREBRAS_API_KEY=your-cerebras-key-here
DEEPSEEK_API_KEY=your-deepseek-key-here
OPENROUTER_API_KEY=your-openrouter-key-here
DEFAULT_MONTHLY_BUDGET=100.00
DATABASE_URL=sqlite:////data/optimizer.db
LOG_LEVEL=INFO
```

**Note**: You only need to configure API keys for providers you want to use. At least one is required.

**Resource Selection**:
- **GPU**: 0 (not needed)
- **CPU**: 2-4 vCPUs recommended
- **RAM**: 4-8 GB recommended
- **Storage**: Community Cloud (cheaper) or Secure Cloud (better uptime)

5. **Deploy**: Click "Deploy" button

### 2.2 Via RunPod CLI

Install RunPod CLI:
```bash
pip install runpod
runpod login
```

Create `pod-config.json`:
```json
{
  "name": "ai-cost-optimizer",
  "image": "your-dockerhub-username/ai-cost-optimizer:latest",
  "docker_args": "",
  "ports": "8000/http",
  "volumeInGb": 5,
  "volumeMountPath": "/data",
  "env": [
    {"key": "GOOGLE_API_KEY", "value": "your-key"},
    {"key": "ANTHROPIC_API_KEY", "value": "your-key"},
    {"key": "DEFAULT_MONTHLY_BUDGET", "value": "100.00"},
    {"key": "DATABASE_URL", "value": "sqlite:////data/optimizer.db"}
  ],
  "containerDiskInGb": 5,
  "cloudType": "COMMUNITY",
  "gpuCount": 0,
  "gpuType": null,
  "minMemoryInGb": 4,
  "minVcpuCount": 2
}
```

Deploy:
```bash
runpod create pod --config pod-config.json
```

### 2.3 Via RunPod API

```python
import requests
import json

RUNPOD_API_KEY = "your-runpod-api-key"

payload = {
    "name": "ai-cost-optimizer",
    "imageName": "your-dockerhub-username/ai-cost-optimizer:latest",
    "dockerArgs": "",
    "ports": "8000/http",
    "volumeInGb": 5,
    "volumeMountPath": "/data",
    "containerDiskInGb": 5,
    "env": [
        {"key": "GOOGLE_API_KEY", "value": "your-key"},
        {"key": "ANTHROPIC_API_KEY", "value": "your-key"},
        {"key": "DEFAULT_MONTHLY_BUDGET", "value": "100.00"}
    ],
    "cloudType": "COMMUNITY",
    "gpuCount": 0,
    "minMemoryInGb": 4,
    "minVcpuCount": 2
}

response = requests.post(
    "https://api.runpod.io/v2/pods",
    json=payload,
    headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"}
)

result = response.json()
print(f"Pod ID: {result['id']}")
print(f"Pod URL: {result.get('url', 'Pending...')}")
```

## Step 3: Verify Deployment

### 3.1 Get Pod URL

Your pod will be assigned a URL like:
```
https://your-pod-id-8000.proxy.runpod.net
```

Find it in:
- RunPod web UI: Pods → Your Pod → "Connect" button
- CLI: `runpod list pods`
- API response: `url` field

### 3.2 Test Endpoints

```bash
POD_URL="https://your-pod-id-8000.proxy.runpod.net"

# Health check
curl $POD_URL/health

# List providers
curl $POD_URL/v1/providers

# List models
curl $POD_URL/v1/models

# Test completion
curl -X POST $POD_URL/v1/complete \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing briefly",
    "max_tokens": 200
  }'

# Check usage
curl "$POD_URL/v1/usage?user_id=default&days=7"
```

### 3.3 Check Logs

**Via Web UI**:
1. Go to Pods → Your Pod
2. Click "Logs" tab
3. View real-time logs

**Via CLI**:
```bash
runpod logs your-pod-id --follow
```

Look for:
```
AI Cost Optimizer started
Providers enabled: ['google', 'anthropic', ...]
```

## Step 4: Configure Claude Desktop

Update your `claude_desktop_config.json`:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ai-cost-optimizer": {
      "command": "python",
      "args": [
        "/absolute/path/to/ai-cost-optimizer/mcp/server.py"
      ],
      "env": {
        "COST_OPTIMIZER_API_URL": "https://your-pod-id-8000.proxy.runpod.net"
      }
    }
  }
}
```

Restart Claude Desktop.

## Step 5: Monitor and Maintain

### 5.1 Monitoring

**Health Checks**:
```bash
# Every 30 seconds, RunPod automatically checks:
curl $POD_URL/health

# Manual metrics check:
curl $POD_URL/metrics
```

**Logs**:
- Stored in `/data/app.log` (persists across restarts)
- View via RunPod web UI or CLI

### 5.2 Scaling

**Vertical Scaling** (more resources):
1. Stop the pod
2. Edit configuration
3. Increase CPU/RAM
4. Restart

**Horizontal Scaling** (multiple instances):
1. Deploy multiple pods
2. Use a load balancer (e.g., Cloudflare)
3. Each pod maintains its own database

### 5.3 Backups

**Database Backup**:
```bash
# From within the pod (via RunPod shell):
cd /data
sqlite3 optimizer.db .dump > backup-$(date +%Y%m%d).sql

# Or copy the entire database:
cp optimizer.db optimizer-backup-$(date +%Y%m%d).db
```

**Download from RunPod**:
1. Use RunPod web UI file browser
2. Navigate to `/data`
3. Download `optimizer.db`

### 5.4 Updates

When you update the code:

```bash
# Rebuild and push
docker build -t ai-cost-optimizer:latest .
docker tag ai-cost-optimizer:latest \
  your-dockerhub-username/ai-cost-optimizer:latest
docker push your-dockerhub-username/ai-cost-optimizer:latest

# In RunPod:
# Option 1: Recreate pod (fresh start, loses non-volume data)
# Option 2: Restart pod (pulls latest image)
```

## Troubleshooting

### Issue: Pod won't start

**Check**:
1. Docker image exists on Docker Hub
2. Image name is correct (including username)
3. Environment variables are set
4. Volume mount path is `/data`

**Logs**:
```bash
runpod logs your-pod-id
```

### Issue: "No providers available"

**Solution**: Add at least one provider API key:
```bash
# Via RunPod UI:
# Pods → Your Pod → Edit → Environment Variables
# Add: GOOGLE_API_KEY=your-key-here

# Then restart the pod
```

### Issue: Database errors

**Solution**: Ensure volume is mounted:
```bash
# In pod shell:
ls -la /data

# Should see:
# drwxr-xr-x  /data
# -rw-r--r--  optimizer.db
```

### Issue: High latency

**Possible causes**:
1. Pod in distant region (check location)
2. Provider API slow (check logs for response times)
3. Insufficient CPU (upgrade to 4+ vCPUs)

**Solutions**:
- Deploy pod closer to your location
- Enable faster providers (Cerebras for speed)
- Upgrade pod resources

### Issue: Costs higher than expected

**Check**:
1. Pod size (Community < $0.50/hour)
2. Storage size (5GB < $0.10/month)
3. Idle time (stop pod when not in use)

**Cost optimization**:
- Use Community Cloud (cheaper)
- Stop pod during off-hours
- Use spot instances if available

## Cost Estimates

**RunPod Costs** (as of 2024):

| Resource | Cost |
|----------|------|
| 2 vCPU, 4GB RAM | ~$0.20/hour ($144/month) |
| 4 vCPU, 8GB RAM | ~$0.40/hour ($288/month) |
| 5GB Persistent Volume | ~$0.10/month |
| Data Transfer | Usually free |

**With spot instances**: 50-70% cheaper

**Total monthly estimate**: $50-150 for 24/7 operation

**Cost saving tips**:
- Use Community Cloud (cheapest)
- Stop pod during off-hours (saves 50-70%)
- Use spot instances when available
- Monitor usage and downscale if possible

## Security Considerations

1. **API Keys**: Never commit to git, use environment variables
2. **HTTPS**: RunPod provides automatic SSL/TLS
3. **Authentication**: Consider adding API key auth to the service
4. **Network**: RunPod pods are isolated by default
5. **Updates**: Keep Docker image updated with security patches

## Production Checklist

Before going live:
- [ ] Test all endpoints work correctly
- [ ] Configure at least 2 provider API keys (redundancy)
- [ ] Set appropriate monthly budget limits
- [ ] Test Claude Desktop integration end-to-end
- [ ] Set up monitoring/alerting
- [ ] Document the pod URL for team
- [ ] Configure backup schedule for database
- [ ] Test health check endpoint
- [ ] Verify logs are being written to `/data/app.log`
- [ ] Test pod restart behavior (should auto-recover)

## Alternative Deployment Options

If RunPod doesn't work for you:

1. **Railway**: https://railway.app (easier, slightly more expensive)
2. **Render**: https://render.com (free tier available)
3. **Fly.io**: https://fly.io (global edge deployment)
4. **DigitalOcean App Platform**: Traditional VM approach
5. **AWS ECS/Fargate**: Enterprise-grade, more complex
6. **Google Cloud Run**: Serverless containers

All use the same Docker image - just different deployment processes.

## Support

- **Issues**: https://github.com/yourusername/ai-cost-optimizer/issues
- **RunPod Docs**: https://docs.runpod.io
- **Discord**: [Your Server]

## Next Steps

After successful deployment:
1. Update Claude Desktop config with your pod URL
2. Test all 5 MCP tools work correctly
3. Monitor costs and usage
4. Share with team members
5. Consider adding more providers for redundancy
