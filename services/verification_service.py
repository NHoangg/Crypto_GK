"""Document verification service."""

from pathlib import Path
from tempfile import NamedTemporaryFile
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
from models.database import DatabaseManager
from utils.crypto import file_sha256


class VerificationService:
    """Handle document verification."""

    def __init__(self, db_manager: DatabaseManager, upload_dir: Path):
        self.db = db_manager
        self.upload_dir = upload_dir

    def verify_document(self, pdf_file) -> dict:
        """
        Verify a document by calculating its hash and comparing with stored documents.
        
        Returns:
            Dictionary with verification result (document info or None if not found)
        """
        if not pdf_file or not pdf_file.filename:
            raise ValueError("Vui lòng chọn tệp PDF để xác thực.")

        # Save to temporary file
        temp_name = f"tmp_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{secure_filename(pdf_file.filename)}"
        temp_path = self.upload_dir / temp_name

        try:
            pdf_file.save(temp_path)
            doc_hash = file_sha256(temp_path)
            result = self.db.get_document_by_hash(doc_hash)

            if result:
                return {"found": True, "document": result}
            else:
                return {"found": False, "document": None}
        finally:
            temp_path.unlink(missing_ok=True)

    def verify_hash(self, file_hash: str) -> dict:
        """Verify document by hash."""
        result = self.db.get_document_by_hash(file_hash)
        if result:
            return {"found": True, "document": result}
        else:
            return {"found": False, "document": None}
