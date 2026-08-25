"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-08-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


provider_status = postgresql.ENUM(
    'PENDING',
    'APPROVED',
    'ACTIVE',
    'SUSPENDED',
    'DEACTIVATED',
    name='providerstatus',
    create_type=False,
)
availability_status = postgresql.ENUM(
    'ACTIVE',
    'INACTIVE',
    'OUT_OF_STOCK',
    name='availabilitystatus',
    create_type=False,
)


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE providerstatus AS ENUM ('PENDING', 'APPROVED', 'ACTIVE', 'SUSPENDED', 'DEACTIVATED');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE availabilitystatus AS ENUM ('ACTIVE', 'INACTIVE', 'OUT_OF_STOCK');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('product_id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('unit', sa.String(length=32), nullable=False),
        sa.Column('npk_ratio', sa.String(length=32), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('product_id', name='uq_products_product_id'),
    )
    op.create_index('ix_products_id', 'products', ['id'])
    op.create_index('ix_products_product_id', 'products', ['product_id'])

    op.create_table(
        'providers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('provider_code', sa.String(length=64), nullable=False),
        sa.Column('provider_name', sa.String(length=255), nullable=False),
        sa.Column('login_username', sa.String(length=128), nullable=False),
        sa.Column('status', provider_status, nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('provider_code', name='uq_providers_provider_code'),
        sa.UniqueConstraint('login_username', name='uq_providers_login_username'),
    )
    op.create_index('ix_providers_id', 'providers', ['id'])
    op.create_index('ix_providers_provider_code', 'providers', ['provider_code'])
    op.create_index('ix_providers_login_username', 'providers', ['login_username'])

    op.create_table(
        'provider_offerings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('listing_id', sa.String(length=64), nullable=False),
        sa.Column('sku', sa.String(length=64), nullable=False),
        sa.Column('provider_id', sa.Integer(), sa.ForeignKey('providers.id'), nullable=False),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('price', sa.Numeric(12, 2), nullable=False),
        sa.Column('stock', sa.Integer(), nullable=False),
        sa.Column('availability', availability_status, nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('listing_id', name='uq_provider_offerings_listing_id'),
        sa.UniqueConstraint('provider_id', 'product_id', name='uq_provider_product'),
        sa.UniqueConstraint('provider_id', 'sku', name='uq_provider_sku'),
    )
    op.create_index('ix_provider_offerings_id', 'provider_offerings', ['id'])
    op.create_index('ix_provider_offerings_listing_id', 'provider_offerings', ['listing_id'])


def downgrade() -> None:
    op.drop_index('ix_provider_offerings_listing_id', table_name='provider_offerings')
    op.drop_index('ix_provider_offerings_id', table_name='provider_offerings')
    op.drop_table('provider_offerings')

    op.drop_index('ix_providers_login_username', table_name='providers')
    op.drop_index('ix_providers_provider_code', table_name='providers')
    op.drop_index('ix_providers_id', table_name='providers')
    op.drop_table('providers')

    op.drop_index('ix_products_product_id', table_name='products')
    op.drop_index('ix_products_id', table_name='products')
    op.drop_table('products')

    op.execute('DROP TYPE IF EXISTS availabilitystatus')
    op.execute('DROP TYPE IF EXISTS providerstatus')
