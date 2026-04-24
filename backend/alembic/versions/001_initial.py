"""Initial schema - Medix AI Sprint 3

Revision ID: 001_initial
Revises: 
Create Date: 2024-12-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Universities ──────────────────────────────────────────
    op.create_table('universities',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('acronym', sa.String(50), nullable=False, unique=True),
        sa.Column('city', sa.String(100), default='Tegucigalpa'),
        sa.Column('logo_url', sa.String(500)),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )

    # ── Curriculum Periods ────────────────────────────────────
    op.create_table('curriculum_periods',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('university_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('universities.id'), nullable=False),
        sa.Column('period_name', sa.String(100), nullable=False),
        sa.Column('period_order', sa.Integer(), nullable=False),
        sa.Column('year_number', sa.Integer()),
        sa.Column('is_internship', sa.Boolean(), default=False),
        sa.Column('is_social_service', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )

    # ── Subjects ──────────────────────────────────────────────
    op.create_table('subjects',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('period_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('curriculum_periods.id'), nullable=False),
        sa.Column('code', sa.String(50)),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('credits', sa.Integer()),
        sa.Column('description', sa.Text()),
        sa.Column('ai_context_hint', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )

    # ── Users ─────────────────────────────────────────────────
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(20)),
        sa.Column('role', sa.Enum('student','medico_general','medico_especialista','admin',
                                   name='userrole'), default='student'),
        sa.Column('subscription_tier', sa.Enum('free','pro','clinical',
                                                name='subscriptiontier'), default='free'),
        sa.Column('university_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('universities.id'), nullable=True),
        sa.Column('current_period_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('curriculum_periods.id'), nullable=True),
        sa.Column('specialty', sa.String(150)),
        sa.Column('stripe_customer_id', sa.String(255)),
        sa.Column('fcm_token', sa.String(500)),
        sa.Column('chat_count_today', sa.Integer(), default=0),
        sa.Column('scan_count_today', sa.Integer(), default=0),
        sa.Column('rate_limit_reset_at', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # ── Chat Sessions ─────────────────────────────────────────
    op.create_table('chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(255)),
        sa.Column('context_subject_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('subjects.id'), nullable=True),
        sa.Column('mode', sa.String(50), default='chat'),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )

    # ── Chat Messages ─────────────────────────────────────────
    op.create_table('chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('chat_sessions.id'), nullable=False),
        sa.Column('sender_type', sa.String(50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('tokens_used', sa.String(20)),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )

    # ── Medical Scans ─────────────────────────────────────────
    op.create_table('medical_scans',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('file_url', sa.Text(), nullable=False),
        sa.Column('file_name', sa.String(255)),
        sa.Column('scan_type', sa.Enum('prescription','xray','lab_result','ecg',
                                       'ultrasound','other', name='scantype'), default='other'),
        sa.Column('ai_summary', sa.Text()),
        sa.Column('ai_findings', sa.Text()),
        sa.Column('ai_recommendations', sa.Text()),
        sa.Column('urgency_level', sa.Enum('low','medium','high','critical',
                                           name='urgencylevel')),
        sa.Column('confidence_score', sa.Float()),
        sa.Column('is_processed', sa.Boolean(), default=False),
        sa.Column('processing_error', sa.Text()),
        sa.Column('processing_time_ms', sa.Float()),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )

    # ── Analytics Events ──────────────────────────────────────
    op.create_table('analytics_events',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_role', sa.String(50)),
        sa.Column('subscription_tier', sa.String(50)),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('module', sa.String(50)),
        sa.Column('extra', postgresql.JSONB()),
        sa.Column('latency_ms', sa.Float()),
        sa.Column('tokens_used', sa.Integer()),
        sa.Column('success', sa.Boolean(), default=True),
        sa.Column('error_message', sa.Text()),
        sa.Column('platform', sa.String(50)),
        sa.Column('app_version', sa.String(20)),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_analytics_event_type', 'analytics_events', ['event_type'])
    op.create_index('ix_analytics_created_at', 'analytics_events', ['created_at'])
    op.create_index('ix_analytics_user_id', 'analytics_events', ['user_id'])

    # ── Daily Metrics ─────────────────────────────────────────
    op.create_table('daily_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('date', sa.String(10), unique=True, nullable=False),
        sa.Column('active_users', sa.Integer(), default=0),
        sa.Column('new_registrations', sa.Integer(), default=0),
        sa.Column('upgrades_to_pro', sa.Integer(), default=0),
        sa.Column('upgrades_to_clinical', sa.Integer(), default=0),
        sa.Column('cancellations', sa.Integer(), default=0),
        sa.Column('total_chat_messages', sa.Integer(), default=0),
        sa.Column('total_medscan_uploads', sa.Integer(), default=0),
        sa.Column('total_soap_notes', sa.Integer(), default=0),
        sa.Column('total_sesal_queries', sa.Integer(), default=0),
        sa.Column('total_ecoe_sessions', sa.Integer(), default=0),
        sa.Column('total_guardia_calcs', sa.Integer(), default=0),
        sa.Column('avg_chat_latency_ms', sa.Float()),
        sa.Column('avg_scan_latency_ms', sa.Float()),
        sa.Column('total_tokens_used', sa.Integer(), default=0),
        sa.Column('error_rate_pct', sa.Float()),
        sa.Column('mrr_usd', sa.Float(), default=0.0),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )

    # ── User Feedback ─────────────────────────────────────────
    op.create_table('user_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('module', sa.String(50)),
        sa.Column('message', sa.Text()),
        sa.Column('app_version', sa.String(20)),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    for table in ['user_feedback','daily_metrics','analytics_events',
                  'medical_scans','chat_messages','chat_sessions',
                  'users','subjects','curriculum_periods','universities']:
        op.drop_table(table)
    for enum in ['userrole','subscriptiontier','scantype','urgencylevel']:
        op.execute(f"DROP TYPE IF EXISTS {enum}")
