#!/usr/bin/env python3
"""
Setup development bookmarks for Nova Civilizational Architecture.
Creates .vscode/settings.json with workspace bookmarks for key files.
"""

import json
import os
from pathlib import Path

BOOKMARKS = {
    "docs/README.md": "📖 Documentation Index",
    "docs/NAVIGATION.md": "🧭 Navigation Guide",
    "docs/GLOSSARY.md": "📚 Glossary",
    "docs/architecture/ARCHITECTURE.md": "🏗️ Architecture",
    "TREE.md": "🌳 Directory Tree",
    "src/nova/slots/": "🎯 Cognitive Slots",
    "src/nova/ledger/": "📊 Three Ledgers",
    "tests/": "🧪 Test Suite",
    "tests/README.md": "🧪 Test Documentation",
    "contracts/": "📋 Contracts",
    "config/.env.example": "⚙️ Configuration",
    "scripts/maintenance/sunlight_scan.py": "🔍 Governance Scanner",
    "agents/nova_ai_operating_framework.md": "🤖 AI Operating Framework",
    "monitoring/": "📈 Monitoring Setup",
    "ops/": "📊 Operations",
    "archive/": "🗂️ Historical Archive"
}

def create_vscode_bookmarks():
    """Create VS Code workspace settings with bookmarks."""
    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)

    settings_file = vscode_dir / "settings.json"

    # Load existing settings or create new
    if settings_file.exists():
        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            settings = {}
    else:
        settings = {}

    # Add bookmarks
    settings["bookmarks"] = BOOKMARKS

    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=2)

    print("✅ VS Code bookmarks created in .vscode/settings.json")
    print("📖 Key bookmarks added:")
    for path, description in BOOKMARKS.items():
        print(f"   {description}: {path}")

def create_jetbrains_bookmarks():
    """Create JetBrains IDE bookmarks (optional)."""
    # Could be extended for PyCharm, IntelliJ, etc.
    pass

if __name__ == "__main__":
    create_vscode_bookmarks()
    print("\n💡 Tip: Use 'make nav' to view navigation guide")
    print("💡 Tip: Use 'make tree' to view directory structure")
