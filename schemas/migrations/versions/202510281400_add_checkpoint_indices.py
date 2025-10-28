"""Add indices for ledger checkpoints performance."""

from alembic import op  # type: ignore
import sqlalchemy as sa  # type: ignore


# Revision identifiers, used by Alembic.
revision = "202510281400"
down_revision = "202510281200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Performance indices for checkpoint queries
    op.create_index(
        "idx_checkpoints_created_at",
        "ledger_checkpoints",
        ["created_at"],
        postgresql_ops={"created_at": "DESC"}
    )

    # Performance index for record timestamp queries
    op.create_index(
        "idx_records_ts",
        "ledger_records",
        ["ts"]
    )

    # Optional: store signed header for federation (JSONB column)
    op.add_column(
        "ledger_checkpoints",
        sa.Column("header", sa.JSONB(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("ledger_checkpoints", "header")
    op.drop_index("idx_records_ts")
    op.drop_index("idx_checkpoints_created_at")