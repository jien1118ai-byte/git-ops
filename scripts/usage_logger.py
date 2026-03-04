#!/usr/bin/env python3
"""
Usage Logger for git-ops
Records natural language patterns and command frequency
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union


class UsageLogger:
    def __init__(self, log_file: Optional[Union[str, Path]] = None) -> None:
        if log_file is None:
            # Store in user's home directory
            home = Path.home()
            self.log_dir = home / ".git-ops"
            self.log_dir.mkdir(exist_ok=True)
            self.log_file = self.log_dir / "usage.jsonl"
            self.error_file = self.log_dir / "errors.jsonl"
            self.notes_dir = self.log_dir / "notes"
            self.notes_dir.mkdir(exist_ok=True)
        else:
            self.log_file = Path(log_file)
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            self.log_dir = self.log_file.parent
            self.error_file = self.log_file.parent / "errors.jsonl"
            self.notes_dir = self.log_file.parent / "notes"
            self.notes_dir.mkdir(exist_ok=True)

    def log(self, input_text: str, operation: str, success: bool = True, error: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> None:
        """Log a single usage event"""
        entry: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "input": input_text,
            "operation": operation,
            "success": success,
            "error": error,
        }
        if context:
            entry["context"] = context

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def log_error(
        self,
        input_text: str,
        operation: str,
        error_msg: str,
        exit_code: int,
        error_code: Optional[str] = None,
        suggestion: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a detailed error event"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "input": input_text,
            "operation": operation,
            "success": False,
            "error": {
                "message": error_msg,
                "exit_code": exit_code,
                "error_code": error_code or "UNKNOWN",
                "suggestion": suggestion,
                "context": context or {},
            },
        }

        with open(self.error_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def get_last_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get last N errors for AI diagnosis"""
        if not self.error_file.exists():
            return []

        errors: List[Dict[str, Any]] = []
        with open(self.error_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry: Dict[str, Any] = json.loads(line)
                    errors.append(entry)
                except json.JSONDecodeError:
                    continue

        return errors[-limit:]

    def generate_error_summary(self) -> Union[str, Path]:
        """Generate AI-readable error summary"""
        if not self.error_file.exists():
            return ""

        summary_lines: List[str] = ["# Git-Ops Error Summary\n"]
        errors = self.get_last_errors(50)

        if not errors:
            return "# Git-Ops Error Summary\n\nNo errors recorded.\n"

        summary_lines.append(f"Last {len(errors)} errors:\n")

        for error in errors:
            ts = error.get("timestamp", "?")
            op = error.get("operation", "?")
            msg = error.get("error", {}).get("message", "?")
            code = error.get("error", {}).get("error_code", "?")
            suggestion = error.get("error", {}).get("suggestion", "")

            summary_lines.append(f"## {ts} - {op} (Code: {code})")
            summary_lines.append(f"Message: {msg}\n")
            if suggestion:
                summary_lines.append(f"Recovery: {suggestion}\n")
            summary_lines.append("")

        summary_file = self.log_dir / "error_summary.md"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("\n".join(summary_lines))

        return summary_file

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        if not self.log_file.exists():
            return {
                "total_uses": 0,
                "operations": {},
                "common_patterns": [],
                "error_rate": 0,
            }

        operations: Dict[str, int] = {}
        patterns: List[str] = []
        total = 0
        errors = 0

        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    total += 1

                    # Count operations
                    op = entry.get("operation", "unknown")
                    operations[op] = operations.get(op, 0) + 1

                    # Collect patterns
                    patterns.append(entry.get("input", ""))

                    # Count errors
                    if not entry.get("success", True):
                        errors += 1
                except json.JSONDecodeError:
                    continue

        # Find common patterns
        from collections import Counter

        pattern_counter = Counter(patterns)
        common_patterns = pattern_counter.most_common(20)

        return {
            "total_uses": total,
            "operations": dict(
                sorted(operations.items(), key=lambda x: x[1], reverse=True)
            ),
            "common_patterns": common_patterns,
            "error_rate": errors / total if total > 0 else 0,
        }

    def export_patterns(self, output_file: Optional[Union[str, Path]] = None) -> int:
        """Export unique patterns for training/improvement"""
        if output_file is None:
            output_file = self.log_dir / "patterns.txt"

        patterns: Set[str] = set()

        if self.log_file.exists():
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("success", True):
                            patterns.add(entry.get("input", ""))
                    except json.JSONDecodeError:
                        continue

        with open(output_file, "w", encoding="utf-8") as f:
            for pattern in sorted(patterns):
                f.write(pattern + "\n")

        return len(patterns)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Git-ops usage logger")
    parser.add_argument("--stats", action="store_true", help="Show usage statistics")
    parser.add_argument("--export", action="store_true", help="Export unique patterns")
    parser.add_argument("--clear", action="store_true", help="Clear usage log")

    args = parser.parse_args()
    logger = UsageLogger()

    if args.stats:
        stats = logger.get_stats()
        print("=== Git-ops Usage Statistics ===\n")
        print(f"Total uses: {stats['total_uses']}")
        print(f"Error rate: {stats['error_rate']:.1%}\n")

        print("Operations by frequency:")
        for op, count in stats["operations"].items():
            percentage = (
                count / stats["total_uses"] * 100 if stats["total_uses"] > 0 else 0
            )
            print(f"  {op:20s} {count:4d} ({percentage:5.1f}%)")

        print("\nMost common patterns:")
        for pattern, count in stats["common_patterns"][:10]:
            print(f"  {count:3d}x: {pattern}")

    elif args.export:
        count = logger.export_patterns()
        print(f"Exported {count} unique patterns to {logger.log_dir / 'patterns.txt'}")

    elif args.clear:
        if logger.log_file.exists():
            logger.log_file.unlink()
            print("Usage log cleared")
        else:
            print("No usage log found")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
