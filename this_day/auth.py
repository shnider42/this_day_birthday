from __future__ import annotations

import base64
import os
from typing import Optional

from flask import Response, request


def basic_auth_required(realm: str = "Family Birthday Page") -> Optional[Response]:
    expected_user = os.environ.get("APP_USER", "")
    expected_pass = os.environ.get("APP_PASS", "")
    if not expected_user or not expected_pass:
        return Response(
            "Server misconfigured: set APP_USER and APP_PASS environment variables.",
            status=500,
            mimetype="text/plain",
        )

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Basic "):
        return Response(
            "Auth required",
            status=401,
            headers={"WWW-Authenticate": f'Basic realm="{realm}"'},
        )

    try:
        decoded = base64.b64decode(auth.split(" ", 1)[1]).decode("utf-8")
        user, pw = decoded.split(":", 1)
    except Exception:
        return Response(
            "Bad auth header",
            status=401,
            headers={"WWW-Authenticate": f'Basic realm="{realm}"'},
        )

    if user != expected_user or pw != expected_pass:
        return Response(
            "Unauthorized",
            status=401,
            headers={"WWW-Authenticate": f'Basic realm="{realm}"'},
        )

    return None
