"""Entry point for: python -m antigravity_bridge"""
import sys
from pathlib import Path

# Add the bridge directory to path
sys.path.insert(0, str(Path(__file__).parent))

from server import main
main()
