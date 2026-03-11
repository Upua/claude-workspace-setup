"""Pi Status MCP Server - Monitor Raspberry Pi health over SSH."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))
from server import main

if __name__ == "__main__":
    main()
