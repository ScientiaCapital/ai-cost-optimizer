#!/usr/bin/env python3
"""Generate realistic training data for learning intelligence system.

Creates 100 diverse queries across 6 patterns and populates the database
with realistic performance metrics.
"""

import sqlite3
import random
import hashlib
from datetime import datetime, timedelta

# Training queries by pattern (15-20 per pattern for high confidence)
TRAINING_QUERIES = {
    "code": [
        "Debug this Python function that's throwing a TypeError",
        "Write a function to validate email addresses using regex",
        "Refactor this nested loop to improve performance",
        "Explain why this async function isn't awaiting properly",
        "Create a binary search tree implementation in Python",
        "Fix the memory leak in this JavaScript event listener",
        "Write unit tests for this API endpoint handler",
        "Implement a decorator for rate limiting API calls",
        "Convert this callback-based code to use Promises",
        "Debug why this SQL query is returning duplicate rows",
        "Optimize this database query with proper indexing",
        "Write a recursive function to traverse a tree structure",
        "Fix the race condition in this concurrent code",
        "Implement lazy loading for this image gallery",
        "Create a custom hook for form validation in React",
        "Debug this CSS flexbox layout issue",
        "Write a function to merge two sorted arrays efficiently",
        "Implement a caching layer using Redis",
        "Fix the CORS error in this API request",
        "Create a responsive navigation menu with dropdown",
    ],
    "explanation": [
        "Explain how garbage collection works in Python",
        "What is the difference between let, const, and var?",
        "How do HTTP cookies work?",
        "Explain the MVC architecture pattern",
        "What is the difference between SQL and NoSQL databases?",
        "How does public key cryptography work?",
        "Explain how Docker containers differ from virtual machines",
        "What is the CAP theorem in distributed systems?",
        "How do browser engines render web pages?",
        "Explain the difference between authentication and authorization",
        "What is middleware in web frameworks?",
        "How does OAuth 2.0 work?",
        "Explain event bubbling in JavaScript",
        "What are microservices and when should you use them?",
        "How does HTTPS encryption work?",
        "Explain the difference between stack and heap memory",
        "What is dependency injection?",
        "How do content delivery networks (CDNs) work?",
        "Explain REST API design principles",
        "What is the difference between TCP and UDP?",
    ],
    "creative": [
        "Write a haiku about debugging code at 3am",
        "Create a funny error message for a 404 page",
        "Write a poem about the beauty of clean code",
        "Generate creative variable names for a weather app",
        "Write a humorous commit message for fixing a typo",
        "Create a story about a bug that became sentient",
        "Design a mascot for a code review tool",
        "Write a limerick about merge conflicts",
        "Create an analogy to explain recursion to a 5-year-old",
        "Write a dramatic monologue from the perspective of a forgotten TODO comment",
        "Generate creative team names for a hackathon",
        "Write a love letter from a developer to their IDE",
        "Create a superhero backstory for a CI/CD pipeline",
        "Write a mystery story where the killer is a memory leak",
        "Generate creative names for Git branches",
        "Write a ballad about the tragedy of production bugs",
        "Create a fantasy world where programming languages are kingdoms",
        "Write a sitcom scene about a standup meeting gone wrong",
        "Generate creative placeholder text for a design mockup",
        "Write a eulogy for deprecated code",
    ],
    "analysis": [
        "Analyze the trade-offs between REST and GraphQL APIs",
        "Compare React, Vue, and Angular for a large enterprise app",
        "Evaluate the security risks of this authentication approach",
        "Analyze why this website has slow load times",
        "Compare SQL vs NoSQL for a social media platform",
        "Evaluate the pros and cons of microservices architecture",
        "Analyze the performance bottlenecks in this application",
        "Compare different state management solutions for React",
        "Evaluate the scalability of this database design",
        "Analyze the accessibility issues in this website",
        "Compare serverless vs traditional hosting for this use case",
        "Evaluate the code quality and maintainability of this project",
        "Analyze the security vulnerabilities in this API",
        "Compare different authentication strategies for mobile apps",
        "Evaluate the testing coverage and quality of this codebase",
        "Analyze the cost implications of this cloud architecture",
        "Compare monorepo vs polyrepo for a growing team",
        "Evaluate the SEO performance of this website",
        "Analyze the data flow and state management in this app",
        "Compare different caching strategies for this API",
    ],
    "factual": [
        "What is the latest stable version of Node.js?",
        "List the SOLID principles in software engineering",
        "What are the HTTP status codes in the 400 range?",
        "What are the main features of Python 3.12?",
        "List the different types of CSS selectors",
        "What are the core principles of Agile development?",
        "What are the main SQL JOIN types?",
        "List the HTTP methods and their purposes",
        "What are the JavaScript primitive data types?",
        "What are the main Git commands for version control?",
        "List the main AWS services for web hosting",
        "What are the different types of database indexes?",
        "What are the main principles of RESTful API design?",
        "List the common design patterns in object-oriented programming",
        "What are the main features of TypeScript?",
        "What are the different HTTP headers for caching?",
        "List the main testing types (unit, integration, e2e)",
        "What are the ACID properties in databases?",
        "What are the main CSS layout techniques?",
        "List the common web security vulnerabilities (OWASP Top 10)",
    ],
    "reasoning": [
        "Why would you choose a NoSQL database over SQL for this use case?",
        "Should we refactor this monolith into microservices? Why or why not?",
        "Is it worth implementing server-side rendering for this app?",
        "Should we use TypeScript or stick with JavaScript for this project?",
        "Why is this API endpoint slow and how can we fix it?",
        "Should we cache this data on the client or server side?",
        "Is it better to use a framework or build from scratch for this project?",
        "Why is our database query getting slower as data grows?",
        "Should we invest in automated testing or manual QA?",
        "Is cloud hosting worth the cost for our startup?",
        "Why is our website not ranking well in search results?",
        "Should we build a native app or use a cross-platform framework?",
        "Is it worth migrating from REST to GraphQL?",
        "Why are users abandoning our checkout flow?",
        "Should we prioritize performance or feature development?",
        "Is serverless architecture right for our workload?",
        "Why is our deployment pipeline taking so long?",
        "Should we use a CDN for our static assets?",
        "Is it worth implementing real-time features for this app?",
        "Why is technical debt accumulating and how do we address it?",
    ]
}

