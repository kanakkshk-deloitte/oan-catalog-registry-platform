from datetime import datetime, timezone
import json
import logging
from typing import List
from uuid import uuid4

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import httpx

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
    ChangePasswordRequest,
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
logger = logging.getLogger('uvicorn.error')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.middleware('http')
async def log_search_raw_body(request: Request, call_next):
    if request.url.path == '/search':
        raw_body = await request.body()
        body_text = raw_body.decode('utf-8', errors='replace') if raw_body else ''
        logger.info(
            'search raw body bytes=%s content_type=%s content_length=%s user_agent=%s body=%s',
            len(raw_body),
            request.headers.get('content-type', ''),
            request.headers.get('content-length', ''),
            request.headers.get('user-agent', ''),
            body_text,
        )

        # Re-inject body so downstream handlers and validators can read it.
        async def receive():
            return {'type': 'http.request', 'body': raw_body, 'more_body': False}

        request = Request(request.scope, receive)

    return await call_next(request)


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    raw_body = await request.body()
    body_text = raw_body.decode('utf-8', errors='replace') if raw_body else ''

    # Keep logs concise but actionable for 422 debugging.
    logger.error(
        '422 validation failed path=%s method=%s client=%s content_type=%s content_length=%s user_agent=%s errors=%s body=%s',
        request.url.path,
        request.method,
        request.client.host if request.client else 'unknown',
        request.headers.get('content-type', ''),
        request.headers.get('content-length', ''),
        request.headers.get('user-agent', ''),
        json.dumps(exc.errors(), ensure_ascii=True),
        body_text,
    )

    return JSONResponse(status_code=422, content={'detail': exc.errors()})


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


