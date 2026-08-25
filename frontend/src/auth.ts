export function parseJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    const payload = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const decoded = atob(payload);
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

export function extractRoles(token: string): string[] {
  const payload = parseJwtPayload(token);
  if (!payload) return [];
  const resourceAccess = payload.resource_access as Record<string, { roles?: string[] }> | undefined;
  const clientRoles = resourceAccess?.['oan-portal']?.roles;
  if (Array.isArray(clientRoles) && clientRoles.length > 0) return clientRoles;
  const realmAccess = payload.realm_access as { roles?: string[] } | undefined;
  return Array.isArray(realmAccess?.roles) ? realmAccess.roles : [];
}

export function getUsername(token: string): string {
  const payload = parseJwtPayload(token);
  const username = payload?.preferred_username;
  return typeof username === 'string' ? username : 'unknown';
}
