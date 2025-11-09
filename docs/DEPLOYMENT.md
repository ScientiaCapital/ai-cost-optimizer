# Production Deployment Guide

**AI Cost Optimizer with Production Feedback Loop**

This guide covers deploying and operating the AI Cost Optimizer in production with the feedback loop enabled.

---

## Prerequisites

### Required
- Docker & Docker Compose installed
- At least one AI provider API key:
  - Google Gemini API key (recommended, free tier available)
  - Anthropic Claude API key
  - OpenRouter API key
- 2GB+ available RAM
- 5GB+ available disk space

### Optional (for production)
- Domain name with SSL certificate
- Nginx or similar reverse proxy
- Monitoring tools (Prometheus, Grafana)
- Log aggregation system

---

## First-Time Setup

### 1. Clone and Configure

```bash
# Clone repository
git clone <repository-url>
cd ai-cost-optimizer

# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 2. Configure Environment Variables

Edit `.env` with your values:

```bash
# Required: At least one provider
GOOGLE_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_claude_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Database (PostgreSQL in production)
POSTGRES_USER=optimizer
POSTGRES_PASSWORD=change_this_secure_password
POSTGRES_DB=cost_optimizer
DATABASE_URL=postgresql://optimizer:change_this_secure_password@db:5432/cost_optimizer

# pgAdmin (Web UI for database)
PGADMIN_DEFAULT_EMAIL=admin@optimizer.local
PGADMIN_DEFAULT_PASSWORD=change_this_admin_password

# Application settings
LOG_LEVEL=INFO
ENVIRONMENT=production
```

**Security Note**: Use strong, unique passwords for production!

### 3. Run Database Migrations

```bash
# Start database only
docker-compose up -d db

# Wait for PostgreSQL to be ready (15-30 seconds)
sleep 30

# Run migrations
docker-compose run --rm api python -m app.database.migrate
```

**Expected output:**
```
Running database migrations...
✓ Created routing_requests table
✓ Created production_feedback table
✓ Created learning_overrides table
Migration complete!
```

### 4. Start All Services

```bash
# Start everything
docker-compose up -d

# Check service health
docker-compose ps
```

**Expected services:**
- `api` - FastAPI application (port 8000)
- `db` - PostgreSQL database (port 5432)
- `pgadmin` - Database admin UI (port 5050)

### 5. Verify Deployment

```bash
# Check API health
curl http://localhost:8000/health

# Expected: {"status": "healthy", "providers": [...]}

# View API documentation
open http://localhost:8000/docs

# Access pgAdmin (optional)
open http://localhost:5050
```

---

## Daily Operations

### Starting Services

**Option 1: Convenience script**
```bash
./scripts/startup.sh
```

**Option 2: Docker Compose directly**
```bash
docker-compose up -d
docker-compose logs -f  # Follow logs
```

### Stopping Services

**Option 1: Convenience script**
```bash
./scripts/shutdown.sh
```

**Option 2: Docker Compose directly**
```bash
# Stop but keep data
docker-compose down

# Stop and remove volumes (DELETES ALL DATA!)
docker-compose down -v
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# API only
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api

# Since specific time
docker-compose logs --since 2024-01-15T10:00:00 api
```

### Restarting Services

```bash
# Restart all
docker-compose restart

# Restart API only
docker-compose restart api

# Rebuild and restart (after code changes)
docker-compose up -d --build
```

---

## Database Management

### Accessing pgAdmin

1. Open browser: `http://localhost:5050`
2. Login with credentials from `.env`:
   - Email: `PGADMIN_DEFAULT_EMAIL`
   - Password: `PGADMIN_DEFAULT_PASSWORD`

3. Add server connection:
   - Host: `db`
   - Port: `5432`
   - Database: `cost_optimizer`
   - Username: `POSTGRES_USER`
   - Password: `POSTGRES_PASSWORD`

### Running SQL Queries

**Via pgAdmin:**
Use the Query Tool in pgAdmin web interface

**Via Docker:**
```bash
# Open PostgreSQL shell
docker-compose exec db psql -U optimizer -d cost_optimizer

# Run query directly
docker-compose exec db psql -U optimizer -d cost_optimizer -c "SELECT COUNT(*) FROM production_feedback;"
```

### Common Database Queries

