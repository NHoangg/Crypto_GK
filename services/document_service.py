"""Document registration and management service."""

from pathlib import Path
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
from typing import Tuple, Optional
from models.database import DatabaseManager
from utils.crypto import file_sha256, utc_now_iso


class DocumentService:
    """Handle document registration and retrieval."""

    def __init__(self, db_manager: DatabaseManager, upload_dir: Path):
        self.db = db_manager
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def register_document(
        self,
        pdf_file,
        owner: str,
        creator: str,
        block_index: int,
        tx_hash: str,
    ) -> Tuple[int, str]:
        """
        Register a new document.
        
        Returns:
            Tuple of (document_id, storage_filename)
        """
        # Generate storage filename
        safe_name = secure_filename(pdf_file.filename)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        storage_name = f"{timestamp}_{safe_name}"
        save_path = self.upload_dir / storage_name

        # Save file
        pdf_file.save(save_path)

        # Calculate hash
        doc_hash = file_sha256(save_path)

        # Check if document already exists
        if self.db.document_exists_by_hash(doc_hash):
            save_path.unlink(missing_ok=True)
            raise ValueError("Chứng từ đã tồn tại trên hệ thống (trùng hash).")

        # Insert into database
        created_at = utc_now_iso()
        doc_id = self.db.insert_document(
            filename=storage_name,
            file_hash=doc_hash,
            tx_hash=tx_hash,
            owner=owner,
            creator=creator,
            created_at=created_at,
            block_index=block_index,
        )

        return doc_id, storage_name

    def get_document(self, doc_id: int):
        """Get document by ID."""
        return self.db.get_document(doc_id)

    def get_all_documents(self):
        """Get all documents."""
        return self.db.get_all_documents()

    def get_document_by_hash(self, file_hash: str):
        """Get document by file hash."""
        return self.db.get_document_by_hash(file_hash)

    def document_exists(self, file_hash: str) -> bool:
        """Check if document exists by hash."""
        return self.db.document_exists_by_hash(file_hash)

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate hash of a file."""
        return file_sha256(file_path)

    def delete_file(self, filename: str) -> bool:
        """Delete a document file."""
        file_path = self.upload_dir / filename
        try:
            file_path.unlink(missing_ok=True)
            return True
        except Exception:
            return False

    def get_transfers(self, doc_id: int):
        """Get ownership transfers for a document."""
        return self.db.get_transfers(doc_id)

    def get_audit_logs(self, doc_id: int):
        """Get audit logs for a document."""
        return self.db.get_audit_logs(doc_id)
