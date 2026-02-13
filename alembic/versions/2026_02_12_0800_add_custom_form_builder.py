"""Add custom form builder support

Revision ID: form_builder_001
Revises: fc684229a033
Create Date: 2026-02-12 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'form_builder_001'
down_revision = 'fc684229a033'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to forms table for custom form builder
    op.add_column('forms', sa.Column('type', sa.String(), nullable=True, default='DOCUMENT'))
    op.add_column('forms', sa.Column('external_url', sa.String(), nullable=True))
    op.add_column('forms', sa.Column('fields', sa.JSON(), nullable=True))
    op.add_column('forms', sa.Column('settings', sa.JSON(), nullable=True))
    op.add_column('forms', sa.Column('is_published', sa.Boolean(), default=False))
    op.add_column('forms', sa.Column('share_link', sa.String(), nullable=True))
    op.add_column('forms', sa.Column('embed_code', sa.Text(), nullable=True))
    op.add_column('forms', sa.Column('views_count', sa.Integer(), default=0))
    op.add_column('forms', sa.Column('submissions_count', sa.Integer(), default=0))
    op.add_column('forms', sa.Column('created_by', sa.Integer(), nullable=True))
    
    # Make file_url nullable (for custom forms that don't have files)
    op.alter_column('forms', 'file_url', nullable=True)
    
    # Create new table for form submissions with JSONB data
    op.create_table('custom_form_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('form_id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('submitted_data', sa.JSON(), nullable=False),
        sa.Column('submitter_email', sa.String(), nullable=True),
        sa.Column('submitter_name', sa.String(), nullable=True),
        sa.Column('submitter_phone', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('status', sa.String(), default='NEW'),
        sa.Column('is_read', sa.Boolean(), default=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('converted_to_booking_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['form_id'], ['forms.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ),
        sa.ForeignKeyConstraint(['converted_to_booking_id'], ['bookings.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_custom_form_submissions_id'), 'custom_form_submissions', ['id'], unique=False)
    op.create_index(op.f('ix_custom_form_submissions_submitter_email'), 'custom_form_submissions', ['submitter_email'], unique=False)
    op.create_index(op.f('ix_custom_form_submissions_form_id'), 'custom_form_submissions', ['form_id'], unique=False)
    
    # Create index on share_link for fast lookups
    op.create_index(op.f('ix_forms_share_link'), 'forms', ['share_link'], unique=True)
    
    # Create leads table for form submissions
    op.create_table('leads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('form_submission_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('source', sa.String(), default='FORM'),
        sa.Column('status', sa.String(), default='NEW'),
        sa.Column('score', sa.Integer(), default=0),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('last_contacted', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.ForeignKeyConstraint(['form_submission_id'], ['custom_form_submissions.id'], ),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_leads_id'), 'leads', ['id'], unique=False)
    op.create_index(op.f('ix_leads_email'), 'leads', ['email'], unique=False)


def downgrade() -> None:
    # Remove new columns from forms table
    op.drop_column('forms', 'type')
    op.drop_column('forms', 'external_url')
    op.drop_column('forms', 'fields')
    op.drop_column('forms', 'settings')
    op.drop_column('forms', 'is_published')
    op.drop_column('forms', 'share_link')
    op.drop_column('forms', 'embed_code')
    op.drop_column('forms', 'views_count')
    op.drop_column('forms', 'submissions_count')
    op.drop_column('forms', 'created_by')
    
    # Make file_url required again
    op.alter_column('forms', 'file_url', nullable=False)
    
    # Drop new tables
    op.drop_table('leads')
    op.drop_table('custom_form_submissions')
    
    # Drop indexes
    op.drop_index(op.f('ix_forms_share_link'), table_name='forms')