```sql
-- Check feedback count
SELECT COUNT(*) FROM production_feedback;

-- View recent feedback
SELECT * FROM production_feedback
ORDER BY created_at DESC
LIMIT 10;

-- Feedback quality breakdown
SELECT quality_score, COUNT(*) as count
FROM production_feedback
GROUP BY quality_score
ORDER BY quality_score;

-- Check learning overrides
SELECT * FROM learning_overrides
WHERE confidence_level = 'high';

-- View routing decisions
SELECT provider, model, COUNT(*) as count
FROM routing_requests
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY provider, model
ORDER BY count DESC;
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Feedback summary
curl http://localhost:8000/admin/feedback/summary

# Learning status
curl http://localhost:8000/admin/learning/status
```

### Feedback Summary Dashboard

```bash
# View feedback metrics
curl http://localhost:8000/admin/feedback/summary | jq
```

**Example output:**
```json
{
  "total_feedback": 150,
  "avg_quality_score": 4.2,
  "by_model": {
    "gemini-1.5-flash": {"count": 80, "avg_score": 4.5},
    "claude-3-5-haiku-20241022": {"count": 70, "avg_score": 3.9}
  },
  "by_query_pattern": {
    "code": {"count": 60, "avg_score": 4.6},
    "creative": {"count": 45, "avg_score": 4.0}
  }
}
```

### Learning Status

```bash
# Check learning system health
curl http://localhost:8000/admin/learning/status | jq
```

**Example output:**
```json
{
  "total_overrides": 5,
  "confidence_distribution": {
    "high": 3,
    "medium": 2,
    "low": 0
  },
  "last_retrain": "2024-01-15T14:30:00Z",
  "recommendation_coverage": "32.5%"
}
```

### Manual Retraining

**Dry run (preview changes):**
```bash
curl -X POST "http://localhost:8000/admin/learning/retrain?dry_run=true" | jq
```

**Actual retrain:**
```bash
curl -X POST "http://localhost:8000/admin/learning/retrain?dry_run=false" | jq
```

**With thresholds:**
```bash
curl -X POST "http://localhost:8000/admin/learning/retrain?dry_run=false&min_samples=15&confidence_threshold=0.75" | jq
```

### Metrics to Monitor

1. **Feedback Volume**: Should have steady stream (target: 10+ per day minimum)
2. **Quality Scores**: Average should be 3.5+ (on 1-5 scale)
3. **Learning Coverage**: Percentage of patterns with overrides (target: 20-40%)
4. **Confidence Distribution**: Most overrides should be high or medium confidence
5. **Error Rates**: Monitor API logs for provider failures

---

## Backup & Recovery

### Database Backups

**Automated backup (cron):**
```bash
# Add to crontab
0 2 * * * docker-compose exec -T db pg_dump -U optimizer cost_optimizer | gzip > /backups/optimizer_$(date +\%Y\%m\%d).sql.gz
```

**Manual backup:**
```bash
# Backup database
docker-compose exec -T db pg_dump -U optimizer cost_optimizer > backup_$(date +%Y%m%d).sql

# Backup with compression
docker-compose exec -T db pg_dump -U optimizer cost_optimizer | gzip > backup_$(date +%Y%m%d).sql.gz
```

**Restore from backup:**
```bash
# Stop API
docker-compose stop api

# Restore database
gunzip -c backup_20240115.sql.gz | docker-compose exec -T db psql -U optimizer cost_optimizer

# Restart API
docker-compose start api
```

### Configuration Backups

```bash
# Backup important files
tar -czf optimizer_config_$(date +%Y%m%d).tar.gz \
  .env \
  docker-compose.yml \
  nginx.conf
```

---

## Troubleshooting

### API Won't Start

**Check logs:**
```bash
docker-compose logs api
```

**Common issues:**
1. **Missing API keys**: Check `.env` file has at least one provider key
2. **Database connection failed**: Ensure `db` service is running
3. **Port already in use**: Change port in `docker-compose.yml`

**Solution:**
```bash
# Restart everything
docker-compose down
docker-compose up -d
```

### Database Connection Errors

**Symptoms:**
- API logs show "could not connect to server"
- `/health` endpoint returns database error

**Check database:**
```bash
docker-compose ps db
docker-compose logs db
```

**Fix:**
```bash
# Restart database
docker-compose restart db

# Wait for startup
sleep 15

# Restart API
docker-compose restart api
```

### Feedback Not Recording

**Check:**
1. Verify `request_id` exists in `routing_requests` table
2. Check API logs for validation errors
3. Verify database migrations ran

