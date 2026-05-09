"""Audit logging service."""

from typing import Optional
from models.database import DatabaseManager
from utils.crypto import utc_now_iso


class AuditService:
    """Handle audit logging."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def log_action(
        self,
        document_id: Optional[int],
        action: str,
        performed_by: str,
        role: str,
        details: str,
        tx_hash: Optional[str] = None,
        block_index: Optional[int] = None,
    ) -> None:
        """Log an action in the audit log."""
        self.db.insert_audit_log(
            document_id=document_id,
            action=action,
            performed_by=performed_by,
            role=role,
            details=details,
            created_at=utc_now_iso(),
            tx_hash=tx_hash,
            block_index=block_index,
        )

    def log_document_registration(
        self,
        doc_id: int,
        user_name: str,
        user_role: str,
        owner: str,
        tx_hash: str,
        block_index: int,
    ) -> None:
        """Log document registration."""
        self.log_action(
            document_id=doc_id,
            action="Register",
            performed_by=user_name,
            role=user_role,
            details=f"Công ty sáng tạo nội dung đăng ký chứng từ, chủ sở hữu ban đầu: {owner}.",
            tx_hash=tx_hash,
            block_index=block_index,
        )

    def log_document_approval(
        self,
        doc_id: int,
        user_name: str,
        user_role: str,
        tx_hash: str,
        block_index: int,
    ) -> None:
        """Log document approval."""
        stage_name = "Đơn vị kiểm duyệt" if user_role == "Censor" else "Nhà phát hành"
        details = f"{stage_name} '{user_name}' đã xác nhận."
        if user_role == "Publisher":
            details = f"Nhà phát hành '{user_name}' đã ký số và phê duyệt chứng từ."
        elif user_role == "Legal Authority":
            details = f"Cơ quan pháp lý '{user_name}' phê duyệt khẩn cấp chứng từ."

        self.log_action(
            document_id=doc_id,
            action="Approve",
            performed_by=user_name,
            role=user_role,
            details=details,
            tx_hash=tx_hash,
            block_index=block_index,
        )

    def log_document_rejection(
        self,
        doc_id: int,
        user_name: str,
        user_role: str,
        reason: str,
        tx_hash: str,
        block_index: int,
    ) -> None:
        """Log document rejection."""
        self.log_action(
            document_id=doc_id,
            action="Reject",
            performed_by=user_name,
            role=user_role,
            details=f"Từ chối: {reason or 'Không có lý do cụ thể'}.",
            tx_hash=tx_hash,
            block_index=block_index,
        )

    def log_document_transfer(
        self,
        doc_id: int,
        user_name: str,
        user_role: str,
        from_owner: str,
        to_owner: str,
        tx_hash: str,
        block_index: int,
    ) -> None:
        """Log ownership transfer."""
        self.log_action(
            document_id=doc_id,
            action="Transfer",
            performed_by=user_name,
            role=user_role,
            details=f"Chuyển quyền sở hữu từ '{from_owner}' sang '{to_owner}'.",
            tx_hash=tx_hash,
            block_index=block_index,
        )

    def log_document_verification(
        self,
        doc_id: int,
        user_name: str,
        user_role: str,
        tx_hash: str,
        block_index: int,
    ) -> None:
        """Log document verification."""
        self.log_action(
            document_id=doc_id,
            action="Verify",
            performed_by=user_name,
            role=user_role,
            details="Xác thực file PDF upload với hash đã lưu.",
            tx_hash=tx_hash,
            block_index=block_index,
        )

    def log_document_deletion(
        self,
        doc_id: int,
        user_name: str,
        user_role: str,
        filename: str,
        file_hash: str,
        tx_hash: str,
        block_index: int,
    ) -> None:
        """Log document deletion."""
        self.log_action(
            document_id=doc_id,
            action="Delete",
            performed_by=user_name,
            role=user_role,
            details=f"Cơ quan pháp lý xóa chứng từ '{filename}' (hash: {file_hash[:16]}...).",
            tx_hash=tx_hash,
            block_index=block_index,
        )
