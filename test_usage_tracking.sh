#!/bin/bash
# Test script for usage tracking features

set -e

echo "=== Testing Git-Ops Usage Tracking ==="
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Test 1: Generate some test usage data
echo "1. Generating test usage data..."
python3 << 'EOF'
from scripts.usage_logger import UsageLogger
from datetime import datetime, timedelta
import random

logger = UsageLogger()

# Generate 50 test entries with varied operations
operations = ['stash', 'checkout', 'commit', 'grep', 'reset', 'merge', 'rebase']
patterns = [
    'stash my changes',
    'checkout main',
    'commit and push',
    'search for TODO',
    'undo last commit',
    'merge develop',
    'squash last 3 commits'
]

for i in range(50):
    op = random.choice(operations)
    pattern = random.choice(patterns)
    logger.log(pattern, op, success=True)

print("✓ Generated 50 test entries")
EOF

echo

# Test 2: View statistics
echo "2. Viewing usage statistics..."
python3 scripts/usage_logger.py --stats
echo

# Test 3: Run pattern analyzer
echo "3. Running pattern analysis..."
python3 scripts/pattern_analyzer.py --days 30
echo

# Test 4: Generate alias suggestions
echo "4. Generating alias suggestions..."
python3 scripts/pattern_analyzer.py --suggest-aliases
echo

# Test 5: Export priority configuration
echo "5. Exporting priority configuration..."
python3 scripts/pattern_analyzer.py --export
if [ -f "priority.json" ]; then
    echo "✓ Priority configuration exported to priority.json"
    cat priority.json | head -20
    echo "..."
else
    echo "✗ Failed to export priority configuration"
fi
echo

# Test 6: Export patterns
echo "6. Exporting unique patterns..."
python3 scripts/usage_logger.py --export
if [ -f "$HOME/.git-ops/patterns.txt" ]; then
    echo "✓ Patterns exported to ~/.git-ops/patterns.txt"
    wc -l "$HOME/.git-ops/patterns.txt"
else
    echo "✗ Failed to export patterns"
fi
echo

# Test 7: Test with actual git-ops command (without logging)
echo "7. Testing git-ops with --no-log..."
python3 scripts/git_ops.py --from-text "stash" --no-log > /dev/null
echo "✓ No-log option works"
echo

echo "=== All Tests Completed ==="
echo
echo "Cleanup options:"
echo "  - View log: cat ~/.git-ops/usage.jsonl"
echo "  - Clear log: python3 scripts/usage_logger.py --clear"
echo "  - View patterns: cat ~/.git-ops/patterns.txt"
echo "  - View priority: cat priority.json"
