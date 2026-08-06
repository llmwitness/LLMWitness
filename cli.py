"""
Legacy compatibility layer for cli.
Forwards CLI commands to agenttrace.cli.
"""

from agenttrace.cli import main

if __name__ == "__main__":
    main()
