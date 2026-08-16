import sys

from moss.cli import main

if __name__ == "__main__":
    # Double-clicking the frozen .exe has no subcommand; open the UI.
    if getattr(sys, "frozen", False) and len(sys.argv) <= 1:
        sys.argv.append("ui")
    raise SystemExit(main())