@app.post('/auth/change-password')
async def change_password(
    payload: ChangePasswordRequest,
    user: AuthContext = Depends(require_provider),
):
    try:
        await exchange_password_for_token(user.username, payload.current_password)
    except HTTPException as exc:
        if exc.status_code == 401:
            raise HTTPException(status_code=400, detail='Current password is invalid') from exc
        raise

    admin_token_url = (
        f"{settings.keycloak_base_url}/realms/"
        f"{settings.keycloak_admin_realm}/protocol/openid-connect/token"
    )
    admin_form = {
        'grant_type': 'password',
        'client_id': settings.keycloak_admin_client_id,
        'username': settings.keycloak_admin_username,
        'password': settings.keycloak_admin_password,
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        admin_token_resp = await client.post(admin_token_url, data=admin_form)
        if admin_token_resp.status_code != 200:
            logger.error(
                'Keycloak admin token request failed status=%s body=%s',
                admin_token_resp.status_code,
                admin_token_resp.text,
            )
            raise HTTPException(status_code=500, detail='Failed to authenticate with Keycloak admin API')

        admin_access_token = admin_token_resp.json().get('access_token', '')
        if not admin_access_token:
            raise HTTPException(status_code=500, detail='Missing Keycloak admin access token')

        admin_headers = {'Authorization': f'Bearer {admin_access_token}'}
        users_url = f"{settings.keycloak_base_url}/admin/realms/{settings.keycloak_realm}/users"
        users_resp = await client.get(users_url, headers=admin_headers, params={'username': user.username, 'exact': 'true'})
        if users_resp.status_code != 200:
            logger.error('Keycloak user lookup failed status=%s body=%s', users_resp.status_code, users_resp.text)
            raise HTTPException(status_code=500, detail='Failed to lookup provider user in Keycloak')

        users = users_resp.json()
        keycloak_user = next((entry for entry in users if entry.get('username') == user.username), None)
        if not keycloak_user:
            raise HTTPException(status_code=404, detail='Provider user not found in Keycloak')

        user_id = keycloak_user.get('id')
        if not user_id:
            raise HTTPException(status_code=500, detail='Invalid Keycloak user record')

        reset_url = f"{settings.keycloak_base_url}/admin/realms/{settings.keycloak_realm}/users/{user_id}/reset-password"
        reset_body = {
            'type': 'password',
            'temporary': False,
            'value': payload.new_password,
        }
        reset_resp = await client.put(reset_url, headers={**admin_headers, 'Content-Type': 'application/json'}, json=reset_body)
        if reset_resp.status_code != 204:
            logger.error('Keycloak reset password failed status=%s body=%s', reset_resp.status_code, reset_resp.text)
            if reset_resp.status_code in (400, 409):
                raise HTTPException(status_code=400, detail='Password policy failed')
            raise HTTPException(status_code=500, detail='Failed to update password in Keycloak')

    return {'message': 'Password updated successfully'}


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
async def create_provider(payload: ProviderCreate, db: Session = Depends(get_db), _: AuthContext = Depends(require_admin)):
    existing_provider = db.execute(select(Provider).where(Provider.provider_code == payload.provider_code)).scalar_one_or_none()
    if existing_provider:
        raise HTTPException(status_code=409, detail='Provider code already exists')

    existing_login = db.execute(select(Provider).where(Provider.login_username == payload.login_username)).scalar_one_or_none()
    if existing_login:
        raise HTTPException(status_code=409, detail='Login username already exists')

    admin_token_url = (
        f"{settings.keycloak_base_url}/realms/"
        f"{settings.keycloak_admin_realm}/protocol/openid-connect/token"
    )

    async with httpx.AsyncClient(timeout=20.0) as client:
        admin_token_resp = await client.post(
            admin_token_url,
            data={
                'grant_type': 'password',
                'client_id': settings.keycloak_admin_client_id,
                'username': settings.keycloak_admin_username,
                'password': settings.keycloak_admin_password,
            },
        )
        if admin_token_resp.status_code != 200:
            logger.error('Keycloak admin token failed status=%s body=%s', admin_token_resp.status_code, admin_token_resp.text)
            raise HTTPException(status_code=500, detail='Unable to authenticate with Keycloak admin API')

        admin_access_token = admin_token_resp.json().get('access_token', '')
        if not admin_access_token:
            raise HTTPException(status_code=500, detail='Missing Keycloak admin token')

        admin_headers = {'Authorization': f'Bearer {admin_access_token}'}

        # Ensure user exists in Keycloak.
        users_url = f"{settings.keycloak_base_url}/admin/realms/{settings.keycloak_realm}/users"
        lookup_resp = await client.get(users_url, headers=admin_headers, params={'username': payload.login_username, 'exact': 'true'})
        if lookup_resp.status_code != 200:
            logger.error('Keycloak user lookup failed status=%s body=%s', lookup_resp.status_code, lookup_resp.text)
            raise HTTPException(status_code=500, detail='Unable to lookup Keycloak user')

        keycloak_users = lookup_resp.json()
        keycloak_user = next((entry for entry in keycloak_users if entry.get('username') == payload.login_username), None)

        if not keycloak_user:
            names = payload.provider_name.strip().split()
            first_name = names[0] if names else payload.login_username
            last_name = ' '.join(names[1:]) if len(names) > 1 else ''
            create_user_resp = await client.post(
                users_url,
                headers={**admin_headers, 'Content-Type': 'application/json'},
                json={
                    'username': payload.login_username,
                    'enabled': True,
                    'email': f"{payload.login_username}@oan.local",
                    'emailVerified': True,
                    'firstName': first_name,
                    'lastName': last_name,
                    'requiredActions': [],
                },
            )
            if create_user_resp.status_code not in (201, 204):
                logger.error('Keycloak user create failed status=%s body=%s', create_user_resp.status_code, create_user_resp.text)
                raise HTTPException(status_code=500, detail='Unable to create Keycloak user')

            lookup_resp = await client.get(users_url, headers=admin_headers, params={'username': payload.login_username, 'exact': 'true'})
            if lookup_resp.status_code != 200:
                raise HTTPException(status_code=500, detail='Unable to lookup newly created Keycloak user')
            keycloak_users = lookup_resp.json()
            keycloak_user = next((entry for entry in keycloak_users if entry.get('username') == payload.login_username), None)

        if not keycloak_user or not keycloak_user.get('id'):
            raise HTTPException(status_code=500, detail='Invalid Keycloak user record')

        keycloak_user_id = keycloak_user['id']

        reset_password_resp = await client.put(
            f"{settings.keycloak_base_url}/admin/realms/{settings.keycloak_realm}/users/{keycloak_user_id}/reset-password",
            headers={**admin_headers, 'Content-Type': 'application/json'},
            json={
                'type': 'password',
                'temporary': False,
                'value': payload.login_password,
            },
        )
        if reset_password_resp.status_code != 204:
            logger.error('Keycloak password set failed status=%s body=%s', reset_password_resp.status_code, reset_password_resp.text)
            raise HTTPException(status_code=500, detail='Unable to set provider password in Keycloak')

        clients_resp = await client.get(
            f"{settings.keycloak_base_url}/admin/realms/{settings.keycloak_realm}/clients",
            headers=admin_headers,
            params={'clientId': settings.keycloak_client_id},
        )
        if clients_resp.status_code != 200:
            logger.error('Keycloak client lookup failed status=%s body=%s', clients_resp.status_code, clients_resp.text)
            raise HTTPException(status_code=500, detail='Unable to lookup Keycloak client')
        clients = clients_resp.json()
        if not clients:
            raise HTTPException(status_code=500, detail='Keycloak client not found')

        client_uuid = clients[0].get('id')
        if not client_uuid:
            raise HTTPException(status_code=500, detail='Invalid Keycloak client record')

        provider_role_resp = await client.get(
            f"{settings.keycloak_base_url}/admin/realms/{settings.keycloak_realm}/clients/{client_uuid}/roles/provider",
            headers=admin_headers,
        )
        if provider_role_resp.status_code != 200:
            logger.error('Keycloak provider role lookup failed status=%s body=%s', provider_role_resp.status_code, provider_role_resp.text)
            raise HTTPException(status_code=500, detail='Unable to lookup provider role in Keycloak')

        provider_role = provider_role_resp.json()
        mappings_resp = await client.get(
            f"{settings.keycloak_base_url}/admin/realms/{settings.keycloak_realm}/users/{keycloak_user_id}/role-mappings/clients/{client_uuid}",
            headers=admin_headers,
        )
        if mappings_resp.status_code != 200:
            logger.error('Keycloak role mapping lookup failed status=%s body=%s', mappings_resp.status_code, mappings_resp.text)
            raise HTTPException(status_code=500, detail='Unable to verify provider role mapping')

        has_provider_role = any(role.get('name') == 'provider' for role in mappings_resp.json())
        if not has_provider_role:
            assign_resp = await client.post(
                f"{settings.keycloak_base_url}/admin/realms/{settings.keycloak_realm}/users/{keycloak_user_id}/role-mappings/clients/{client_uuid}",
                headers={**admin_headers, 'Content-Type': 'application/json'},
                json=[provider_role],
            )
            if assign_resp.status_code not in (200, 201, 204):
                logger.error('Keycloak role assignment failed status=%s body=%s', assign_resp.status_code, assign_resp.text)
                raise HTTPException(status_code=500, detail='Unable to assign provider role in Keycloak')

    provider_payload = payload.model_dump(exclude={'login_password'})
    provider = Provider(**provider_payload, status='PENDING')
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


@app.post('/search')
async def beckn_search(
    background_tasks: BackgroundTasks,
    http_request: Request,
    db: Session = Depends(get_db),
):
    """Permissive Beckn search endpoint: always ACK and process async."""

    payload: dict = {}
    try:
        parsed = await http_request.json()
        if isinstance(parsed, dict):
            payload = parsed
        else:
            logger.warning('search payload is not a JSON object: type=%s', type(parsed).__name__)
    except Exception as exc:
        logger.warning('search payload parse failed: %s', str(exc))

    context = payload.get('context', {}) if isinstance(payload, dict) else {}
    if not isinstance(context, dict):
        context = {}

    # Attempt schema validation for observability, but do not reject the request.
    try:
        typed_request = BecknSearchRequest.model_validate(payload)
        logger.info(
            'search payload received transaction_id=%s message_id=%s action=%s payload=%s',
            typed_request.context.transaction_id,
            typed_request.context.message_id,
            typed_request.context.action,
            typed_request.model_dump_json(),
        )
    except Exception as exc:
        logger.warning(
            'search payload validation skipped transaction_id=%s message_id=%s action=%s reason=%s payload=%s',
            context.get('transaction_id', ''),
            context.get('message_id', ''),
            context.get('action', ''),
            str(exc),
            json.dumps(payload, ensure_ascii=True),
        )

    # Extract incoming headers for callback
    incoming_headers = dict(http_request.headers)
    
    # Queue background task to process search and callback
    background_tasks.add_task(
        process_search_and_callback,
        payload,
        incoming_headers,
        db
    )
    
    # Return immediate acknowledgement (Beckn standard)
    return {
        "message": {
            "ack": {
                "status": "ACK"
            }
        }
    }


async def process_search_and_callback(
    request_payload: dict,
    incoming_headers: dict,
    db: Session
):
    """Process catalog search and POST callback to BAP's on_search endpoint"""
    
    try:
        context = request_payload.get('context', {}) if isinstance(request_payload, dict) else {}
        message = request_payload.get('message', {}) if isinstance(request_payload, dict) else {}
        if not isinstance(context, dict):
            context = {}
        if not isinstance(message, dict):
            message = {}

        # Extract search query from intent if present
        search_query = ''
        intent = message.get('intent', {}) if isinstance(message, dict) else {}
        item = intent.get('item', {}) if isinstance(intent, dict) else {}
        descriptor = item.get('descriptor', {}) if isinstance(item, dict) else {}
        if isinstance(descriptor, dict):
            search_query = descriptor.get('name', '') or ''
        
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

        # Build catalog
        catalog = BecknCatalog(
            descriptor=BecknDescriptor(name='OAN Catalog Registry'),
            providers=list(providers_map.values()),
        )
        
        # POST callback to BAP
        await post_on_search_callback(
            context,
            catalog,
            incoming_headers
        )
        
    except Exception as e:
        logger.exception('process_search_and_callback failed: %s', str(e))


async def post_on_search_callback(
    request_context: dict,
    catalog: BecknCatalog,
    incoming_headers: dict
):
    """POST on_search callback to BAP's callback URL"""

    if not isinstance(request_context, dict):
        request_context = {}

    bap_uri = request_context.get('bap_uri', '')
    
    if not bap_uri or not isinstance(bap_uri, str) or len(bap_uri) == 0:
        print("[WARN] on_search callback skipped: bap_uri missing")
        return
    
    # Build callback context
    correlation_id = request_context.get('transaction_id') or request_context.get('message_id') or str(uuid4())
    core_version = request_context.get('core_version') or request_context.get('version') or '1.1.0'
    
    callback_context = BecknContext(
        domain=request_context.get('domain', 'weather-advisory:oan'),
        country=request_context.get('country'),
        city=request_context.get('city'),
        action='on_search',
        core_version=core_version,
        bap_id=request_context.get('bap_id', 'bap-network'),
        bap_uri=bap_uri,
        transaction_id=correlation_id,
        message_id=str(uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    
    on_search_payload = {
        "context": callback_context.model_dump(),
        "message": {
            "catalog": catalog.model_dump()
        }
    }
    
    # Construct callback URL (aligned with OAN-Provider-Service behavior).
    base_bap_uri = bap_uri.rstrip('/')
    domain = request_context.get('domain')

    forwarded_host_raw = incoming_headers.get('x-forwarded-host')
    if isinstance(forwarded_host_raw, str):
        forwarded_host = forwarded_host_raw.split(',')[0].strip()
    else:
        forwarded_host = ''

    if domain in ('schemes:oan', 'schemes:vistaar'):
        if forwarded_host:
            callback_url = f"http://{forwarded_host.rstrip('/')}/bpp/caller/on_search"
        else:
            callback_url = 'http://onix-adapter2:8081/bpp/caller/on_search'
    elif '/bap/receiver' in base_bap_uri:
        callback_url = base_bap_uri.replace('/bap/receiver', '/bpp/caller') + '/on_search'
    elif base_bap_uri.endswith('/on_search'):
        callback_url = base_bap_uri
    else:
        callback_url = base_bap_uri + '/on_search'
    
    # Prepare headers (remove problematic ones)
    callback_headers = {
        k: v
        for k, v in incoming_headers.items()
        if k.lower() not in [
            'content-length',
            'transfer-encoding',
            'host',
            'authorization',
            'proxy-authorization',
            'x-gateway-authorization',
        ]
    }
    callback_headers['Content-Type'] = 'application/json'
    
    # POST callback
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                callback_url,
                json=on_search_payload,
                headers=callback_headers,
                timeout=10.0
            )
            print(f"[INFO] on_search callback posted to {callback_url}: HTTP {response.status_code}")
    except Exception as callback_err:
        print(f"[ERROR] on_search callback failed to {callback_url}: {callback_err}")
