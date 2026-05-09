"""Document verification routes."""

from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from pathlib import Path
from models.database import DatabaseManager
from services.verification_service import VerificationService
from services.audit_service import AuditService
from config import UPLOAD_DIR, ALLOWED_EXTENSIONS
from utils.crypto import allowed_file

verification_bp = Blueprint("verification", __name__)

# Initialize services
db_manager = DatabaseManager()
verification_service = VerificationService(db_manager, UPLOAD_DIR)
audit_service = AuditService(db_manager)


def get_current_user():
    """Get current user from session."""
    from config import ROLES
    name = session.get("user_name")
    role = session.get("user_role")
    role_info = ROLES.get(role, {})
    return {
        "is_authenticated": bool(name and role),
        "name": name or "Khách",
        "role": role or "Guest",
        "role_label": role_info.get("label", role or "Khách"),
        "role_icon": role_info.get("icon", "ph-user"),
        "role_color": role_info.get("color", "#94a3b8"),
    }


@verification_bp.route("/verify", methods=["GET", "POST"])
def verify_document():
    """Verify a document by uploading it."""
    user = get_current_user()
    result = None

    if request.method == "POST":
        pdf = request.files.get("pdf")

        try:
            if not pdf or not pdf.filename:
                flash("Vui lòng chọn tệp PDF để xác thực.", "error")
                return redirect(url_for("verification.verify_document"))

            if not allowed_file(pdf.filename, ALLOWED_EXTENSIONS):
                flash("Chỉ hỗ trợ tệp PDF.", "error")
                return redirect(url_for("verification.verify_document"))

            # Verify document
            verify_result = verification_service.verify_document(pdf)
            result = verify_result["document"]

            if result and user["is_authenticated"]:
                # Log verification in audit
                audit_service.log_document_verification(
                    doc_id=result["id"],
                    user_name=user["name"],
                    user_role=user["role"],
                    tx_hash=result["tx_hash"],
                    block_index=result["block_index"],
                )

        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for("verification.verify_document"))

    return render_template("verify.html", result=result)
