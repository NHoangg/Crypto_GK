"""Document approval workflow routes."""

from flask import Blueprint, request, session, flash, redirect, url_for
from models.database import DatabaseManager
from services.approval_service import ApprovalService
from services.audit_service import AuditService
from auth.decorators import login_required

approval_bp = Blueprint("approval", __name__)

# Initialize services
db_manager = DatabaseManager()
approval_service = ApprovalService(db_manager)
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


@approval_bp.route("/document/<int:doc_id>/review", methods=["POST"])
@login_required
def review_document(doc_id: int):
    """Review and approve/reject a document."""
    user = get_current_user()
    action = request.form.get("action")
    reason = request.form.get("reason", "").strip()

    # Get document
    document = db_manager.get_document(doc_id)
    if not document:
        flash("Không tìm thấy chứng từ.", "error")
        return redirect(url_for("document.index"))

    try:
        if action == "approve":
            result = approval_service.approve_document(
                doc_id=doc_id,
                user_role=user["role"],
                user_name=user["name"],
                current_status=document["approval_status"],
            )
            audit_service.log_document_approval(
                doc_id=doc_id,
                user_name=user["name"],
                user_role=user["role"],
                tx_hash=document["tx_hash"],
                block_index=document["block_index"],
            )
            flash("Cập nhật trạng thái phê duyệt thành công.", "success")

        elif action == "reject":
            result = approval_service.reject_document(
                doc_id=doc_id,
                user_role=user["role"],
                user_name=user["name"],
                current_status=document["approval_status"],
                reason=reason,
            )
            audit_service.log_document_rejection(
                doc_id=doc_id,
                user_name=user["name"],
                user_role=user["role"],
                reason=reason,
                tx_hash=document["tx_hash"],
                block_index=document["block_index"],
            )
            flash("Tài liệu đã bị từ chối.", "success")
        else:
            flash("Hành động không hợp lệ.", "error")

    except PermissionError as e:
        flash(str(e), "error")
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("document.document_detail", doc_id=doc_id))
