# coding=utf-8
"""
自定义认证中间件 - 最终版 (简化IP判断逻辑)
"""

import os
import time
import jwt
import ipaddress
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
        # 在启动时读取配置和密钥，但不在此处进行强制检查
        self.remote_auth_enabled = os.getenv("AUTH_REMOTE_ENABLED", "true").lower() == "true"
        self.local_auth_enabled = os.getenv("AUTH_LOCAL_ENABLED", "false").lower() == "true"
        self.algorithm = "HS256"

        secret_file_path = os.getenv("OCR_SHARED_SECRET_FILE")
        if secret_file_path:
            try:
                with open(secret_file_path, 'r') as f:
                    self.secret_key = f.read().strip()
                print("[Auth] Secret loaded from file.")
            except IOError as e:
                # 在启动时打印错误，但允许服务继续运行
                print(f"[Auth Error] Could not read secret file {secret_file_path}: {e}", file=sys.stderr)
                self.secret_key = None
        else:
            self.secret_key = os.getenv("OCR_SHARED_SECRET")
            if self.secret_key:
                print("[Auth] Secret loaded from environment variable.")

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        
        if request.method == "OPTIONS":
            return await call_next(request)

        forwarded_for = request.headers.get("x-forwarded-for")
        final_client_ip = forwarded_for.split(',')[0].strip() if forwarded_for else request.client.host
        is_local_request = is_private_or_local_ip(final_client_ip)

        auth_required = False
        if is_local_request and self.local_auth_enabled:
            auth_required = True
        elif not is_local_request and self.remote_auth_enabled:
            auth_required = True

        if not auth_required:
            return await call_next(request)

        # --- 在需要时才检查密钥是否存在 ---
        if not self.secret_key:
            return JSONResponse(
                status_code=500,
                content={"error": "Server configuration error: Authentication is required but no secret key is configured."}
            )

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=401, content={"error": "Authorization header is missing."}
            )

        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid authentication scheme.")
        except ValueError:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Invalid Authorization header format. Expected 'Bearer <token>'."
                },
            )

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("exp", 0) < time.time():
                raise jwt.ExpiredSignatureError("Token has expired.")
        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=401, content={"error": "Token has expired."}
            )
        except jwt.InvalidTokenError as e:
            return JSONResponse(
                status_code=403,
                content={"error": "Invalid token.", "detail": str(e)},
            )
        
        return await call_next(request)