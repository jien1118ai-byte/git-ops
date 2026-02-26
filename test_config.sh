#!/bin/bash
# Test script for configuration file support

set -e

echo "=== Testing Git-Ops Configuration Support ==="
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if PyYAML is installed
echo "1. Checking dependencies..."
if python3 -c "import yaml" 2>/dev/null; then
    echo "✓ PyYAML is installed"
else
    echo "✗ PyYAML not installed"
    echo "  Install with: pip install PyYAML"
    echo "  Or: pip install -r requirements.txt"
    exit 1
fi
echo

# Test 2: Initialize config file
echo "2. Testing config initialization..."
python3 scripts/config_manager.py --init
if [ -f "git-ops.yml" ]; then
    echo "✓ Config template created: git-ops.yml"
    mv git-ops.yml git-ops-test.yml
    echo "  Renamed to: git-ops-test.yml"
else
    echo "✗ Failed to create config template"
    exit 1
fi
echo

# Test 3: Show default configuration
echo "3. Showing default configuration..."
python3 scripts/config_manager.py --show | head -20
echo "..."
echo

# Test 4: Set and get configuration values
echo "4. Testing get/set operations..."
python3 scripts/config_manager.py --config git-ops-test.yml --set git.remote upstream
echo "✓ Set git.remote to upstream"

value=$(python3 scripts/config_manager.py --config git-ops-test.yml --get git.remote)
if [ "$value" = "upstream" ]; then
    echo "✓ Get git.remote: $value"
else
    echo "✗ Get git.remote failed: expected 'upstream', got '$value'"
fi
echo

# Test 5: Test alias resolution
echo "5. Testing alias resolution..."
cat > git-ops-test.yml << 'EOF'
aliases:
  s: stash
  cm: checkout main
  cap: commit and push
EOF

python3 << 'PYEOF'
from scripts.config_manager import ConfigManager
config = ConfigManager('git-ops-test.yml')

# Test alias resolution
tests = [
    ('s', 'stash'),
    ('cm', 'checkout main'),
    ('cap', 'commit and push'),
    ('unknown', 'unknown'),  # Should return original
]

for input_text, expected in tests:
    result = config.resolve_alias(input_text)
    if result == expected:
        print(f"✓ Alias '{input_text}' → '{result}'")
    else:
        print(f"✗ Alias '{input_text}': expected '{expected}', got '{result}'")
PYEOF
echo

# Test 6: Test custom patterns
echo "6. Testing custom patterns..."
cat > git-ops-test.yml << 'EOF'
custom_patterns:
  save: stash with message 'WIP'
  quick commit: commit 'wip' and push
EOF

python3 << 'PYEOF'
from scripts.config_manager import ConfigManager
config = ConfigManager('git-ops-test.yml')

# Test custom pattern resolution
tests = [
    ('save', "stash with message 'WIP'"),
    ('quick commit', "commit 'wip' and push"),
    ('unknown', None),  # Should return None
]

for input_text, expected in tests:
    result = config.resolve_custom_pattern(input_text)
    if result == expected:
        status = '✓'
    else:
        status = '✗'
    print(f"{status} Pattern '{input_text}' → {result}")
PYEOF
echo

# Test 7: Integration with git_ops.py
echo "7. Testing integration with git_ops.py..."

cat > git-ops-test.yml << 'EOF'
aliases:
  s: stash

logging:
  enabled: false
EOF

# Test alias through git_ops.py (just generate, don't execute)
echo "Testing: gops 's' --config git-ops-test.yml"
output=$(python3 scripts/git_ops.py --from-text "s" --config git-ops-test.yml --no-log 2>&1 | grep "git stash" || echo "not found")

if echo "$output" | grep -q "git stash"; then
    echo "✓ Alias resolution works through git_ops.py"
else
    echo "✗ Alias resolution failed in git_ops.py"
    echo "  Output: $output"
fi
echo

# Test 8: Config file precedence
echo "8. Testing config file precedence..."

# Create configs in different locations
mkdir -p test-precedence
cd test-precedence

# Local config (should have highest precedence)
echo "git:" > git-ops.yml
echo "  remote: local" >> git-ops.yml

# Parent config
echo "git:" > ../.git-ops-test2.yml
echo "  remote: parent" >> ../.git-ops-test2.yml

result=$(python3 ../scripts/config_manager.py --get git.remote)
echo "Config file found, remote setting: $result"

cd ..
rm -rf test-precedence
echo

# Cleanup
echo "9. Cleanup..."
rm -f git-ops-test.yml .git-ops-test2.yml
echo "✓ Test files cleaned up"
echo

echo "=== All Configuration Tests Completed ==="
echo
echo "Next steps:"
echo "  1. Initialize your config: python3 scripts/git_ops.py --init-config"
echo "  2. Edit the config: nano ~/.git-ops.yml"
echo "  3. View current config: python3 scripts/config_manager.py --show"
echo "  4. Read the guide: cat CONFIG_GUIDE.md"
