"""Document management routes."""

from pathlib import Path
from flask import Blueprint, render_template, request, session, flash, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from models.database import DatabaseManager
from services.document_service import DocumentService
from services.blockchain_service import BlockchainService
from services.audit_service import AuditService
from auth.decorators import login_required, permission_required
from config import UPLOAD_DIR, ALLOWED_EXTENSIONS
from utils.crypto import utc_now_iso
import os

document_bp = Blueprint("document", __name__)

# Initialize services
db_manager = DatabaseManager()
doc_service = DocumentService(db_manager, UPLOAD_DIR)
blockchain_service = BlockchainService(db_manager)
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


@document_bp.route("/")
def index():
    """List all documents."""
    documents = doc_service.get_all_documents()
    return render_template("index.html", documents=documents)


@document_bp.route("/register", methods=["GET", "POST"])
@login_required
@permission_required("register_document")
def register_document():
    """Register a new document (Content Creator)."""
    user = get_current_user()
    
    if request.method == "POST":
        owner = request.form.get("owner", "").strip()
        creator = request.form.get("creator", "").strip()
        pdf = request.files.get("pdf")

        if not owner or not creator:
            flash("Vui lòng điền người khởi tạo và chủ sở hữu ban đầu.", "error")
            return redirect(url_for("document.register_document"))

        if not pdf or not pdf.filename:
            flash("Vui lòng tải lên tệp PDF.", "error")
            return redirect(url_for("document.register_document"))

        if not allowed_file(pdf.filename, ALLOWED_EXTENSIONS):
            flash("Chỉ hỗ trợ tệp PDF.", "error")
            return redirect(url_for("document.register_document"))

        try:
            # Create blockchain block
            payload = blockchain_service.create_register_payload(
                file_hash="",  # Will be calculated in service
                creator=creator,
                owner=owner,
            )
            block_index, tx_hash = blockchain_service.append_block(payload)

            # Register document
            doc_id, storage_name = doc_service.register_document(
                pdf_file=pdf,
                owner=owner,
                creator=creator,
                block_index=block_index,
                tx_hash=tx_hash,
            )

            # Log audit
            audit_service.log_document_registration(
                doc_id=doc_id,
                user_name=user["name"],
                user_role=user["role"],
                owner=owner,
                tx_hash=tx_hash,
                block_index=block_index,
            )

            flash("Đăng ký chứng từ thành công. Chứng từ đang chờ Đơn vị kiểm duyệt xem xét.", "success")
            return redirect(url_for("document.index"))

        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for("document.index"))
        except Exception as e:
            flash(f"Lỗi khi đăng ký chứng từ: {str(e)}", "error")
            return redirect(url_for("document.register_document"))

    return render_template("register.html")


@document_bp.route("/document/<int:doc_id>")
def document_detail(doc_id: int):
    """Show document details and audit history."""
    document = doc_service.get_document(doc_id)
    if not document:
        flash("Không tìm thấy chứng từ.", "error")
        return redirect(url_for("document.index"))

    transfers = doc_service.get_transfers(doc_id)
    audit_logs = doc_service.get_audit_logs(doc_id)

    return render_template("detail.html", document=document, transfers=transfers, audit_logs=audit_logs)


@document_bp.route("/uploads/<path:filename>")
def uploaded_file(filename: str):
    """Download uploaded file."""
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Check if file is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions
