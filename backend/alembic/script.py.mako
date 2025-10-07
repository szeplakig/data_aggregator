"""Mako template for Alembic migration scripts."""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "${up_revision}"
down_revision = ${down_revision if down_revision else None}
branch_labels = None
depends_on = None

def upgrade():
    ${upgrades if upgrades else 'pass'}


def downgrade():
    ${downgrades if downgrades else 'pass'}
