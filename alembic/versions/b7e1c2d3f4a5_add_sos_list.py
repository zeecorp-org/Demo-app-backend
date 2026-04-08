"""add sos list

Revision ID: b7e1c2d3f4a5
Revises: d92e1f5a7c4b
Create Date: 2026-03-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7e1c2d3f4a5"
down_revision: Union[str, Sequence[str], None] = "d92e1f5a7c4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "sos_list",
        sa.Column("sos_user_id", sa.Integer(), nullable=False),
        sa.Column("sos_contact_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["sos_contact_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sos_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("sos_user_id", "sos_contact_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("sos_list")
