from dataclasses import dataclass
from typing import Annotated, Callable

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    subject: str
    tenant_id: str
    scopes: frozenset[str]


TOKENS = {
    "admin-token": Principal("admin", "tenant_cincinnati", frozenset({"catalog:read", "quote:write", "order:write", "tools:invoke", "partner:write"})),
    "partner-token": Principal("partner", "tenant_cincinnati", frozenset({"catalog:read", "quote:write", "order:write", "tools:invoke", "partner:write"})),
    "analyst-token": Principal("analyst", "tenant_cincinnati", frozenset({"catalog:read", "quote:write"})),
}


def authenticate(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> Principal:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    principal = TOKENS.get(credentials.credentials)
    if principal is None:
        raise HTTPException(status_code=401, detail="Invalid bearer token")
    return principal


def require_scope(scope: str) -> Callable[[Principal], Principal]:
    def dependency(principal: Annotated[Principal, Depends(authenticate)]) -> Principal:
        if scope not in principal.scopes:
            raise HTTPException(status_code=403, detail=f"Missing scope: {scope}")
        return principal

    return dependency

