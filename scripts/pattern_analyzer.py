#!/usr/bin/env python3
"""
Pattern Analyzer for git-ops
Analyzes usage patterns and suggests improvements
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime, timedelta


class PatternAnalyzer:
    def __init__(self, log_file=None):
        if log_file is None:
            home = Path.home()
            self.log_file = home / '.git-ops' / 'usage.jsonl'
        else:
            self.log_file = Path(log_file)

    def load_entries(self, days=None):
        """Load usage entries, optionally filtering by date"""
        entries = []

        if not self.log_file.exists():
            return entries

        cutoff = None
        if days:
            cutoff = datetime.now() - timedelta(days=days)

        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)

                    if cutoff:
                        timestamp = datetime.fromisoformat(entry['timestamp'])
                        if timestamp < cutoff:
                            continue

                    entries.append(entry)
                except (json.JSONDecodeError, KeyError):
                    continue

        return entries

    def analyze_operation_priority(self, days=30):
        """Analyze which operations are used most frequently"""
        entries = self.load_entries(days)

        if not entries:
            return {}

        operation_count = Counter()
        for entry in entries:
            operation_count[entry.get('operation', 'unknown')] += 1

        total = sum(operation_count.values())
        results = {}

        for op, count in operation_count.most_common():
            percentage = (count / total * 100) if total > 0 else 0
            results[op] = {
                'count': count,
                'percentage': percentage,
                'rank': len(results) + 1
            }

        return results

    def find_missing_patterns(self):
        """Find input patterns that weren't successfully parsed"""
        entries = self.load_entries()

        failed_patterns = []
        status_operations = []  # Track patterns that fell through to status

        for entry in entries:
            if not entry.get('success', True):
                failed_patterns.append(entry.get('input', ''))
            elif entry.get('operation') == 'status':
                # These might be patterns that weren't recognized
                status_operations.append(entry.get('input', ''))

        return {
            'failed': Counter(failed_patterns).most_common(10),
            'fallback_to_status': Counter(status_operations).most_common(10)
        }

    def suggest_alias_patterns(self, min_count=3):
        """Suggest patterns that should have shortcuts"""
        entries = self.load_entries()

        # Count exact pattern occurrences
        pattern_counter = Counter()
        for entry in entries:
            if entry.get('success', True):
                pattern_counter[entry.get('input', '')] += 1

        # Find frequently used patterns
        suggestions = []
        for pattern, count in pattern_counter.most_common():
            if count >= min_count:
                # Extract keywords
                words = pattern.lower().split()
                # Simple alias suggestion
                alias = ''.join([w[0] for w in words[:3]])  # First letters
                suggestions.append({
                    'pattern': pattern,
                    'count': count,
                    'suggested_alias': alias,
                    'command': f"alias gops-{alias}='gops \"{pattern}\"'"
                })

        return suggestions[:10]

    def analyze_keyword_usage(self):
        """Analyze which keywords/operations should be optimized"""
        entries = self.load_entries()

        keywords = defaultdict(int)
        operation_keywords = defaultdict(lambda: Counter())

        for entry in entries:
            input_text = entry.get('input', '').lower()
            operation = entry.get('operation', 'unknown')

            # Extract keywords (simple word-based)
            words = re.findall(r'\b\w+\b', input_text)
            for word in words:
                if len(word) > 2:  # Ignore very short words
                    keywords[word] += 1
                    operation_keywords[operation][word] += 1

        # Most common keywords overall
        top_keywords = Counter(keywords).most_common(20)

        # Keywords per operation
        operation_specific = {}
        for op, word_counter in operation_keywords.items():
            operation_specific[op] = word_counter.most_common(5)

        return {
            'overall': top_keywords,
            'by_operation': operation_specific
        }

    def generate_report(self, days=30):
        """Generate a comprehensive usage report"""
        print("=" * 70)
        print(f"Git-Ops Usage Analysis (Last {days} days)")
        print("=" * 70)
        print()

        # 1. Operation Priority
        print("### Operation Priority (by usage frequency)")
        print()
        priorities = self.analyze_operation_priority(days)

        if not priorities:
            print("No usage data found.")
            return

        for op, data in sorted(priorities.items(), key=lambda x: x[1]['rank']):
            stars = '⭐' * min(5, int(data['percentage'] / 10))
            print(f"{data['rank']:2d}. {op:15s} {data['count']:4d} uses ({data['percentage']:5.1f}%) {stars}")

        print()

        # 2. Missing Patterns
        print("### Unrecognized or Failed Patterns")
        print()
        missing = self.find_missing_patterns()

        if missing['failed']:
            print("Failed patterns:")
            for pattern, count in missing['failed']:
                print(f"  {count}x: {pattern}")
        else:
            print("  None - all patterns parsed successfully!")

        if missing['fallback_to_status']:
            print("\nPatterns that defaulted to 'status':")
            for pattern, count in missing['fallback_to_status'][:5]:
                print(f"  {count}x: {pattern}")

        print()

        # 3. Alias Suggestions
        print("### Suggested Aliases (for frequent patterns)")
        print()
        aliases = self.suggest_alias_patterns(min_count=3)

        if aliases:
            print("Add these to your ~/.bashrc or ~/.zshrc:\n")
            for suggestion in aliases[:5]:
                print(f"# Used {suggestion['count']} times")
                print(suggestion['command'])
                print()
        else:
            print("  No frequently-repeated patterns detected yet.")
            print("  Keep using git-ops to discover patterns!")

        print()

        # 4. Keyword Analysis
        print("### Most Common Keywords")
        print()
        keywords = self.analyze_keyword_usage()

        print("Overall top keywords:")
        for word, count in keywords['overall'][:10]:
            print(f"  {word:15s} {count:4d} times")

        print()

    def export_priority_config(self, output_file='priority.json'):
        """Export priority configuration based on usage"""
        priorities = self.analyze_operation_priority(days=90)  # 3 months

        config = {
            'generated_at': datetime.now().isoformat(),
            'priorities': priorities,
            'recommendations': {}
        }

        # Generate recommendations
        for op, data in priorities.items():
            if data['percentage'] > 20:
                config['recommendations'][op] = 'high_priority'
            elif data['percentage'] > 10:
                config['recommendations'][op] = 'medium_priority'
            elif data['percentage'] > 5:
                config['recommendations'][op] = 'normal'
            else:
                config['recommendations'][op] = 'low_priority'

        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        return output_path


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Analyze git-ops usage patterns')
    parser.add_argument('--days', type=int, default=30, help='Number of days to analyze')
    parser.add_argument('--export', action='store_true', help='Export priority configuration')
    parser.add_argument('--suggest-aliases', action='store_true', help='Show alias suggestions only')
    parser.add_argument('--log-file', help='Path to usage log file (default: ~/.git-ops/usage.jsonl)')
    parser.add_argument('--top-operations', action='store_true', help='Show top operations only')

    args = parser.parse_args()
    analyzer = PatternAnalyzer(log_file=args.log_file)

    if args.export:
        path = analyzer.export_priority_config()
        print(f"Priority configuration exported to: {path}")
    elif args.suggest_aliases:
        aliases = analyzer.suggest_alias_patterns(min_count=2)
        if aliases:
            print("# Suggested aliases based on your usage:")
            print("# Add to ~/.bashrc or ~/.zshrc\n")
            for suggestion in aliases:
                print(f"# Used {suggestion['count']} times")
                print(suggestion['command'])
                print()
        else:
            print("No frequently-repeated patterns found yet.")
    elif args.top_operations:
        priorities = analyzer.analyze_operation_priority(days=args.days)
        print("### Top Operations")
        print()
        for op, data in sorted(priorities.items(), key=lambda x: x[1]['count'], reverse=True):
            print(f"  {op:15s} {data['count']:4d} times ({data['percentage']:.1f}%)")
    else:
        analyzer.generate_report(days=args.days)


if __name__ == '__main__':
    main()