**Debug:**
```bash
# Check routing_requests
docker-compose exec db psql -U optimizer -d cost_optimizer -c "SELECT COUNT(*) FROM routing_requests;"

# Check recent requests
docker-compose exec db psql -U optimizer -d cost_optimizer -c "SELECT id, created_at FROM routing_requests ORDER BY created_at DESC LIMIT 5;"

# Submit test feedback
curl -X POST http://localhost:8000/production/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "valid_request_id_here",
    "quality_score": 4,
    "is_correct": true
  }'
```

### Retraining Returns No Changes

**Normal if:**
- Not enough feedback samples (need 10+ per pattern-model)
- Feedback doesn't meet confidence threshold
- Feedback quality too variable

**Check:**
```bash
# View feedback counts by pattern
curl http://localhost:8000/admin/feedback/summary | jq '.by_query_pattern'

# Try lower thresholds
curl -X POST "http://localhost:8000/admin/learning/retrain?dry_run=true&min_samples=5&confidence_threshold=0.65" | jq
```

### High Memory Usage

**Check container stats:**
```bash
docker stats
```

**If API using > 1GB:**
1. Check for memory leaks in logs
2. Restart API: `docker-compose restart api`
3. Consider increasing container memory limit in `docker-compose.yml`

### Provider API Failures

**Check provider status:**
```bash
curl http://localhost:8000/health | jq '.providers'
```

**If provider failing:**
1. Verify API key is correct in `.env`
2. Check provider service status page
3. Review rate limits (may need to wait)
4. System will fall back to OpenRouter automatically

---

## Production Considerations

### Security Hardening

1. **Environment Variables:**
   - Never commit `.env` to version control
   - Use secrets management (AWS Secrets Manager, Vault)
   - Rotate API keys regularly

2. **Database:**
   - Use strong passwords (20+ characters)
   - Enable SSL/TLS for PostgreSQL connections
   - Restrict network access to database port

3. **API:**
   - Enable authentication/authorization
   - Use HTTPS only (configure reverse proxy)
   - Implement rate limiting
   - Set up CORS policies

4. **Docker:**
   - Don't run containers as root
   - Use specific image versions (not `latest`)
   - Scan images for vulnerabilities

### Reverse Proxy (Nginx)

**Example nginx configuration:**
```nginx
server {
    listen 80;
    server_name optimizer.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name optimizer.example.com;

    ssl_certificate /etc/ssl/certs/optimizer.crt;
    ssl_certificate_key /etc/ssl/private/optimizer.key;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Monitoring & Alerting

**Recommended metrics:**
- API response times (p50, p95, p99)
- Error rates by endpoint
- Provider API latencies
- Database query performance
- Feedback submission rate
- Learning override count

**Tools:**
- Prometheus for metrics collection
- Grafana for dashboards
- Alertmanager for alerts
- ELK stack for log aggregation

### Scaling

**Horizontal scaling:**
```yaml
# docker-compose.yml
services:
  api:
    deploy:
      replicas: 3
```

**Load balancing:**
- Use nginx or HAProxy
- Consider cloud load balancers (AWS ALB, GCP Load Balancer)

**Database:**
- Use managed PostgreSQL (AWS RDS, GCP Cloud SQL)
- Enable read replicas for analytics
- Set up automated backups

---

## Automated Retraining (Optional)

### Daily Retraining Cron Job

```bash
# Add to crontab (runs at 3 AM daily)
0 3 * * * curl -X POST "http://localhost:8000/admin/learning/retrain?dry_run=false" >> /var/log/optimizer_retrain.log 2>&1
```

### Monitoring Retraining

```bash
# View retraining log
tail -f /var/log/optimizer_retrain.log

# Check last retrain time
curl http://localhost:8000/admin/learning/status | jq '.last_retrain'
```

---

## Next Steps

After deployment:

1. **Submit test requests** to verify routing works
2. **Monitor initial feedback** (first 50-100 responses)
3. **Run first retraining** after 1-2 weeks (100+ feedback samples)
4. **Review learning overrides** to ensure quality
5. **Set up monitoring dashboards**
6. **Configure automated backups**
7. **Document any custom configurations**

---

## Support & Resources

- **API Documentation**: `http://localhost:8000/docs`
- **Project README**: `README.md`
- **Architecture Documentation**: `docs/PRODUCTION_FEEDBACK_LOOP.md`
- **Issue Tracker**: GitHub Issues

---

**Version**: 2.0.0
**Last Updated**: 2024-01-15
