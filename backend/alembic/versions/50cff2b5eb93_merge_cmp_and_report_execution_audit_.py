"""merge CMP and report execution audit heads

Revision ID: 50cff2b5eb93
Revises: 20260830_g84324l_report_execution_audit, 20260830_g84328_cmp_authoritative_controls
Create Date: 2026-09-01 12:15:18.345940

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '50cff2b5eb93'
down_revision: Union[str, Sequence[str], None] = ('20260830_g84324l_report_execution_audit', '20260830_g84328_cmp_authoritative_controls')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
