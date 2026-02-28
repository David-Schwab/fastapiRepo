"""create_alchemyposts_table

Revision ID: ffc9b550673b
Revises:
Create Date: 2026-02-28 19:49:14.149534

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ffc9b550673b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("alchemyposts", sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
                    sa.Column("title", sa.String(), nullable=False),
                    sa.Column("content", sa.String(), nullable=False),
                    sa.Column("published", sa.Boolean(), nullable=False, server_default="true"),
                    sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
                    sa.Column("user_id", sa.Integer(), nullable=False),
                   # sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE")
                    )
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
