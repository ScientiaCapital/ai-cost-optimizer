# Learning Intelligence Dashboard

Visual CLI dashboard showing learning progress and model performance.

## Usage

### Interactive Mode (Recommended)

```bash
# Run without arguments for user-friendly menu
python3 dashboard.py
```

This will display an interactive menu:
```
╔══════════════════════════════════════════╗
║  Learning Intelligence Dashboard         ║
╚══════════════════════════════════════════╝

Select your view:

  1. Customer View (Recommended)
     → Shows performance tiers
     → Hides technical details

  2. Admin View (Internal Use)
     → Shows actual model names
     → Full technical details

Enter choice (1-2) [1]: _
```

- Press Enter or type `1` for Customer View (default)
- Type `2` for Admin View
- Invalid inputs will prompt again
- Ctrl+C to cancel

### Command-Line Flags (Scriptable)

```bash
# External view (black-boxed tiers)
python3 dashboard.py --mode external

# Internal view (actual models)
python3 dashboard.py --mode internal
```

Use flags when running in scripts or automation where interactive prompts are not desired.

## Sections

1. **Training Data Overview** - Total queries, models, feedback count
2. **Pattern Distribution** - Sample counts per query pattern
3. **Top Performing Models** - Ranked by composite score
4. **Savings Projection** - 30-day cost optimization opportunity
5. **Learning Progress** - Maturity progress bars per pattern

## Requirements

- Database with historical data (run `init_test_data.py` first)
- Python 3.8+
- No external dependencies (uses stdlib only)

## Composite Score Formula

The ranking uses a weighted composite score:
- Quality Score: 50% weight
- Cost Efficiency: 30% weight (inverted - lower cost = higher score)
- Request Volume: 20% weight (confidence from sample size)

## Modes

### External Mode (Default)
Shows tier labels (Economy Tier, Premium Tier, etc.) to protect competitive intelligence.
Suitable for customer-facing reports and external presentations.

### Internal Mode
Shows actual model names (openrouter/deepseek-chat, etc.) for internal analysis.
Requires --mode internal flag. Use for development and debugging.

## Error Handling

If database is not found, the dashboard will display an error message and exit.
Run the main application or test data initialization script to create the database.
