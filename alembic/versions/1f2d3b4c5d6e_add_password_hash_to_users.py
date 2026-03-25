"""add password hash to users

Revision ID: 1f2d3b4c5d6e
Revises: 5464d53bcf7a
Create Date: 2026-03-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1f2d3b4c5d6e"
down_revision: Union[str, Sequence[str], None] = "5464d53bcf7a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(length=255), nullable=True),
    )
    op.execute("UPDATE users SET password_hash = 'legacy-user-no-password'")
    op.alter_column("users", "password_hash", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "password_hash")