# Model configurations with realistic performance characteristics
MODELS = {
    "openrouter/deepseek-chat": {
        "tier": "Economy Tier",
        "quality_range": (0.75, 0.85),  # Good quality
        "cost_per_1k": 0.00014,  # Very cheap
        "best_for": ["code", "reasoning", "factual"]
    },
    "openrouter/qwen-2-72b": {
        "tier": "Premium Tier",
        "quality_range": (0.82, 0.92),  # Excellent quality
        "cost_per_1k": 0.00047,  # Moderate cost
        "best_for": ["analysis", "reasoning", "explanation"]
    },
    "openrouter/deepseek-coder": {
        "tier": "Economy Tier",
        "quality_range": (0.85, 0.95),  # Excellent for code
        "cost_per_1k": 0.00014,  # Very cheap
        "best_for": ["code"]
    },
    "google/gemini-flash": {
        "tier": "Standard Tier",
        "quality_range": (0.70, 0.80),  # Decent quality
        "cost_per_1k": 0.00012,  # Cheap
        "best_for": ["factual", "explanation", "creative"]
    },
    "claude/claude-3-haiku": {
        "tier": "Premium Tier",
        "quality_range": (0.80, 0.90),  # High quality
        "cost_per_1k": 0.00095,  # More expensive
        "best_for": ["analysis", "creative", "explanation"]
    },
    "openrouter/qwen-2.5-math": {
        "tier": "Specialty Tier",
        "quality_range": (0.88, 0.98),  # Excellent for math/reasoning
        "cost_per_1k": 0.00024,  # Reasonable cost
        "best_for": ["reasoning"]
    }
}

def calculate_quality_score(model_config, pattern, is_best_pattern):
    """Calculate quality score based on model and pattern match."""
    min_q, max_q = model_config["quality_range"]

    if is_best_pattern:
        # Higher quality for best patterns
        return random.uniform(max_q - 0.05, max_q)
    else:
        # Good but not optimal
        return random.uniform(min_q, max_q - 0.1)

def calculate_cost(model_config, prompt_length):
    """Calculate cost based on model and prompt length."""
    estimated_tokens = prompt_length * 0.75  # Rough estimation
    total_tokens = estimated_tokens * 2  # Input + output
    return (total_tokens / 1000) * model_config["cost_per_1k"]

def generate_cache_key(prompt, model):
    """Generate cache key for response."""
    return hashlib.sha256(f"{prompt}:{model}".encode()).hexdigest()

