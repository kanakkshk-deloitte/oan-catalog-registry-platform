"""Add category hierarchy

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new category columns
    op.add_column('products', sa.Column('supercategory', sa.String(length=128), nullable=True, comment='Top-level category (e.g., Agricultural Inputs)'))
    op.add_column('products', sa.Column('subcategory', sa.String(length=128), nullable=True, comment='Specific category (e.g., NPK Fertilizers)'))
    
    # Migrate existing data: use current category as both supercategory and category
    op.execute("UPDATE products SET supercategory = category WHERE supercategory IS NULL")
    
    # Make supercategory not nullable after migration
    op.alter_column('products', 'supercategory', nullable=False)
    
    # Update category column comment
    op.alter_column('products', 'category', comment='Mid-level category (e.g., Fertilizers)')


def downgrade() -> None:
    op.drop_column('products', 'subcategory')
    op.drop_column('products', 'supercategory')
