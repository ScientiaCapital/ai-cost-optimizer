"""Simple complexity scoring for prompt routing."""

def score_complexity(prompt: str) -> str:
    """
    Analyze prompt complexity using token count and keywords.

    Args:
        prompt: The user's input prompt

    Returns:
        "simple" for basic queries, "complex" for detailed queries
    """
    # Count tokens (simple word-based approximation)
    token_count = len(prompt.split())

    # Keywords indicating complex queries (50+ keywords for better accuracy)
    complexity_keywords = [
        # Analysis & Reasoning
        "explain", "analyze", "compare", "design", "architecture",
        "evaluate", "critique", "research", "synthesize", "assess",
        "prove", "deduce", "infer", "conclude", "recommend", "suggest",

        # Code & Technical
        "implement", "debug", "optimize", "refactor", "algorithm",
        "function", "class", "method", "code", "api", "endpoint",
        "schema", "database", "query", "migration", "deploy",
        "configuration", "dependency", "package", "module", "component",

        # Problem Solving
        "solve", "calculate", "compute", "troubleshoot", "diagnose",
        "investigate", "fix", "repair", "resolve", "address",

        # Architecture & Systems
        "scalability", "performance", "security", "reliability",
        "availability", "infrastructure", "system", "distributed",
        "microservice", "pattern", "framework", "integration",

        # Complex Actions
        "reverse engineer", "benchmark", "profile", "migrate",
        "transform", "integrate", "construct", "build", "develop",

        # Creative & Strategic
        "create", "generate", "write", "compose", "draft",
        "strategy", "tradeoff", "decision", "prioritize", "roadmap"
    ]

    # Check for complexity indicators
    has_keywords = any(keyword in prompt.lower() for keyword in complexity_keywords)

    # Routing logic: simple if short and no complex keywords
    if token_count < 100 and not has_keywords:
        return "simple"

    return "complex"


def get_complexity_metadata(prompt: str) -> dict:
    """
    Get detailed complexity analysis for logging/debugging.

    Returns:
        Dictionary with token count, keywords found, and classification
    """
    token_count = len(prompt.split())

    # Same expanded keywords as in score_complexity()
    complexity_keywords = [
        # Analysis & Reasoning
        "explain", "analyze", "compare", "design", "architecture",
        "evaluate", "critique", "research", "synthesize", "assess",
        "prove", "deduce", "infer", "conclude", "recommend", "suggest",

        # Code & Technical
        "implement", "debug", "optimize", "refactor", "algorithm",
        "function", "class", "method", "code", "api", "endpoint",
        "schema", "database", "query", "migration", "deploy",
        "configuration", "dependency", "package", "module", "component",

        # Problem Solving
        "solve", "calculate", "compute", "troubleshoot", "diagnose",
        "investigate", "fix", "repair", "resolve", "address",

        # Architecture & Systems
        "scalability", "performance", "security", "reliability",
        "availability", "infrastructure", "system", "distributed",
        "microservice", "pattern", "framework", "integration",

        # Complex Actions
        "reverse engineer", "benchmark", "profile", "migrate",
        "transform", "integrate", "construct", "build", "develop",

        # Creative & Strategic
        "create", "generate", "write", "compose", "draft",
        "strategy", "tradeoff", "decision", "prioritize", "roadmap"
    ]

    keywords_found = [kw for kw in complexity_keywords if kw in prompt.lower()]
    classification = score_complexity(prompt)

    return {
        "token_count": token_count,
        "keywords_found": keywords_found,
        "classification": classification
    }
