import os
import httpx
import ssl
import ipaddress
# import traceback
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp

def is_private_or_local_ip(ip_str: str) -> bool:
    """
    严谨地检查一个IP地址字符串是否属于私有地址或环回地址。
    """
    if not ip_str:
        return False
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return ip_obj.is_loopback or ip_obj.is_private
    except ValueError:
        return False

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        # --- 服务启动时加载一次配置，提高效率 ---
        self.remote_auth_enabled = os.getenv("AUTH_REMOTE_ENABLED", "true").lower() == "true"
        self.local_auth_enabled = os.getenv("AUTH_LOCAL_ENABLED", "false").lower() == "true"
        self.validation_url = os.getenv("AUTH_VALIDATION_URL")
        self.validation_timeout = float(os.getenv("AUTH_VALIDATION_TIMEOUT", "20.0"))

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        
        immediate_client_ip = request.client.host
        final_client_ip = immediate_client_ip

        if is_private_or_local_ip(immediate_client_ip):
            forwarded_for = request.headers.get("x-forwarded-for")
            if forwarded_for:
                final_client_ip = forwarded_for.split(',')[0].strip()
        
        is_local_request = (
            is_private_or_local_ip(final_client_ip)
            or "localhost" in final_client_ip.lower()
        )

        auth_required = False
        if is_local_request and self.local_auth_enabled:
            auth_required = True
        elif not is_local_request and self.remote_auth_enabled:
            auth_required = True

        if not auth_required:
            return await call_next(request)

        if not self.validation_url:
            return JSONResponse(
                status_code=500,
                content={"error": "AUTH_VALIDATION_URL is not configured."},
            )

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=401, content={"error": "Authorization header is missing."}
            )

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid Authorization header format."},
            )

        token = parts[1]

        try:
            async with httpx.AsyncClient(verify=True) as client:
                response = await client.post(
                    self.validation_url,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=self.validation_timeout,
                )

            if response.status_code == 200:
                return await call_next(request)
            else:
                return JSONResponse(
                    status_code=response.status_code,
                    content={"error": "Token validation failed.", "detail": response.text},
                )
        except httpx.RequestError as e:
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Failed to connect to authentication service.",
                    "detail": str(e) # traceback.format_exc()
                },
            )
