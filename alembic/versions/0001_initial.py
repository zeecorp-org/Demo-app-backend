"""initial schema: users and friendships

Revision ID: 0001_initial
Revises:
Create Date: 2026-03-25 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

friendship_status_enum = sa.Enum(
    "PENDING",
    "ACCEPTED",
    "DECLINED",
    "BLOCKED",
    name="friendship_status",
)


def upgrade() -> None:
    """Create users and friendships tables."""

    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ------------------------------------------------------------------
    # friendships
    # ------------------------------------------------------------------
    friendship_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "friendships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("requester_id", sa.Integer(), nullable=False),
        sa.Column("addressee_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            friendship_status_enum,
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["requester_id"],
            ["users.id"],
            name="fk_friendships_requester_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["addressee_id"],
            ["users.id"],
            name="fk_friendships_addressee_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "requester_id", "addressee_id", name="uq_friendship_pair"
        ),
    )
    op.create_index("ix_friendships_id", "friendships", ["id"], unique=False)
    op.create_index(
        "ix_friendships_requester_id", "friendships", ["requester_id"], unique=False
    )
    op.create_index(
        "ix_friendships_addressee_id", "friendships", ["addressee_id"], unique=False
    )


def downgrade() -> None:
    """Drop friendships then users."""
    op.drop_index("ix_friendships_addressee_id", table_name="friendships")
    op.drop_index("ix_friendships_requester_id", table_name="friendships")
    op.drop_index("ix_friendships_id", table_name="friendships")
    op.drop_table("friendships")
    friendship_status_enum.drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
