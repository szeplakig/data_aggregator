import os
import sys


# Ensure the repository root and backend package path are on sys.path so `app` imports work during pytest
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_PATH = os.path.join(REPO_ROOT, "backend")

for p in (BACKEND_PATH, REPO_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)
