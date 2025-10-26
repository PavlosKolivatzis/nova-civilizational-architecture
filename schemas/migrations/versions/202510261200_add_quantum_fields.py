"""Add quantum fidelity fields to attestation records."""

from alembic import op  # type: ignore
import sqlalchemy as sa  # type: ignore


# Revision identifiers, used by Alembic.
revision = "202510261200"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("attestation_records") as batch_op:
        batch_op.add_column(sa.Column("quantum_fidelity", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("entropy_source", sa.String(length=32), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("attestation_records") as batch_op:
        batch_op.drop_column("entropy_source")
        batch_op.drop_column("quantum_fidelity")
