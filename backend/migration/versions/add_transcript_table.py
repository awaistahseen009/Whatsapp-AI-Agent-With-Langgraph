"""Add transcript table

Revision ID: add_transcript_table
Revises: be36cbe28c31
Create Date: 2026-05-04 14:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision = 'add_transcript_table'
down_revision = 'be36cbe28c31'
branch_labels = None
depends_on = None


def upgrade():
    # Create transcripts table
    op.create_table(
        'transcripts',
        sa.Column('transcript_id', sa.UUID(as_uuid=True), nullable=False, default=uuid.uuid4, primary_key=True),
        sa.Column('session_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('client_phone', sa.VARCHAR(), nullable=False),
        sa.Column('message_content', sa.TEXT(), nullable=False),
        sa.Column('message_type', sa.VARCHAR(), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tokens_used', sa.INTEGER(), nullable=True),
        sa.Column('processing_time_ms', sa.INTEGER(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_phone'], ['client.phone_num'], ),
        sa.ForeignKeyConstraint(['session_id'], ['conversation_sessions.session_id'], ),
    )
    op.create_index(op.f('ix_transcripts_session_id'), 'transcripts', ['session_id'], unique=False)
    op.create_index(op.f('ix_transcripts_client_phone'), 'transcripts', ['client_phone'], unique=False)


def downgrade():
    # Try to drop indexes if they exist
    try:
        op.drop_index(op.f('ix_transcripts_client_phone'), table_name='transcripts')
    except:
        pass
    try:
        op.drop_index(op.f('ix_transcripts_session_id'), table_name='transcripts')
    except:
        pass
    op.drop_table('transcripts')
