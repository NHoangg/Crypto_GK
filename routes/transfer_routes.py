"""Ownership transfer routes."""

from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from models.database import DatabaseManager
from services.transfer_service import TransferService
from services.blockchain_service import BlockchainService
from services.audit_service import AuditService
from auth.decorators import login_required, permission_required

transfer_bp = Blueprint("transfer", __name__)

# Initialize services
db_manager = DatabaseManager()
transfer_service = TransferService(db_manager)
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


@transfer_bp.route("/transfer/<int:doc_id>", methods=["GET", "POST"])
@login_required
@permission_required("transfer_ownership")
def transfer_ownership(doc_id: int):
    """Transfer document ownership."""
    user = get_current_user()
    document = db_manager.get_document(doc_id)

    if not document:
        flash("Không tìm thấy chứng từ.", "error")
        return redirect(url_for("document.index"))

    if request.method == "POST":
        new_owner = request.form.get("new_owner", "").strip()

        try:
            # Create blockchain block
            payload = blockchain_service.create_transfer_payload(
                doc_id=doc_id,
                file_hash=document["file_hash"],
                from_owner=document["owner"],
                to_owner=new_owner,
            )
            block_index, tx_hash = blockchain_service.append_block(payload)

            # Transfer ownership
            transfer_service.transfer_ownership(
                doc_id=doc_id,
                new_owner=new_owner,
                block_index=block_index,
                tx_hash=tx_hash,
            )

            # Log audit
            audit_service.log_document_transfer(
                doc_id=doc_id,
                user_name=user["name"],
                user_role=user["role"],
                from_owner=document["owner"],
                to_owner=new_owner,
                tx_hash=tx_hash,
                block_index=block_index,
            )

            flash("Chuyển quyền sở hữu thành công và đã ghi lên blockchain.", "success")
            return redirect(url_for("document.document_detail", doc_id=doc_id))

        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for("transfer.transfer_ownership", doc_id=doc_id))

    return render_template("transfer.html", document=document)
