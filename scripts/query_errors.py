#!/usr/bin/env python3
"""
Query errors from git-ops
Helpful for AI to diagnose what went wrong with operations
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def query_last_error() -> Optional[Dict[str, Any]]:
    """Get the last error that occurred"""
    home = Path.home()
    error_file = home / ".git-ops" / "errors.jsonl"

    if not error_file.exists():
        print("No errors recorded")
        return None

    errors: List[Dict[str, Any]] = []
    with open(error_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                errors.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not errors:
        print("No errors recorded")
        return None

    last_error: Dict[str, Any] = errors[-1]
    return last_error


def print_error(error: Optional[Dict[str, Any]]) -> None:
    """Print error in human-readable format"""
    if not error:
        return

    print("=" * 60)
    print("📋 LAST ERROR DETAILS")
    print("=" * 60)

    print(f"\n⏰ Timestamp: {error.get('timestamp', '?')}")
    print(f"🔧 Operation: {error.get('operation', '?')}")
    print(f"📝 Input: {error.get('input', '?')}")

    error_detail = error.get("error", {})
    print(f"\n❌ Error Code: {error_detail.get('error_code', 'UNKNOWN')}")
    print(f"📌 Message: {error_detail.get('message', 'Unknown error')}")
    print(f"🔢 Exit Code: {error_detail.get('exit_code', '?')}")

    if error_detail.get("suggestion"):
        print(f"\n💡 Recovery: {error_detail['suggestion']}")
        print("\nTry running:")
        for step in error_detail["suggestion"].split("&&"):
            print(f"  {step.strip()}")

    context = error_detail.get("context", {})
    if context:
        print("\n📊 Context:")
        for key, value in context.items():
            print(f"  {key}: {value}")

    print("\n" + "=" * 60)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Query git-ops errors")
    parser.add_argument("--last", action="store_true", help="Show last error")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--all", action="store_true", help="Show all errors")

    args = parser.parse_args()

    home = Path.home()
    error_file = home / ".git-ops" / "errors.jsonl"

    if args.all:
        if not error_file.exists():
            print("No errors recorded")
            return

        errors: List[Dict[str, Any]] = []
        with open(error_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    errors.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        if not errors:
            print("No errors recorded")
            return

        print(f"Found {len(errors)} errors:\n")
        for i, error in enumerate(errors[-10:], 1):  # Show last 10
            ts = error.get('timestamp', '?')
            op = error.get('operation', '?')
            code = error.get('error', {}).get('error_code', '?')
            print(
                f"{i}. [{ts}] {op}: {code}"
            )

    elif args.json:
        error = query_last_error()
        if error:
            print(json.dumps(error, indent=2, ensure_ascii=False))

    else:
        # Default: show last error
        error = query_last_error()
        print_error(error)


if __name__ == "__main__":
    main()
