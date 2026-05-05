"""Add conversation summary to meetings table

Revision ID: add_meeting_summary
Revises: add_transcript_table
Create Date: 2026-05-04 14:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_meeting_summary'
down_revision = 'add_transcript_table'
branch_labels = None
depends_on = None


def upgrade():
    # Add conversation_summary column to meetings table
    op.add_column('meetings', sa.Column('conversation_summary', sa.TEXT(), nullable=True))


def downgrade():
    # Remove conversation_summary column from meetings table
    op.drop_column('meetings', 'conversation_summary')
