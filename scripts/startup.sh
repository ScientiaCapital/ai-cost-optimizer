#!/bin/bash
set -e

echo "Starting AI Cost Optimizer..."

# Check .env exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found"
    echo "Run: cp .env.example .env"
    exit 1
fi

# Start services
docker-compose up -d

# Wait for health checks
echo "Waiting for services to be healthy..."
sleep 15

# Check health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ API is healthy"
else
    echo "✗ API failed to start"
    docker-compose logs api
    exit 1
fi

echo ""
echo "========================================="
echo "AI Cost Optimizer is running!"
echo "========================================="
echo ""
echo "API:      http://localhost:8000"
echo "Docs:     http://localhost:8000/docs"
echo "pgAdmin:  http://localhost:5050"
echo ""
echo "Logs:     docker-compose logs -f"
echo "Stop:     docker-compose down"
echo "========================================="
