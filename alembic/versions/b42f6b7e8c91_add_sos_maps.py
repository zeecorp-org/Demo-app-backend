"""add sos maps

Revision ID: b42f6b7e8c91
Revises: 8fca39980f02
Create Date: 2026-03-25 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b42f6b7e8c91"
down_revision: Union[str, Sequence[str], None] = "8fca39980f02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "sos_maps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("friendship_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["friendship_id"], ["friendships.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "friendship_id", name="uq_sos_map_user_friendship"),
    )
    op.create_index(op.f("ix_sos_maps_friendship_id"), "sos_maps", ["friendship_id"], unique=False)
    op.create_index(op.f("ix_sos_maps_id"), "sos_maps", ["id"], unique=False)
    op.create_index(op.f("ix_sos_maps_user_id"), "sos_maps", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_sos_maps_user_id"), table_name="sos_maps")
    op.drop_index(op.f("ix_sos_maps_id"), table_name="sos_maps")
    op.drop_index(op.f("ix_sos_maps_friendship_id"), table_name="sos_maps")
    op.drop_table("sos_maps")
