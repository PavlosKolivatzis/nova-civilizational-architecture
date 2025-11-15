#!/usr/bin/env python3
"""
Ledger migration CLI tool.

Phase 14-1: Apply/verify PostgreSQL schema migrations for Autonomous Verification Ledger.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from alembic import command
from alembic.config import Config
from alembic.environment import EnvironmentContext
from alembic.script import ScriptDirectory

from nova.config.ledger_config import LedgerConfig


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def get_alembic_config() -> Config:
    """Get Alembic configuration for ledger migrations."""
    # Assume migrations are in schemas/migrations
    migration_dir = Path(__file__).parent.parent / "schemas" / "migrations"

    config = Config()
    config.set_main_option("script_location", str(migration_dir))
    config.set_main_option("sqlalchemy.url", LedgerConfig.from_env().dsn)

    return config


async def check_db_connection():
    """Check if database is reachable."""
    from sqlalchemy.ext.asyncio import create_async_engine
    import sqlalchemy.exc

    config = LedgerConfig.from_env()
    if not config.dsn:
        print("ERROR: LEDGER_DSN not configured")
        return False

    try:
        engine = create_async_engine(config.dsn, pool_size=1, pool_timeout=5)
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        print("✓ Database connection successful")
        return True
    except sqlalchemy.exc.SQLAlchemyError as e:
        print(f"✗ Database connection failed: {e}")
        return False
    finally:
        await engine.dispose()


def upgrade_database(revision: str = "head"):
    """Upgrade database to specified revision."""
    config = get_alembic_config()
    try:
        command.upgrade(config, revision)
        print(f"✓ Database upgraded to {revision}")
    except Exception as e:
        print(f"✗ Upgrade failed: {e}")
        sys.exit(1)


def downgrade_database(revision: str):
    """Downgrade database to specified revision."""
    config = get_alembic_config()
    try:
        command.downgrade(config, revision)
        print(f"✓ Database downgraded to {revision}")
    except Exception as e:
        print(f"✗ Downgrade failed: {e}")
        sys.exit(1)


def show_current_revision():
    """Show current database revision."""
    config = get_alembic_config()
    script = ScriptDirectory.from_config(config)

    def show_current(connection, context):
        current_rev = context.get_current_revision()
        print(f"Current revision: {current_rev}")
        return []

    with EnvironmentContext(config, script, fn=show_current):
        script.run_env()


def show_history():
    """Show migration history."""
    config = get_alembic_config()
    script = ScriptDirectory.from_config(config)

    for rev in script.walk_revisions():
        print(f"{rev.revision}: {rev.doc}")
        if rev.down_revision:
            print(f"  ↓ {rev.down_revision}")


def main():
    parser = argparse.ArgumentParser(
        description="Ledger PostgreSQL migration tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check database connection
  python scripts/ledger_migrate.py check-db

  # Upgrade to latest
  python scripts/ledger_migrate.py upgrade

  # Upgrade to specific revision
  python scripts/ledger_migrate.py upgrade 202510281200

  # Show current revision
  python scripts/ledger_migrate.py current

  # Show migration history
  python scripts/ledger_migrate.py history

  # Downgrade (CAUTION: destructive)
  python scripts/ledger_migrate.py downgrade base
        """
    )

    parser.add_argument(
        "command",
        choices=["check-db", "upgrade", "downgrade", "current", "history"],
        help="Migration command to run"
    )

    parser.add_argument(
        "revision",
        nargs="?",
        default="head",
        help="Revision to upgrade/downgrade to (default: head)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    if args.command == "check-db":
        success = asyncio.run(check_db_connection())
        sys.exit(0 if success else 1)

    elif args.command == "upgrade":
        upgrade_database(args.revision)

    elif args.command == "downgrade":
        if args.revision == "head":
            print("ERROR: Must specify a revision to downgrade to")
            sys.exit(1)
        downgrade_database(args.revision)

    elif args.command == "current":
        show_current_revision()

    elif args.command == "history":
        show_history()


if __name__ == "__main__":
    main()
