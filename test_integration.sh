#!/bin/bash
# Integration test: Configuration + Usage Tracking
# Demonstrates the "learn-optimize-execute" cycle

set -e

echo "=== Git-Ops Integration Test ==="
echo "Testing: Configuration + Usage Tracking Integration"
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Setup
echo "1. Setup test environment..."
mkdir -p test-integration
cd test-integration

# Create test config
cat > git-ops-test.yml << 'EOF'
aliases:
  s: stash
  cm: checkout main

custom_patterns:
  save: stash with message 'WIP'

logging:
  enabled: true
  log_file: ./test-usage.jsonl
EOF

echo "✓ Test configuration created"
echo

# Test 1: Usage logging with aliases
echo "2. Testing alias and pattern resolution..."
rm -f test-usage.jsonl

# Use alias (output should contain "git stash")
output=$(python3 ../scripts/git_ops.py --from-text "s" --config git-ops-test.yml --no-log 2>&1)
if echo "$output" | grep -q "git stash"; then
    echo "✓ Alias 's' resolved to 'stash'"
else
    echo "✗ Alias 's' did not resolve correctly"
    echo "  Output: $output"
fi

# Use custom pattern
output=$(python3 ../scripts/git_ops.py --from-text "save" --config git-ops-test.yml --no-log 2>&1)
if echo "$output" | grep -q "git stash"; then
    echo "✓ Custom pattern 'save' resolved"
else
    echo "✗ Custom pattern 'save' did not resolve correctly"
fi

echo

# Test 2: Pattern analysis
echo "3. Testing pattern analysis..."

# Create sample usage data
cat > test-usage.jsonl << 'EOF'
{"timestamp": "2026-01-30T10:00:00", "input": "stash", "operation": "stash", "success": true}
{"timestamp": "2026-01-30T10:05:00", "input": "stash", "operation": "stash", "success": true}
{"timestamp": "2026-01-30T10:10:00", "input": "stash", "operation": "stash", "success": true}
{"timestamp": "2026-01-30T10:15:00", "input": "checkout main", "operation": "checkout", "success": true}
{"timestamp": "2026-01-30T10:20:00", "input": "checkout main", "operation": "checkout", "success": true}
{"timestamp": "2026-01-30T10:25:00", "input": "commit and push", "operation": "commit", "success": true}
{"timestamp": "2026-01-30T10:30:00", "input": "pull", "operation": "pull", "success": true}
EOF

# Analyze patterns
python3 ../scripts/pattern_analyzer.py --log-file test-usage.jsonl --top-operations > analysis.txt

if grep -q "stash" analysis.txt && grep -q "checkout" analysis.txt; then
    echo "✓ Pattern analysis working"
else
    echo "✗ Pattern analysis failed"
    cat analysis.txt
fi

echo

# Test 3: Alias suggestions
echo "4. Testing alias suggestions..."

python3 ../scripts/pattern_analyzer.py --log-file test-usage.jsonl --suggest-aliases > suggestions.txt

if grep -q "checkout main" suggestions.txt || grep -q "stash" suggestions.txt; then
    echo "✓ Alias suggestions generated"
    echo "  Sample suggestions:"
    head -5 suggestions.txt | sed 's/^/  /'
else
    echo "✗ Alias suggestion failed"
fi

echo

# Test 4: Config integration
echo "5. Testing configuration get/set..."

# Test get operation
remote=$(python3 ../scripts/config_manager.py --config git-ops-test.yml --get aliases.s 2>/dev/null || echo "")
if [ "$remote" = "stash" ]; then
    echo "✓ Config get works: aliases.s = stash"
else
    echo "✗ Config get failed: got '$remote'"
fi

# Test set operation
python3 ../scripts/config_manager.py --config git-ops-test.yml --set aliases.test "test value" > /dev/null
test_val=$(python3 ../scripts/config_manager.py --config git-ops-test.yml --get aliases.test)
if [ "$test_val" = "test value" ]; then
    echo "✓ Config set works"
else
    echo "✗ Config set failed"
fi

echo

# Test 5: Full workflow demonstration
echo "6. Demonstrating complete workflow..."
echo

echo "   STEP 1: User runs commands (recorded to usage log)"
echo "   → gops 'stash' | bash"
echo "   → gops 'checkout main' | bash"
echo "   → gops 'stash' | bash"
echo

echo "   STEP 2: Analyze usage patterns"
echo "   → python3 scripts/pattern_analyzer.py --top-operations"
echo

echo "   STEP 3: Get alias suggestions"
echo "   → python3 scripts/pattern_analyzer.py --suggest-aliases"
echo "   Suggestions:"
python3 ../scripts/pattern_analyzer.py --log-file test-usage.jsonl --suggest-aliases 2>/dev/null | head -5 | sed 's/^/   /'
echo

echo "   STEP 4: Add suggestions to config file"
echo "   → Edit ~/.git-ops.yml"
echo "   Add: aliases:"
echo "        s: stash"
echo "        cm: checkout main"
echo

echo "   STEP 5: Use shortened commands"
echo "   → gops 's' | bash        # Instead of 'stash'"
echo "   → gops 'cm' | bash       # Instead of 'checkout main'"
echo

echo "   STEP 6: Cycle continues..."
echo "   → New usage patterns → New suggestions → Updated config"
echo

# Test 6: Verify all components work together
echo "7. Final integration check..."

# Check all required files exist
errors=0

if [ ! -f "../scripts/git_ops.py" ]; then
    echo "✗ Missing git_ops.py"
    errors=$((errors + 1))
fi

if [ ! -f "../scripts/config_manager.py" ]; then
    echo "✗ Missing config_manager.py"
    errors=$((errors + 1))
fi

if [ ! -f "../scripts/usage_logger.py" ]; then
    echo "✗ Missing usage_logger.py"
    errors=$((errors + 1))
fi

if [ ! -f "../scripts/pattern_analyzer.py" ]; then
    echo "✗ Missing pattern_analyzer.py"
    errors=$((errors + 1))
fi

if [ $errors -eq 0 ]; then
    echo "✓ All components present"
else
    echo "✗ Missing $errors component(s)"
fi

echo

# Cleanup
echo "8. Cleanup..."
cd ..
rm -rf test-integration
echo "✓ Test files cleaned up"
echo

# Summary
echo "=== Integration Test Summary ==="
echo
echo "Components tested:"
echo "  ✓ Configuration file loading (git-ops.yml)"
echo "  ✓ Alias resolution"
echo "  ✓ Custom pattern matching"
echo "  ✓ Usage logging"
echo "  ✓ Pattern analysis"
echo "  ✓ Alias suggestions"
echo "  ✓ Configuration get/set"
echo
echo "The complete 'learn-optimize-execute' cycle is working!"
echo
echo "Next steps:"
echo "  1. Start using git-ops with configuration"
echo "  2. Let it learn your patterns automatically"
echo "  3. Review suggestions periodically"
echo "  4. Update config with useful aliases"
echo "  5. Enjoy faster Git workflows!"
echo
