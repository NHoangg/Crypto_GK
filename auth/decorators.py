"""Role-based access control decorators."""

from functools import wraps
from typing import Callable, List, Optional
from flask import session, flash, redirect, url_for
from auth.permissions import has_permission


def login_required(f: Callable) -> Callable:
    """Decorator to require user login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_name = session.get("user_name")
        user_role = session.get("user_role")
        if not user_name or not user_role:
            flash("Vui lòng đăng nhập để thực hiện thao tác này.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*allowed_roles: str) -> Callable:
    """Decorator to require specific role(s)."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get("user_role")
            if not user_role or user_role not in allowed_roles:
                flash(f"Bạn không có quyền truy cập. Chỉ {', '.join(allowed_roles)} mới có thể.", "error")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def permission_required(permission: str) -> Callable:
    """Decorator to require specific permission."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get("user_role")
            if not user_role or not has_permission(user_role, permission):
                flash("Bạn không có quyền thực hiện thao tác này.", "error")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
