"""Authentication routes."""

from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from config import ROLES

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """User login endpoint."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        role = request.form.get("role", "").strip()
        
        if not name or role not in ROLES:
            flash("Vui lòng nhập tên và chọn vai trò hợp lệ.", "error")
            return redirect(url_for("auth.login"))
        
        session["user_name"] = name
        session["user_role"] = role
        flash(f"Đăng nhập thành công với vai trò: {ROLES[role]['label']}.", "success")
        return redirect(url_for("document.index"))
    
    return render_template("login.html", roles=ROLES)


@auth_bp.route("/logout")
def logout():
    """User logout endpoint."""
    session.clear()
    flash("Đã đăng xuất.", "success")
    return redirect(url_for("document.index"))
