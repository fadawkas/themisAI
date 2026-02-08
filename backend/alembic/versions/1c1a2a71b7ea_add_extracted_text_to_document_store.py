"""add extracted_text to document_store

Revision ID: 1c1a2a71b7ea
Revises: f3ad7195c4be
Create Date: 2025-12-27 15:01:28.119565
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1c1a2a71b7ea'
down_revision = 'f3ad7195c4be'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("document_store", sa.Column("extracted_text", sa.Text(), nullable=True))

def downgrade():
    op.drop_column("document_store", "extracted_text")


