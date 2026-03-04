"""Shared fixtures for git-ops tests."""

import sys
from pathlib import Path

# Allow importing from scripts/ without installing as a package
scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)
