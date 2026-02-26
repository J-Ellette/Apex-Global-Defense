"""agd-shared test configuration."""
import sys
import os

# Ensure agd_shared is importable when running tests from the package root.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
