"""Initial fulfillment ticket schema

Revision ID: 48ea33bd6d47
Revises: 
Create Date: 2025-12-21 07:22:06.904380

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '48ea33bd6d47'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create ENUM types
    op.execute("CREATE TYPE ticketstatus AS ENUM ('new', 'in_progress', 'pending', 'resolved', 'closed', 'cancelled')")
    op.execute("CREATE TYPE fulfillmentstate AS ENUM ('not_started', 'processing', 'shipped', 'delivered', 'failed', 'refunded')")
    op.execute("CREATE TYPE claimstatus AS ENUM ('open', 'investigating', 'approved', 'denied', 'closed')")
    op.execute("CREATE TYPE actiontype AS ENUM ('created', 'updated', 'status_changed', 'assigned', 'comment_added', 'label_added', 'label_removed', 'claim_created', 'claim_updated', 'moved')")
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=200), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])
    
    # Create marketplaces table
    op.create_table('marketplaces',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('code')
    )
    op.create_index('ix_marketplaces_name', 'marketplaces', ['name'])
    
    # Create categories table
    op.create_table('categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('marketplace_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['marketplace_id'], ['marketplaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('marketplace_id', 'code', name='uq_marketplace_category_code')
    )
    op.create_index('ix_categories_name', 'categories', ['name'])
    op.create_index('ix_category_marketplace_id', 'categories', ['marketplace_id'])
    
    # Create folders table
    op.create_table('folders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('path', sa.String(length=1000), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['folders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_folders_name', 'folders', ['name'])
    op.create_index('ix_folder_parent_id', 'folders', ['parent_id'])
    op.create_index('ix_folder_category_id', 'folders', ['category_id'])
    op.create_index('ix_folder_path', 'folders', ['path'])
    
    # Create labels table
    op.create_table('labels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_labels_name', 'labels', ['name'])
    
    # Create tickets table
    op.create_table('tickets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('folder_id', sa.Integer(), nullable=False),
        sa.Column('ticket_number', sa.String(length=50), nullable=False),
        sa.Column('email_message_id', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('from_address', sa.String(length=255), nullable=False),
        sa.Column('from_name', sa.String(length=255), nullable=True),
        sa.Column('body_text', sa.Text(), nullable=True),
        sa.Column('body_html', sa.Text(), nullable=True),
        sa.Column('headers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.Enum('NEW', 'IN_PROGRESS', 'PENDING', 'RESOLVED', 'CLOSED', 'CANCELLED', name='ticketstatus'), nullable=False, server_default='new'),
        sa.Column('fulfillment_state', sa.Enum('NOT_STARTED', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'FAILED', 'REFUNDED', name='fulfillmentstate'), nullable=False, server_default='not_started'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('received_date', sa.DateTime(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ticket_number')
    )
    op.create_index('ix_tickets_ticket_number', 'tickets', ['ticket_number'])
    op.create_index('ix_tickets_email_message_id', 'tickets', ['email_message_id'])
    op.create_index('ix_tickets_from_address', 'tickets', ['from_address'])
    op.create_index('ix_ticket_folder_id', 'tickets', ['folder_id'])
    op.create_index('ix_ticket_status', 'tickets', ['status'])
    op.create_index('ix_ticket_created_at', 'tickets', ['created_at'])
    op.create_index('ix_ticket_assigned_to_id', 'tickets', ['assigned_to_id'])
    
    # Create ticket_labels association table
    op.create_table('ticket_labels',
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('label_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['label_id'], ['labels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('ticket_id', 'label_id')
    )
    
    # Create claims table
    op.create_table('claims',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('claim_number', sa.String(length=50), nullable=False),
        sa.Column('claim_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.Enum('OPEN', 'INVESTIGATING', 'APPROVED', 'DENIED', 'CLOSED', name='claimstatus'), nullable=False, server_default='open'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('claim_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('approved_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('resolved_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['resolved_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('claim_number')
    )
    op.create_index('ix_claims_claim_number', 'claims', ['claim_number'])
    op.create_index('ix_claim_ticket_id', 'claims', ['ticket_id'])
    op.create_index('ix_claim_status', 'claims', ['status'])
    
    # Create actions table
    op.create_table('actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action_type', sa.Enum('CREATED', 'UPDATED', 'STATUS_CHANGED', 'ASSIGNED', 'COMMENT_ADDED', 'LABEL_ADDED', 'LABEL_REMOVED', 'CLAIM_CREATED', 'CLAIM_UPDATED', 'MOVED', name='actiontype'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('old_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_action_ticket_id', 'actions', ['ticket_id'])
    op.create_index('ix_action_created_at', 'actions', ['created_at'])
    op.create_index('ix_action_type', 'actions', ['action_type'])
    
    # Create sales_orders table
    op.create_table('sales_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('sales_id', sa.String(length=100), nullable=False),
        sa.Column('purchase_order', sa.String(length=100), nullable=True),
        sa.Column('order_number', sa.String(length=100), nullable=True),
        sa.Column('order_date', sa.DateTime(), nullable=True),
        sa.Column('ship_date', sa.DateTime(), nullable=True),
        sa.Column('delivery_date', sa.DateTime(), nullable=True),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('payment_status', sa.String(length=50), nullable=True),
        sa.Column('payment_reference', sa.String(length=100), nullable=True),
        sa.Column('transaction_id', sa.String(length=100), nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('paid_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('refund_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sales_order_ticket_id', 'sales_orders', ['ticket_id'])
    op.create_index('ix_sales_order_sales_id', 'sales_orders', ['sales_id'])
    op.create_index('ix_sales_orders_purchase_order', 'sales_orders', ['purchase_order'])
    op.create_index('ix_sales_orders_order_number', 'sales_orders', ['order_number'])
    op.create_index('ix_sales_orders_transaction_id', 'sales_orders', ['transaction_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('sales_orders')
    op.drop_table('actions')
    op.drop_table('claims')
    op.drop_table('ticket_labels')
    op.drop_table('tickets')
    op.drop_table('labels')
    op.drop_table('folders')
    op.drop_table('categories')
    op.drop_table('marketplaces')
    op.drop_table('users')
    
    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS actiontype")
    op.execute("DROP TYPE IF EXISTS claimstatus")
    op.execute("DROP TYPE IF EXISTS fulfillmentstate")
    op.execute("DROP TYPE IF EXISTS ticketstatus")

