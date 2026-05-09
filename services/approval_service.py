"""Document approval workflow service."""

from models.database import DatabaseManager
from utils.crypto import utc_now_iso
from config import STATUS_FLOW


class ApprovalService:
    """Handle document approval workflow."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def can_approve(self, user_role: str, current_status: str) -> bool:
        """Check if user can approve document at current status."""
        if user_role == "Censor" and current_status == "Pending Censor Review":
            return True
        if user_role == "Publisher" and current_status == "Pending Publisher Approval":
            return True
        if user_role == "Legal Authority":
            return current_status not in ("Approved", "Rejected")
        return False

    def can_reject(self, user_role: str, current_status: str) -> bool:
        """Check if user can reject document at current status."""
        if current_status in ("Approved", "Rejected"):
            return False
        if user_role == "Censor" and current_status == "Pending Censor Review":
            return True
        if user_role == "Publisher" and current_status == "Pending Publisher Approval":
            return True
        if user_role == "Legal Authority":
            return True
        return False

    def approve_document(self, doc_id: int, user_role: str, user_name: str, current_status: str) -> dict:
        """
        Approve a document and advance it to next status.
        
        Returns:
            Dictionary with new_status and details
        """
        if not self.can_approve(user_role, current_status):
            raise PermissionError("Bạn không có quyền phê duyệt tài liệu này ở trạng thái hiện tại.")

        # Determine next status based on role and current status
        if user_role == "Censor" and current_status == "Pending Censor Review":
            new_status = "Pending Publisher Approval"
            details = "Đơn vị kiểm duyệt đã xác nhận nội dung. Chờ Nhà phát hành phê duyệt."
            self.db.update_document_status(doc_id, new_status)

        elif user_role == "Publisher" and current_status == "Pending Publisher Approval":
            new_status = "Approved"
            details = f"Nhà phát hành '{user_name}' đã ký số và phê duyệt chứng từ."
            approved_at = utc_now_iso()
            self.db.update_document_approval(doc_id, user_name, approved_at)

        elif user_role == "Legal Authority":
            new_status = "Approved"
            details = f"Cơ quan pháp lý '{user_name}' phê duyệt khẩn cấp chứng từ."
            approved_at = utc_now_iso()
            self.db.update_document_approval(doc_id, user_name, approved_at)

        else:
            raise ValueError("Không thể xác định trạng thái phê duyệt tiếp theo.")

        return {"new_status": new_status, "details": details}

    def reject_document(self, doc_id: int, user_role: str, user_name: str, current_status: str, reason: str) -> dict:
        """
        Reject a document.
        
        Returns:
            Dictionary with rejection details
        """
        if not self.can_reject(user_role, current_status):
            raise PermissionError("Bạn không có quyền từ chối tài liệu này.")

        rejected_at = utc_now_iso()
        self.db.update_document_rejection(
            doc_id,
            rejected_by=user_name,
            rejected_at=rejected_at,
            reason=reason or "Không có lý do cụ thể",
        )

        details = f"Từ chối: {reason or 'Không có lý do cụ thể'}."
        return {"new_status": "Rejected", "details": details}

    def get_next_approver_role(self, current_status: str) -> str:
        """Get the role that should approve next."""
        if current_status == "Pending Censor Review":
            return "Censor"
        elif current_status == "Pending Publisher Approval":
            return "Publisher"
        else:
            return "Legal Authority"
