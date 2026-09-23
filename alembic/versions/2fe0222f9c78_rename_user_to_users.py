"""rename_user_to_users

Revision ID: 2fe0222f9c78
Revises: b506192f7b3c
Create Date: 2026-09-23 21:19:02.241046

"""
from typing import Sequence, Union

from alembic import op

revision: str = '2fe0222f9c78'
down_revision: Union[str, Sequence[str], None] = 'b506192f7b3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: rename table 'user' to 'users' without data loss."""
    op.rename_table('user', 'users')
    op.execute('ALTER INDEX IF EXISTS ix_user_uid RENAME TO ix_users_uid')


def downgrade() -> None:
    """Downgrade schema: rename table 'users' back to 'user'."""
    op.execute('ALTER INDEX IF EXISTS ix_users_uid RENAME TO ix_user_uid')
    op.rename_table('users', 'user')
