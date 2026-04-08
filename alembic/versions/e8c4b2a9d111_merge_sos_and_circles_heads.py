"""merge sos and circles heads

Revision ID: e8c4b2a9d111
Revises: b7e1c2d3f4a5, f7a82c4d9e31
Create Date: 2026-04-08 00:00:00.000000

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "e8c4b2a9d111"
down_revision: Union[str, Sequence[str], None] = ("b7e1c2d3f4a5", "f7a82c4d9e31")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge migration branches."""
    pass


def downgrade() -> None:
    """Unmerge migration branches."""
    pass
