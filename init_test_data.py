"""Initialize database with test data for agent testing."""
from app.database import CostTracker

# Initialize database (creates tables)
tracker = CostTracker(db_path='optimizer.db')

# Add some test data
tracker.log_request(
    prompt='What is artificial intelligence?',
    complexity='simple',
    provider='gemini',
    model='gemini-1.5-flash',
    tokens_in=50,
    tokens_out=200,
    cost=0.000075
)

tracker.log_request(
    prompt='Explain the architecture of a microservices system with detailed examples',
    complexity='complex',
    provider='claude',
    model='claude-3-haiku',
    tokens_in=150,
    tokens_out=800,
    cost=0.00125
)

tracker.log_request(
    prompt='Hello world',
    complexity='simple',
    provider='gemini',
    model='gemini-1.5-flash',
    tokens_in=10,
    tokens_out=50,
    cost=0.000015
)

tracker.log_request(
    prompt='Compare JavaScript and Python for web development',
    complexity='complex',
    provider='claude',
    model='claude-3-haiku',
    tokens_in=100,
    tokens_out=600,
    cost=0.00095
)

tracker.log_request(
    prompt='Hi',
    complexity='simple',
    provider='gemini',
    model='gemini-1.5-flash',
    tokens_in=5,
    tokens_out=20,
    cost=0.000008
)

print('✅ Database initialized with test data')
stats = tracker.get_usage_stats()
print(f'Total requests: {stats["overall"]["total_requests"]}')
print(f'Total cost: ${tracker.get_total_cost():.6f}')
print(f'\nBreakdown by provider:')
for provider in stats['by_provider']:
    print(f"  - {provider['provider']}: {provider['request_count']} requests, ${provider['total_cost']:.6f}")
