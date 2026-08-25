"""Add categories table

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-25 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    # Create categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('supercategory', sa.String(length=128), nullable=False, comment='Top-level category'),
        sa.Column('category', sa.String(length=128), nullable=False, comment='Mid-level category'),
        sa.Column('subcategory', sa.String(length=128), nullable=True, comment='Specific category (optional)'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('supercategory', 'category', 'subcategory', name='uq_category_hierarchy')
    )
    
    # Create indexes
    op.create_index(op.f('ix_categories_id'), 'categories', ['id'], unique=False)
    op.create_index(op.f('ix_categories_supercategory'), 'categories', ['supercategory'], unique=False)
    op.create_index(op.f('ix_categories_category'), 'categories', ['category'], unique=False)
    op.create_index(op.f('ix_categories_subcategory'), 'categories', ['subcategory'], unique=False)
    
    # Insert some default categories for agricultural products
    op.execute("""
        INSERT INTO categories (supercategory, category, subcategory, description, is_active) VALUES
        ('Agricultural Inputs', 'Fertilizers', 'NPK Fertilizers', 'Nitrogen-Phosphorus-Potassium fertilizers', true),
        ('Agricultural Inputs', 'Fertilizers', 'Organic Fertilizers', 'Natural organic fertilizers', true),
        ('Agricultural Inputs', 'Fertilizers', 'Micronutrient Fertilizers', 'Essential micronutrients for crops', true),
        ('Agricultural Inputs', 'Seeds', 'Vegetable Seeds', 'Seeds for vegetable crops', true),
        ('Agricultural Inputs', 'Seeds', 'Cereal Seeds', 'Seeds for cereal crops', true),
        ('Crop Protection', 'Pesticides', 'Insecticides', 'Chemical insect control', true),
        ('Crop Protection', 'Pesticides', 'Fungicides', 'Fungal disease control', true),
        ('Crop Protection', 'Pesticides', 'Herbicides', 'Weed control products', true),
        ('Farm Equipment', 'Machinery', 'Tractors', 'Agricultural tractors', true),
        ('Farm Equipment', 'Tools', 'Hand Tools', 'Manual farming tools', true)
    """)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_categories_subcategory'), table_name='categories')
    op.drop_index(op.f('ix_categories_category'), table_name='categories')
    op.drop_index(op.f('ix_categories_supercategory'), table_name='categories')
    op.drop_index(op.f('ix_categories_id'), table_name='categories')
    
    # Drop table
    op.drop_table('categories')
