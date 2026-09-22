"""PyInstaller entry point for the sagaz-cli standalone binary.

The CLI module uses relative imports (``from .agent import Agent``), so PyInstaller
needs this absolute-import launcher as its entry script.
"""
from laya.cli import main

if __name__ == "__main__":
    main()
