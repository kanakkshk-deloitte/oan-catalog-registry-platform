from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models import AvailabilityStatus, ProviderStatus


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


class ProductCreate(BaseModel):
    product_id: str = Field(min_length=3)
    name: str
    supercategory: str
    category: str
    subcategory: Optional[str] = None
    description: Optional[str] = None
    unit: str
    npk_ratio: Optional[str] = None
    is_active: bool = True


class ProductOut(BaseModel):
    id: int
    product_id: str
    name: str
    supercategory: str
    category: str
    subcategory: Optional[str]
    description: Optional[str]
    unit: str
    npk_ratio: Optional[str]
    is_active: bool

    model_config = {'from_attributes': True}


class ProductStatusUpdate(BaseModel):
    is_active: bool


class ProviderCreate(BaseModel):
    provider_code: str
    provider_name: str
    login_username: str
    login_password: str = Field(default='provider123', min_length=8)


class ProviderStatusUpdate(BaseModel):
    status: ProviderStatus


class ProviderOut(BaseModel):
    id: int
    provider_code: str
    provider_name: str
    login_username: str
    status: ProviderStatus

    model_config = {'from_attributes': True}


class OfferingCreate(BaseModel):
    listing_id: str
    sku: str
    product_id: str
    price: Decimal
    stock: int = Field(ge=0)
    availability: AvailabilityStatus


class OfferingUpdate(BaseModel):
    price: Optional[Decimal] = None
    stock: Optional[int] = Field(default=None, ge=0)
    availability: Optional[AvailabilityStatus] = None


class OfferingOut(BaseModel):
    listing_id: str
    product_id: str
    product_name: str
    provider_code: str
    provider_name: str
    sku: str
    price: Decimal
    stock: int
    availability: AvailabilityStatus


class DiscoveryItem(BaseModel):
    product_id: str
    product_name: str
    category: str
    provider_code: str
    provider_name: str
    listing_id: str
    sku: str
    price: Decimal
    stock: int
    availability: AvailabilityStatus


class BecknContext(BaseModel):
    domain: str
    country: str | None = None
    city: str | None = None
    action: str
    core_version: str | None = Field(default=None)  # Make optional with explicit default
    version: str | None = Field(default=None)  # Make optional with explicit default
    bap_id: str
    bap_uri: str
    bpp_id: str | None = None
    bpp_uri: str | None = None
    transaction_id: str
    message_id: str
    timestamp: str
    ttl: str | None = None
    location: dict | None = None  # Accept location object
    
    model_config = {"extra": "allow"}  # Allow extra fields
    
    @model_validator(mode='after')
    def set_core_version(self):
        # If version is provided but core_version is not, copy version to core_version
        if self.version and not self.core_version:
            self.core_version = self.version
        # If core_version is provided but version is not, copy core_version to version
        elif self.core_version and not self.version:
            self.version = self.core_version
        # Ensure at least one is set
        if not self.core_version and not self.version:
            raise ValueError("Either 'version' or 'core_version' must be provided")
        return self


class BecknIntent(BaseModel):
    item: Optional[dict] = None
    category: Optional[dict] = None
    fulfillment: Optional[dict] = None


class BecknSearchMessage(BaseModel):
    intent: Optional[BecknIntent] = None


class BecknSearchRequest(BaseModel):
    context: BecknContext
    message: Optional[BecknSearchMessage] = None


class BecknDescriptor(BaseModel):
    name: str


class BecknPrice(BaseModel):
    currency: str
    value: str


class BecknQuantity(BaseModel):
    available: dict


class BecknItem(BaseModel):
    id: str
    descriptor: BecknDescriptor
    category_id: str
    price: BecknPrice
    quantity: BecknQuantity
    tags: dict


class BecknProvider(BaseModel):
    id: str
    descriptor: BecknDescriptor
    items: list[BecknItem]


class BecknCatalog(BaseModel):
    descriptor: BecknDescriptor
    providers: list[BecknProvider]


class BecknMessage(BaseModel):
    catalog: BecknCatalog


class BecknOnSearchResponse(BaseModel):
    context: BecknContext
    message: BecknMessage


# Category Schemas
class CategoryCreate(BaseModel):
    supercategory: str = Field(min_length=1, max_length=128)
    category: str = Field(min_length=1, max_length=128)
    subcategory: Optional[str] = Field(None, max_length=128)
    description: Optional[str] = None
    is_active: bool = True


class CategoryOut(BaseModel):
    id: int
    supercategory: str
    category: str
    subcategory: Optional[str]
    description: Optional[str]
    is_active: bool

    model_config = {'from_attributes': True}


class CategoryStatusUpdate(BaseModel):
    is_active: bool
