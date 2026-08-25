import enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.database import Base


class ProviderStatus(str, enum.Enum):
    pending = 'PENDING'
    approved = 'APPROVED'
    active = 'ACTIVE'
    suspended = 'SUSPENDED'
    deactivated = 'DEACTIVATED'


class AvailabilityStatus(str, enum.Enum):
    active = 'ACTIVE'
    inactive = 'INACTIVE'
    out_of_stock = 'OUT_OF_STOCK'


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    supercategory = Column(String(128), nullable=False, comment='Top-level category (e.g., Agricultural Inputs)')
    category = Column(String(128), nullable=False, comment='Mid-level category (e.g., Fertilizers)')
    subcategory = Column(String(128), nullable=True, comment='Specific category (e.g., NPK Fertilizers)')
    description = Column(Text, nullable=True)
    unit = Column(String(32), nullable=False)
    npk_ratio = Column(String(32), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    offerings = relationship('ProviderOffering', back_populates='product')


class Provider(Base):
    __tablename__ = 'providers'

    id = Column(Integer, primary_key=True, index=True)
    provider_code = Column(String(64), unique=True, nullable=False, index=True)
    provider_name = Column(String(255), nullable=False)
    login_username = Column(String(128), unique=True, nullable=False, index=True)
    status = Column(String(20), default='PENDING', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    offerings = relationship('ProviderOffering', back_populates='provider')


class ProviderOffering(Base):
    __tablename__ = 'provider_offerings'
    __table_args__ = (
        UniqueConstraint('provider_id', 'product_id', name='uq_provider_product'),
        UniqueConstraint('provider_id', 'sku', name='uq_provider_sku'),
    )

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(String(64), unique=True, nullable=False, index=True)
    sku = Column(String(64), nullable=False)
    provider_id = Column(Integer, ForeignKey('providers.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    stock = Column(Integer, nullable=False)
    availability = Column(String(20), default='ACTIVE', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    provider = relationship('Provider', back_populates='offerings')
    product = relationship('Product', back_populates='offerings')


class Category(Base):
    __tablename__ = 'categories'
    __table_args__ = (
        UniqueConstraint('supercategory', 'category', 'subcategory', name='uq_category_hierarchy'),
    )

    id = Column(Integer, primary_key=True, index=True)
    supercategory = Column(String(128), nullable=False, index=True, comment='Top-level category')
    category = Column(String(128), nullable=False, index=True, comment='Mid-level category')
    subcategory = Column(String(128), nullable=True, index=True, comment='Specific category (optional)')
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
