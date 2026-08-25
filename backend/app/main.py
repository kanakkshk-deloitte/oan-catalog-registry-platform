from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import AuthContext, exchange_password_for_token, require_admin, require_provider
from app.config import settings
from app.database import get_db
from app.models import AvailabilityStatus, Category, Product, Provider, ProviderOffering, ProviderStatus
from app.schemas import (
    BecknCatalog,
    BecknContext,
    BecknDescriptor,
    BecknIntent,
    BecknItem,
    BecknMessage,
    BecknOnSearchResponse,
    BecknPrice,
    BecknProvider,
    BecknQuantity,
    BecknSearchMessage,
    BecknSearchRequest,
    CategoryCreate,
    CategoryOut,
    CategoryStatusUpdate,
    DiscoveryItem,
    OfferingCreate,
    OfferingOut,
    OfferingUpdate,
    ProductCreate,
    ProductOut,
    ProductStatusUpdate,
    ProviderCreate,
    ProviderOut,
    ProviderStatusUpdate,
    TokenRequest,
    TokenResponse,
)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.post('/auth/token', response_model=TokenResponse)
async def get_token(payload: TokenRequest):
    token = await exchange_password_for_token(payload.username, payload.password)
    return TokenResponse(
        access_token=token['access_token'],
        token_type=token.get('token_type', 'Bearer'),
        expires_in=token.get('expires_in', 300),
    )


@app.post('/admin/products', response_model=ProductOut)
def create_product(payload: ProductCreate, db: Session = Depends(get_db), _: AuthContext = Depends(require_admin)):
    product = Product(**payload.model_dump())
    db.add(product)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail='Product ID already exists') from exc
    db.refresh(product)
    return product


@app.get('/admin/products', response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db), _: AuthContext = Depends(require_admin)):
    return db.execute(select(Product).order_by(Product.id.desc())).scalars().all()


@app.patch('/admin/products/{product_id}/status', response_model=ProductOut)
def update_product_status(
    product_id: str,
    payload: ProductStatusUpdate,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_admin),
):
    product = db.execute(select(Product).where(Product.product_id == product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    product.is_active = payload.is_active
    db.commit()
    db.refresh(product)
    return product


@app.post('/admin/providers', response_model=ProviderOut)
def create_provider(payload: ProviderCreate, db: Session = Depends(get_db), _: AuthContext = Depends(require_admin)):
    provider = Provider(**payload.model_dump(), status='PENDING')
    db.add(provider)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail='Provider code or login username already exists') from exc
    db.refresh(provider)
    return provider


@app.get('/admin/providers', response_model=List[ProviderOut])
def list_providers(db: Session = Depends(get_db), _: AuthContext = Depends(require_admin)):
    return db.execute(select(Provider).order_by(Provider.id.desc())).scalars().all()


@app.patch('/admin/providers/{provider_code}/status', response_model=ProviderOut)
def update_provider_status(
    provider_code: str,
    payload: ProviderStatusUpdate,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_admin),
):
    provider = db.execute(select(Provider).where(Provider.provider_code == provider_code)).scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail='Provider not found')
    provider.status = payload.status
    db.commit()
    db.refresh(provider)
    return provider


@app.post('/provider/offerings', response_model=OfferingOut)
def create_offering(
    payload: OfferingCreate,
    db: Session = Depends(get_db),
    user: AuthContext = Depends(require_provider),
):
    provider = db.execute(select(Provider).where(Provider.login_username == user.username)).scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail='Provider profile not found for user')
    if provider.status != ProviderStatus.active:
        raise HTTPException(status_code=403, detail='Provider must be ACTIVE to manage offerings')

    product = db.execute(select(Product).where(and_(Product.product_id == payload.product_id, Product.is_active.is_(True)))).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail='Active product not found')

    offering = ProviderOffering(
        listing_id=payload.listing_id,
        sku=payload.sku,
        provider_id=provider.id,
        product_id=product.id,
        price=payload.price,
        stock=payload.stock,
        availability=payload.availability,
    )
    db.add(offering)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail='Duplicate product for provider or duplicate SKU/listing ID') from exc
    db.refresh(offering)
    return OfferingOut(
        listing_id=offering.listing_id,
        product_id=product.product_id,
        product_name=product.name,
        provider_code=provider.provider_code,
        provider_name=provider.provider_name,
        sku=offering.sku,
        price=offering.price,
        stock=offering.stock,
        availability=offering.availability,
    )