def populate_database(db_path: str = "optimizer.db"):
    """Populate database with realistic training data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Tables already exist from the main application
    # Just populate with data

    total_inserted = 0
    base_time = datetime.now() - timedelta(days=30)

    for pattern, queries in TRAINING_QUERIES.items():
        print(f"\n📝 Generating {pattern} queries...")

        for i, prompt in enumerate(queries):
            # Select appropriate model for this pattern
            best_models = [m for m, cfg in MODELS.items() if pattern in cfg["best_for"]]
            if not best_models:
                best_models = list(MODELS.keys())

            # Use best model 70% of the time, random otherwise (realistic usage)
            if random.random() < 0.7:
                model = random.choice(best_models)
            else:
                model = random.choice(list(MODELS.keys()))

            model_config = MODELS[model]
            provider = model.split("/")[0]

            # Calculate metrics
            is_best = pattern in model_config["best_for"]
            quality_score = calculate_quality_score(model_config, pattern, is_best)
            cost = calculate_cost(model_config, len(prompt))
            tokens_used = int(len(prompt) * 1.5)  # Rough estimation

            # Generate cache key
            cache_key = generate_cache_key(prompt, model)
            prompt_normalized = prompt.lower()

            # Simulate realistic response
            response = f"[Simulated {pattern} response from {model}]"

            # Timestamp with some spread over 30 days
            timestamp = base_time + timedelta(days=i % 30, hours=random.randint(0, 23))
            created_at = timestamp.isoformat()
            last_accessed = timestamp.isoformat()

            # Calculate tokens
            tokens_in = int(len(prompt) * 0.75)
            tokens_out = int(tokens_in * 1.2)

            # Determine complexity based on pattern
            if pattern in ["code", "analysis", "reasoning"]:
                complexity = "complex"
            elif pattern in ["explanation", "factual"]:
                complexity = "moderate"
            else:
                complexity = "simple"

            max_tokens = 4000

            try:
                # Insert into response_cache using actual schema
                cursor.execute("""
                    INSERT OR IGNORE INTO response_cache
                    (cache_key, prompt_normalized, max_tokens, response, provider, model,
                     complexity, tokens_in, tokens_out, cost, created_at, last_accessed,
                     hit_count, upvotes, downvotes, quality_score, invalidated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (cache_key, prompt_normalized, max_tokens, response, provider, model,
                      complexity, tokens_in, tokens_out, cost, created_at, last_accessed,
                      1, 0, 0, quality_score, 0))

                # Add user feedback (80% of queries get rated)
                if random.random() < 0.8:
                    # Rating correlates with quality
                    if quality_score >= 0.85:
                        rating = random.choice([4, 5, 5])  # Mostly 5s
                    elif quality_score >= 0.75:
                        rating = random.choice([3, 4, 4])  # Mostly 4s
                    else:
                        rating = random.choice([2, 3, 3])  # Mostly 3s

                    feedback_timestamp = (timestamp + timedelta(minutes=5)).isoformat()

                    cursor.execute("""
                        INSERT INTO response_feedback (cache_key, rating, timestamp)
                        VALUES (?, ?, ?)
                    """, (cache_key, rating, feedback_timestamp))

                total_inserted += 1

            except sqlite3.IntegrityError:
                # Skip duplicates
                pass

    conn.commit()

    # Print summary
    cursor.execute("SELECT COUNT(*) FROM response_cache")
    total_queries = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM response_feedback")
    total_feedback = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT model) FROM response_cache")
    unique_models = cursor.fetchone()[0]

    conn.close()

    print(f"\n✅ Training data generated successfully!")
    print(f"   Total queries: {total_queries}")
    print(f"   With feedback: {total_feedback}")
    print(f"   Unique models: {unique_models}")
    print(f"\n🎯 Ready to train learning intelligence!")

if __name__ == "__main__":
    print("=" * 70)
    print("  LEARNING INTELLIGENCE - TRAINING DATA GENERATOR")
    print("=" * 70)
    print("\nGenerating 100+ realistic queries across 6 patterns...")
    print("Models: DeepSeek, Qwen, Gemini, Claude, OpenRouter")
    print("\nThis will create a 30-day history of diverse queries.")

    populate_database()

    print("\n" + "=" * 70)
    print("  Next steps:")
    print("  1. Run customer_dashboard.py to see learning progress")
    print("  2. Run admin_dashboard.py to see model performance")
    print("  3. Test the agent with: python3 cost_optimizer_agent.py")
    print("=" * 70)
