"""Add PostgreSQL tables for Autonomous Verification Ledger."""

from alembic import op  # type: ignore
import sqlalchemy as sa  # type: ignore


# Revision identifiers, used by Alembic.
revision = "202510281200"
down_revision = "202510261200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ledger_records table
    op.create_table(
        "ledger_records",
        sa.Column("rid", sa.UUID(), nullable=False),
        sa.Column("anchor_id", sa.UUID(), nullable=False),
        sa.Column("slot", sa.Text(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("ts", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("prev_hash", sa.CHAR(64), nullable=True),
        sa.Column("hash", sa.CHAR(64), nullable=False),
        sa.Column("payload", sa.JSONB(), nullable=False),
        sa.Column("sig", sa.LargeBinary(), nullable=True),
        sa.Column("producer", sa.Text(), nullable=True),
        sa.Column("version", sa.Text(), nullable=False, default="v1"),
        sa.PrimaryKeyConstraint("rid"),
        sa.UniqueConstraint("hash"),
    )

    # Create index on anchor_id and ts for efficient chain queries
    op.create_index("idx_records_anchor_ts", "ledger_records", ["anchor_id", "ts"])

    # Create ledger_checkpoints table
    op.create_table(
        "ledger_checkpoints",
        sa.Column("cid", sa.UUID(), nullable=False),
        sa.Column("range_start", sa.Text(), nullable=False),
        sa.Column("range_end", sa.Text(), nullable=False),
        sa.Column("merkle_root", sa.CHAR(64), nullable=False),
        sa.Column("sig", sa.LargeBinary(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("record_count", sa.Integer(), nullable=False, default=0),
        sa.PrimaryKeyConstraint("cid"),
    )


def downgrade() -> None:
    op.drop_table("ledger_checkpoints")
    op.drop_index("idx_records_anchor_ts")
    op.drop_table("ledger_records")