@app.get('/provider/offerings/me', response_model=List[OfferingOut])
def my_offerings(db: Session = Depends(get_db), user: AuthContext = Depends(require_provider)):
    provider = db.execute(select(Provider).where(Provider.login_username == user.username)).scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail='Provider profile not found for user')

    rows = db.execute(
        select(ProviderOffering, Product)
        .join(Product, Product.id == ProviderOffering.product_id)
        .where(ProviderOffering.provider_id == provider.id)
        .order_by(ProviderOffering.id.desc())
    ).all()

    return [
        OfferingOut(
            listing_id=offering.listing_id,
            product_id=product.product_id,
            product_name=product.name,
            provider_code=provider.provider_code,
            provider_name=provider.provider_name,
            sku=offering.sku,
            price=offering.price,
            stock=offering.stock,
            availability=offering.availability,
        )
        for offering, product in rows
    ]


@app.get('/provider/catalog', response_model=List[ProductOut])
def provider_catalog(db: Session = Depends(get_db), _: AuthContext = Depends(require_provider)):
    return (
        db.execute(
            select(Product)
            .where(Product.is_active.is_(True))
            .order_by(Product.name.asc())
        )
        .scalars()
        .all()
    )


@app.get('/admin/offerings', response_model=List[OfferingOut])
def admin_offerings(db: Session = Depends(get_db), _: AuthContext = Depends(require_admin)):
    rows = db.execute(
        select(ProviderOffering, Product, Provider)
        .join(Product, Product.id == ProviderOffering.product_id)
        .join(Provider, Provider.id == ProviderOffering.provider_id)
        .order_by(ProviderOffering.id.desc())
    ).all()

    return [
        OfferingOut(
            listing_id=offering.listing_id,
            product_id=product.product_id,
            product_name=product.name,
            provider_code=provider.provider_code,
            provider_name=provider.provider_name,
            sku=offering.sku,
            price=offering.price,
            stock=offering.stock,
            availability=offering.availability,
        )
        for offering, product, provider in rows
    ]


# Admin Categories endpoints
@app.post('/admin/categories', response_model=CategoryOut)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db), _: AuthContext = Depends(require_admin)):
    category = Category(**payload.model_dump())
    db.add(category)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail='Category combination already exists') from exc
    db.refresh(category)
    return category


@app.get('/admin/categories', response_model=List[CategoryOut])
def list_categories(db: Session = Depends(get_db), _: AuthContext = Depends(require_admin)):
    return db.execute(select(Category).where(Category.is_active == True).order_by(Category.supercategory, Category.category, Category.subcategory)).scalars().all()


@app.patch('/admin/categories/{category_id}/status', response_model=CategoryOut)
def update_category_status(
    category_id: int,
    payload: CategoryStatusUpdate,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_admin),
):
    category = db.execute(select(Category).where(Category.id == category_id)).scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail='Category not found')
    category.is_active = payload.is_active
    db.commit()
    db.refresh(category)
    return category


@app.delete('/admin/categories/{category_id}')
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_admin),
):
    category = db.execute(select(Category).where(Category.id == category_id)).scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail='Category not found')
    db.delete(category)
    db.commit()
    return {'message': 'Category deleted successfully'}


