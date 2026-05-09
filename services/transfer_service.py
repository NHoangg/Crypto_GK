"""Ownership transfer service."""

from models.database import DatabaseManager
from utils.crypto import utc_now_iso


class TransferService:
    """Handle ownership transfer operations."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def can_transfer_ownership(self, user_role: str) -> bool:
        """Check if user role can transfer ownership."""
        return user_role in ("Content Creator", "Publisher", "Customer", "Legal Authority")

    def transfer_ownership(
        self, doc_id: int, new_owner: str, block_index: int, tx_hash: str
    ) -> None:
        """
        Transfer document ownership to a new owner.
        """
        if not new_owner or not new_owner.strip():
            raise ValueError("Chủ sở hữu mới không được để trống.")

        document = self.db.get_document(doc_id)
        if not document:
            raise ValueError("Không tìm thấy chứng từ.")

        from_owner = document["owner"]

        # Update owner
        self.db.update_document_owner(doc_id, new_owner)

        # Record transfer
        transferred_at = utc_now_iso()
        self.db.insert_transfer(
            doc_id=doc_id,
            from_owner=from_owner,
            to_owner=new_owner,
            tx_hash=tx_hash,
            transferred_at=transferred_at,
            block_index=block_index,
        )

        return {"from_owner": from_owner, "to_owner": new_owner}

    def get_transfer_history(self, doc_id: int):
        """Get transfer history for a document."""
        return self.db.get_transfers(doc_id)
