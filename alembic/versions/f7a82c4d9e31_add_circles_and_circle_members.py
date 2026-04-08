"""add circles and circle members

Revision ID: f7a82c4d9e31
Revises: d92e1f5a7c4b
Create Date: 2026-03-31 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f7a82c4d9e31"
down_revision: Union[str, Sequence[str], None] = "d92e1f5a7c4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "circles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_circles_id"), "circles", ["id"], unique=False)
    op.create_index(op.f("ix_circles_owner_id"), "circles", ["owner_id"], unique=False)

    op.create_table(
        "circle_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("circle_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["circle_id"], ["circles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("circle_id", "user_id", name="uq_circle_member"),
    )
    op.create_index(op.f("ix_circle_members_id"), "circle_members", ["id"], unique=False)
    op.create_index(op.f("ix_circle_members_circle_id"), "circle_members", ["circle_id"], unique=False)
    op.create_index(op.f("ix_circle_members_user_id"), "circle_members", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_circle_members_user_id"), table_name="circle_members")
    op.drop_index(op.f("ix_circle_members_circle_id"), table_name="circle_members")
    op.drop_index(op.f("ix_circle_members_id"), table_name="circle_members")
    op.drop_table("circle_members")
    op.drop_index(op.f("ix_circles_owner_id"), table_name="circles")
    op.drop_index(op.f("ix_circles_id"), table_name="circles")
    op.drop_table("circles")