@app.patch('/provider/offerings/{listing_id}', response_model=OfferingOut)
def update_offering(
    listing_id: str,
    payload: OfferingUpdate,
    db: Session = Depends(get_db),
    user: AuthContext = Depends(require_provider),
):
    provider = db.execute(select(Provider).where(Provider.login_username == user.username)).scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail='Provider profile not found for user')

    offering = db.execute(
        select(ProviderOffering).where(
            and_(ProviderOffering.provider_id == provider.id, ProviderOffering.listing_id == listing_id)
        )
    ).scalar_one_or_none()

    if not offering:
        raise HTTPException(status_code=404, detail='Offering not found')

    if payload.price is not None:
        offering.price = payload.price
    if payload.stock is not None:
        offering.stock = payload.stock
        if payload.stock == 0 and offering.availability == AvailabilityStatus.active:
            offering.availability = 'OUT_OF_STOCK'
    if payload.availability is not None:
        offering.availability = payload.availability.value if isinstance(payload.availability, AvailabilityStatus) else payload.availability

    db.commit()
    db.refresh(offering)

    product = db.execute(select(Product).where(Product.id == offering.product_id)).scalar_one()
    return OfferingOut(
        listing_id=offering.listing_id,
        product_id=product.product_id,
        product_name=product.name,
        provider_code=provider.provider_code,
        provider_name=provider.provider_name,
        sku=offering.sku,
        price=offering.price,
        stock=offering.stock,
        availability=offering.availability,
    )


@app.post('/search', response_model=BecknOnSearchResponse)
def beckn_search(
    request: BecknSearchRequest,
    db: Session = Depends(get_db),
):
    """Beckn protocol compliant search endpoint for catalog discovery"""
    
    # Extract search query from intent if present
    search_query = ''
    if request.message and request.message.intent and request.message.intent.item:
        descriptor = request.message.intent.item.get('descriptor', {})
        search_query = descriptor.get('name', '')
    
    # Query active products with active providers
    rows = db.execute(
        select(Product, Provider, ProviderOffering)
        .join(ProviderOffering, ProviderOffering.product_id == Product.id)
        .join(Provider, Provider.id == ProviderOffering.provider_id)
        .where(
            and_(
                Product.is_active.is_(True),
                Provider.status == 'ACTIVE',
                ProviderOffering.availability == 'ACTIVE',
            )
        )
        .order_by(Product.name.asc())
    ).all()

    # Filter results based on search query
    result: List[DiscoveryItem] = []
    q_lower = search_query.strip().lower()
    for product, provider, offering in rows:
        haystack = f"{product.name} {product.category} {provider.provider_name} {provider.provider_code}".lower()
        if q_lower and q_lower not in haystack:
            continue
        result.append(
            DiscoveryItem(
                product_id=product.product_id,
                product_name=product.name,
                category=product.category,
                provider_code=provider.provider_code,
                provider_name=provider.provider_name,
                listing_id=offering.listing_id,
                sku=offering.sku,
                price=offering.price,
                stock=offering.stock,
                availability=offering.availability,
            )
        )
    
    # Group items by provider
    providers_map: dict[str, BecknProvider] = {}
    for item in result:
        provider = providers_map.get(item.provider_code)
        if not provider:
            provider = BecknProvider(
                id=item.provider_code,
                descriptor=BecknDescriptor(name=item.provider_name),
                items=[],
            )
            providers_map[item.provider_code] = provider

        provider.items.append(
            BecknItem(
                id=item.listing_id,
                descriptor=BecknDescriptor(name=item.product_name),
                category_id=item.category,
                price=BecknPrice(currency='INR', value=str(item.price)),
                quantity=BecknQuantity(available={'count': str(item.stock)}),
                tags={
                    'product_id': item.product_id,
                    'sku': item.sku,
                    'availability': item.availability,
                },
            )
        )

    # Build Beckn on_search response
    return BecknOnSearchResponse(
        context=BecknContext(
            domain=request.context.domain,
            country=request.context.country,
            city=request.context.city,
            action='on_search',
            core_version=request.context.core_version,
            bap_id=request.context.bap_id,
            bap_uri=request.context.bap_uri,
            bpp_id='oan-catalog-registry.local',
            bpp_uri='https://oan-catalog-registry.local',
            transaction_id=request.context.transaction_id,
            message_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
        message=BecknMessage(
            catalog=BecknCatalog(
                descriptor=BecknDescriptor(name='OAN Catalog Registry'),
                providers=list(providers_map.values()),
            )
        ),
    )
