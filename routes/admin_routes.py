"""Legal Authority admin routes."""

from flask import Blueprint, request, session, flash, redirect, url_for
from models.database import DatabaseManager
from services.audit_service import AuditService
from services.document_service import DocumentService
from auth.decorators import login_required, role_required
from config import UPLOAD_DIR

admin_bp = Blueprint("admin", __name__)

# Initialize services
db_manager = DatabaseManager()
audit_service = AuditService(db_manager)
doc_service = DocumentService(db_manager, UPLOAD_DIR)


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


@admin_bp.route("/document/<int:doc_id>/delete", methods=["POST"])
@login_required
@role_required("Legal Authority")
def delete_document(doc_id: int):
    """Delete a document (Legal Authority only)."""
    user = get_current_user()
    document = db_manager.get_document(doc_id)

    if not document:
        flash("Không tìm thấy chứng từ.", "error")
        return redirect(url_for("document.index"))

    # Log deletion
    audit_service.log_document_deletion(
        doc_id=doc_id,
        user_name=user["name"],
        user_role=user["role"],
        filename=document["filename"],
        file_hash=document["file_hash"],
        tx_hash=document["tx_hash"],
        block_index=document["block_index"],
    )

    # Delete file and records
    doc_service.delete_file(document["filename"])
    db_manager.delete_document(doc_id)

    flash(f"Đã xóa chứng từ #{doc_id} thành công.", "success")
    return redirect(url_for("document.index"))


@admin_bp.route("/documents/delete-all", methods=["POST"])
@login_required
@role_required("Legal Authority")
def delete_all_documents():
    """Delete all documents (Legal Authority only)."""
    user = get_current_user()
    documents = db_manager.get_all_documents()

    if not documents:
        flash("Không có chứng từ nào để xóa.", "error")
        return redirect(url_for("document.index"))

    # Log deletions
    for doc in documents:
        audit_service.log_document_deletion(
            doc_id=doc["id"],
            user_name=user["name"],
            user_role=user["role"],
            filename=doc["filename"],
            file_hash=doc["file_hash"],
            tx_hash=doc["tx_hash"],
            block_index=doc["block_index"],
        )
        doc_service.delete_file(doc["filename"])

    count = db_manager.delete_all_documents()
    flash(f"Đã xóa toàn bộ {count} chứng từ thành công.", "success")
    return redirect(url_for("document.index"))
