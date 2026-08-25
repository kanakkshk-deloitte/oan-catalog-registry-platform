from typing import Any, Dict, List

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings


security = HTTPBearer(auto_error=False)


class AuthContext:
    def __init__(self, username: str, roles: List[str]):
        self.username = username
        self.roles = roles


def _extract_roles(payload: Dict[str, Any]) -> List[str]:
    client_roles = (
        payload.get('resource_access', {})
        .get(settings.keycloak_client_id, {})
        .get('roles', [])
    )
    if client_roles:
        return client_roles
    return payload.get('realm_access', {}).get('roles', [])


def _issuer() -> str:
    return f"{settings.keycloak_base_url}/realms/{settings.keycloak_realm}"


def _jwks_url() -> str:
    return f"{_issuer()}/protocol/openid-connect/certs"


def _token_url() -> str:
    return f"{_issuer()}/protocol/openid-connect/token"


async def exchange_password_for_token(username: str, password: str) -> Dict[str, Any]:
    data = {
        'grant_type': 'password',
        'client_id': settings.keycloak_client_id,
        'client_secret': settings.keycloak_client_secret,
        'username': username,
        'password': password,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(_token_url(), data=data)
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
    return response.json()


async def _fetch_signing_key(token: str) -> Dict[str, Any]:
    headers = jwt.get_unverified_header(token)
    kid = headers.get('kid')
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(_jwks_url())
    response.raise_for_status()
    keys = response.json().get('keys', [])
    for key in keys:
        if key.get('kid') == kid:
            return key
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Signing key not found')


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> AuthContext:
    if not settings.auth_enabled:
        return AuthContext(username='dev-admin', roles=['admin', 'provider'])

    if not credentials or credentials.scheme.lower() != 'bearer':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing bearer token')

    token = credentials.credentials
    try:
        key = await _fetch_signing_key(token)
        payload = jwt.decode(
            token,
            key,
            algorithms=['RS256'],
            issuer=_issuer(),
            options={'verify_aud': False},
        )
        username = payload.get('preferred_username')
        roles = _extract_roles(payload)
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token subject')
        return AuthContext(username=username, roles=roles)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token') from exc


def require_admin(user: AuthContext = Depends(get_current_user)) -> AuthContext:
    if 'admin' not in user.roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin role required')
    return user


def require_provider(user: AuthContext = Depends(get_current_user)) -> AuthContext:
    if 'provider' not in user.roles and 'admin' not in user.roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Provider role required')
    return user
