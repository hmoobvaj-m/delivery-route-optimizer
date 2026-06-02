"""baseline

Revision ID: 88bec29e453f
Revises: 
Create Date: 2026-06-02 17:43:27.791145

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = '88bec29e453f'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
