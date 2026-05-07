"""initial-migrations

Revision ID: 0258928eafd9
Revises: 
Create Date: 2026-04-27 21:27:45.981435

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlmodel import SQLModel
from sqlalchemy.dialects import postgresql

revision: str = '0258928eafd9'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Safely create all enums using native PostgreSQL IF NOT EXISTS
    op.execute("CREATE TYPE IF NOT EXISTS clientstatus AS ENUM ('NEW', 'SERIOUS', 'CONVERTED', 'LOST')")
    op.execute("CREATE TYPE IF NOT EXISTS clientintent AS ENUM ('BUY', 'INVEST', 'RENT')")
    op.execute("CREATE TYPE IF NOT EXISTS companydoctype AS ENUM ('PROPERTY_LISTING', 'AREA_GUIDE', 'POLICY', 'FAQ', 'DEVELOPER_PROFILE', 'LEGAL')")
    op.execute("CREATE TYPE IF NOT EXISTS retrystatus AS ENUM ('PENDING', 'RETRIED', 'ABANDONED')")
    op.execute("CREATE TYPE IF NOT EXISTS propertytype AS ENUM ('APARTMENT', 'HOUSE', 'PLOT', 'VILLA', 'COMMERCIAL')")
    op.execute("CREATE TYPE IF NOT EXISTS listingtype AS ENUM ('SALE', 'RENT')")
    op.execute("CREATE TYPE IF NOT EXISTS clientdoctype AS ENUM ('SALE_DEED', 'NOC', 'BANK_STATEMENT', 'CNIC', 'FLOOR_PLAN', 'BROCHURE', 'OTHER')")
    op.execute("CREATE TYPE IF NOT EXISTS storagestatus AS ENUM ('INJECTED', 'CHUNKED')")
    op.execute("CREATE TYPE IF NOT EXISTS escalationstatus AS ENUM ('PENDING', 'RESOLVED', 'DISMISSED')")
    op.execute("CREATE TYPE IF NOT EXISTS meetingtype AS ENUM ('VIRTUAL_CONSULTATION', 'PROPERTY_TOUR', 'DOCUMENT_SIGNING', 'FOLLOWUP')")
    op.execute("CREATE TYPE IF NOT EXISTS meetingstatus AS ENUM ('SCHEDULED', 'COMPLETED', 'CANCELLED', 'NO_SHOW')")
    op.execute("CREATE TYPE IF NOT EXISTS userrole AS ENUM ('owner', 'agent')")

    op.create_table('client',
    sa.Column('phone_num', sa.VARCHAR(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('email', sa.VARCHAR(), nullable=True),
    sa.Column('city', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('timezone', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('status', sa.Enum('NEW', 'SERIOUS', 'CONVERTED', 'LOST', name='clientstatus', create_type=False), nullable=False),
    sa.Column('intent', sa.Enum('BUY', 'INVEST', 'RENT', name='clientintent', create_type=False), nullable=True),
    sa.Column('budget_min', sa.BIGINT(), nullable=True),
    sa.Column('budget_max', sa.BIGINT(), nullable=True),
    sa.Column('preferred_locations', postgresql.ARRAY(sa.VARCHAR()), nullable=True),
    sa.Column('property_type_pref', postgresql.ARRAY(sa.VARCHAR()), nullable=True),
    sa.Column('loan_preapproved', sa.Boolean(), nullable=False),
    sa.Column('onboarding_complete', sa.Boolean(), nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), nullable=False),
    sa.Column('last_active_at', postgresql.TIMESTAMP(), nullable=False),
    sa.PrimaryKeyConstraint('phone_num')
    )
    op.create_table('company_documents',
    sa.Column('doc_id', sa.VARCHAR(), nullable=False),
    sa.Column('filename', sa.VARCHAR(), nullable=False),
    sa.Column('doc_type', sa.Enum('PROPERTY_LISTING', 'AREA_GUIDE', 'POLICY', 'FAQ', 'DEVELOPER_PROFILE', 'LEGAL', name='companydoctype', create_type=False), nullable=False),
    sa.Column('chunk_count', sa.INTEGER(), nullable=False),
    sa.Column('token_count', sa.INTEGER(), nullable=False),
    sa.Column('ingested_at', postgresql.TIMESTAMP(), nullable=True),
    sa.Column('last_updated_at', postgresql.TIMESTAMP(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('doc_id')
    )
    op.create_table('error_logs',
    sa.Column('error_id', sa.UUID(), nullable=False),
    sa.Column('client_phone', sa.VARCHAR(), nullable=True),
    sa.Column('thread_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('node_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('incoming_message', sa.TEXT(), nullable=True),
    sa.Column('error_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('error_message', sa.TEXT(), nullable=True),
    sa.Column('traceback', sa.TEXT(), nullable=True),
    sa.Column('retry_count', sa.Integer(), nullable=False),
    sa.Column('retry_status', sa.Enum('PENDING', 'RETRIED', 'ABANDONED', name='retrystatus', create_type=False), nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), nullable=True),
    sa.PrimaryKeyConstraint('error_id')
    )
    op.create_table('property',
    sa.Column('property_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.VARCHAR(), nullable=False),
    sa.Column('description', sa.TEXT(), nullable=True),
    sa.Column('property_type', sa.Enum('APARTMENT', 'HOUSE', 'PLOT', 'VILLA', 'COMMERCIAL', name='propertytype', create_type=False), nullable=False),
    sa.Column('listing_type', sa.Enum('SALE', 'RENT', name='listingtype', create_type=False), nullable=False),
    sa.Column('location_area', sa.VARCHAR(), nullable=True),
    sa.Column('location_city', sa.VARCHAR(), nullable=True),
    sa.Column('address', sa.TEXT(), nullable=True),
    sa.Column('price', sa.BIGINT(), nullable=False),
    sa.Column('price_negotiable', sa.Boolean(), nullable=False),
    sa.Column('bedrooms', sa.Integer(), nullable=True),
    sa.Column('bathrooms', sa.Integer(), nullable=True),
    sa.Column('size_sqft', sa.INTEGER(), nullable=True),
    sa.Column('floor_number', sa.Integer(), nullable=True),
    sa.Column('total_floors', sa.Integer(), nullable=True),
    sa.Column('features', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('images', postgresql.ARRAY(sa.VARCHAR()), nullable=True),
    sa.Column('available', sa.Boolean(), nullable=False),
    sa.Column('developer_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('property_id')
    )
    op.create_table('user',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('password_hash', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('role', sa.Enum('owner', 'agent', name='userrole', create_type=False), server_default='agent', nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('client_documents',
    sa.Column('doc_id', sa.VARCHAR(), nullable=False),
    sa.Column('client_phone', sa.VARCHAR(), nullable=False),
    sa.Column('filename', sa.VARCHAR(), nullable=False),
    sa.Column('doc_type', sa.Enum('SALE_DEED', 'NOC', 'BANK_STATEMENT', 'CNIC', 'FLOOR_PLAN', 'BROCHURE', 'OTHER', name='clientdoctype', create_type=False), nullable=False),
    sa.Column('page_count', sa.INTEGER(), nullable=True),
    sa.Column('token_count', sa.INTEGER(), nullable=True),
    sa.Column('storage_status', sa.Enum('INJECTED', 'CHUNKED', name='storagestatus', create_type=False), nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), nullable=True),
    sa.Column('expires_at', postgresql.TIMESTAMP(), nullable=True),
    sa.Column('chunks_cleared', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['client_phone'], ['client.phone_num'], ),
    sa.PrimaryKeyConstraint('doc_id')
    )
    op.create_table('client_property_views',
    sa.Column('view_id', sa.UUID(), nullable=False),
    sa.Column('client_phone', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('property_id', sa.Uuid(), nullable=False),
    sa.Column('viewed_at', postgresql.TIMESTAMP(), nullable=False),
    sa.Column('client_feedback', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.ForeignKeyConstraint(['client_phone'], ['client.phone_num'], ),
    sa.ForeignKeyConstraint(['property_id'], ['property.property_id'], ),
    sa.PrimaryKeyConstraint('view_id')
    )
    op.create_table('conversation_sessions',
    sa.Column('session_id', sa.UUID(), nullable=False),
    sa.Column('client_phone', sa.VARCHAR(), nullable=True),
    sa.Column('started_at', postgresql.TIMESTAMP(), nullable=True),
    sa.Column('ended_at', postgresql.TIMESTAMP(), nullable=True),
    sa.Column('message_count', sa.Integer(), nullable=False),
    sa.Column('tools_called', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('properties_shown', sa.Integer(), nullable=False),
    sa.Column('meeting_scheduled', sa.Boolean(), nullable=False),
    sa.Column('escalated', sa.Boolean(), nullable=False),
    sa.Column('summarization_triggered', sa.Boolean(), nullable=False),
    sa.Column('total_tokens_in', sa.Integer(), nullable=False),
    sa.Column('total_tokens_out', sa.Integer(), nullable=False),
    sa.Column('total_latency_ms', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['client_phone'], ['client.phone_num'], ),
    sa.PrimaryKeyConstraint('session_id')
    )
    op.create_table('escalations',
    sa.Column('escalation_id', sa.UUID(), nullable=False),
    sa.Column('client_phone', sa.VARCHAR(), nullable=False),
    sa.Column('triggered_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('reason', sa.TEXT(), nullable=False),
    sa.Column('conversation_summary', sa.TEXT(), nullable=False),
    sa.Column('last_client_message', sa.TEXT(), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'RESOLVED', 'DISMISSED', name='escalationstatus', create_type=False), nullable=False),
    sa.Column('resolved_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('resolution_notes', sa.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['client_phone'], ['client.phone_num'], ),
    sa.PrimaryKeyConstraint('escalation_id')
    )
    op.create_table('meetings',
    sa.Column('meeting_id', sa.UUID(), nullable=False),
    sa.Column('client_phone', sa.VARCHAR(), nullable=False),
    sa.Column('meeting_type', sa.Enum('VIRTUAL_CONSULTATION', 'PROPERTY_TOUR', 'DOCUMENT_SIGNING', 'FOLLOWUP', name='meetingtype', create_type=False), nullable=False),
    sa.Column('zoom_meeting_id', sa.VARCHAR(), nullable=True),
    sa.Column('zoom_join_url', sa.VARCHAR(), nullable=True),
    sa.Column('calendar_event_id', sa.VARCHAR(), nullable=True),
    sa.Column('start_time', postgresql.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('end_time', postgresql.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('client_timezone', sa.VARCHAR(), nullable=False),
    sa.Column('duration_minutes', sa.INTEGER(), nullable=False),
    sa.Column('status', sa.Enum('SCHEDULED', 'COMPLETED', 'CANCELLED', 'NO_SHOW', name='meetingstatus', create_type=False), nullable=False),
    sa.Column('notes', sa.TEXT(), nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('cancelled_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('cancellation_reason', sa.TEXT(), nullable=True),
    sa.Column('meeting_format', sa.VARCHAR(), server_default='virtual', nullable=False),
    sa.Column('conversation_summary', sa.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['client_phone'], ['client.phone_num'], ),
    sa.PrimaryKeyConstraint('meeting_id')
    )
    op.create_table('security_questions',
    sa.Column('question_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('question', sa.TEXT(), nullable=False),
    sa.Column('answer_hash', sa.TEXT(), nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('question_id')
    )
    op.create_table('token_logs',
    sa.Column('log_id', sa.UUID(), nullable=False),
    sa.Column('client_phone', sa.VARCHAR(), nullable=True),
    sa.Column('session_id', sa.UUID(), nullable=True),
    sa.Column('node_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('model_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('tokens_in', sa.Integer(), nullable=False),
    sa.Column('tokens_out', sa.Integer(), nullable=False),
    sa.Column('latency_ms', sa.Integer(), nullable=False),
    sa.Column('cost_usd', sa.NUMERIC(precision=10, scale=6), nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['conversation_sessions.session_id'], ),
    sa.PrimaryKeyConstraint('log_id')
    )
    op.create_table('tool_execution_logs',
    sa.Column('log_id', sa.UUID(), nullable=False),
    sa.Column('client_phone', sa.VARCHAR(), nullable=True),
    sa.Column('session_id', sa.UUID(), nullable=True),
    sa.Column('tool_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('success', sa.Boolean(), nullable=False),
    sa.Column('error_message', sa.TEXT(), nullable=True),
    sa.Column('execution_time_ms', sa.Integer(), nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['conversation_sessions.session_id'], ),
    sa.PrimaryKeyConstraint('log_id')
    )
    op.create_table('transcripts',
    sa.Column('transcript_id', sa.UUID(), nullable=False),
    sa.Column('session_id', sa.UUID(), nullable=False),
    sa.Column('client_phone', sa.VARCHAR(), nullable=False),
    sa.Column('message_content', sa.TEXT(), nullable=False),
    sa.Column('message_type', sa.VARCHAR(), nullable=False),
    sa.Column('timestamp', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('tokens_used', sa.INTEGER(), nullable=True),
    sa.Column('processing_time_ms', sa.INTEGER(), nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['client_phone'], ['client.phone_num'], ),
    sa.ForeignKeyConstraint(['session_id'], ['conversation_sessions.session_id'], ),
    sa.PrimaryKeyConstraint('transcript_id')
    )
    op.create_index('ix_transcripts_session_id', 'transcripts', ['session_id'], unique=False)
    op.create_index('ix_transcripts_client_phone', 'transcripts', ['client_phone'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_transcripts_client_phone', table_name='transcripts')
    op.drop_index('ix_transcripts_session_id', table_name='transcripts')
    op.drop_table('transcripts')
    op.drop_table('tool_execution_logs')
    op.drop_table('token_logs')
    op.drop_table('security_questions')
    op.drop_table('meetings')
    op.drop_table('escalations')
    op.drop_table('conversation_sessions')
    op.drop_table('client_property_views')
    op.drop_table('client_documents')
    op.drop_table('user')
    op.drop_table('property')
    op.drop_table('error_logs')
    op.drop_table('company_documents')
    op.drop_table('client')