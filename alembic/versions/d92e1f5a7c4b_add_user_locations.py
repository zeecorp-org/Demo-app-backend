"""add user locations

Revision ID: d92e1f5a7c4b
Revises: 8fca39980f02
Create Date: 2026-03-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d92e1f5a7c4b"
down_revision: Union[str, Sequence[str], None] = "8fca39980f02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "user_locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("is_visible", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_locations_id"), "user_locations", ["id"], unique=False)
    op.create_index(op.f("ix_user_locations_updated_at"), "user_locations", ["updated_at"], unique=False)
    op.create_index(op.f("ix_user_locations_user_id"), "user_locations", ["user_id"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_user_locations_user_id"), table_name="user_locations")
    op.drop_index(op.f("ix_user_locations_updated_at"), table_name="user_locations")
    op.drop_index(op.f("ix_user_locations_id"), table_name="user_locations")
    op.drop_table("user_locations")
