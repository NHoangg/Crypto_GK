"""Database operations and model management."""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Optional, List, Dict, Any
from config import DB_PATH, ROLES


class DatabaseManager:
    """Manage database connections and operations."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    @contextmanager
    def get_db(self) -> Generator[sqlite3.Connection, None, None]:
        """Get database connection context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self) -> None:
        """Initialize database schema."""
        with self.get_db() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_hash TEXT NOT NULL UNIQUE,
                    tx_hash TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    creator TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    block_index INTEGER NOT NULL,
                    approval_status TEXT NOT NULL DEFAULT 'Pending Censor Review',
                    approved_by TEXT,
                    approved_at TEXT,
                    rejected_by TEXT,
                    rejected_at TEXT,
                    rejection_reason TEXT
                );

                CREATE TABLE IF NOT EXISTS ownership_transfers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    from_owner TEXT NOT NULL,
                    to_owner TEXT NOT NULL,
                    tx_hash TEXT NOT NULL,
                    transferred_at TEXT NOT NULL,
                    block_index INTEGER NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(id)
                );

                CREATE TABLE IF NOT EXISTS blockchain (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    block_index INTEGER NOT NULL UNIQUE,
                    previous_hash TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    tx_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER,
                    action TEXT NOT NULL,
                    performed_by TEXT NOT NULL,
                    role TEXT NOT NULL,
                    details TEXT,
                    created_at TEXT NOT NULL,
                    tx_hash TEXT,
                    block_index INTEGER,
                    FOREIGN KEY(document_id) REFERENCES documents(id)
                );
                """
            )

            # Add missing columns if they don't exist
            existing_columns = [row[1] for row in conn.execute("PRAGMA table_info(documents)")]
            for col, defval in [
                ("approval_status", "'Pending Censor Review'"),
                ("approved_by", "NULL"),
                ("approved_at", "NULL"),
                ("rejected_by", "NULL"),
                ("rejected_at", "NULL"),
                ("rejection_reason", "NULL"),
            ]:
                if col not in existing_columns:
                    conn.execute(f"ALTER TABLE documents ADD COLUMN {col} TEXT DEFAULT {defval}")

    def get_document(self, doc_id: int) -> Optional[sqlite3.Row]:
        """Get a document by ID."""
        with self.get_db() as conn:
            return conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()

    def get_all_documents(self) -> List[sqlite3.Row]:
        """Get all documents."""
        with self.get_db() as conn:
            return conn.execute(
                """
                SELECT d.id, d.filename, d.file_hash, d.owner, d.creator, d.created_at, d.tx_hash,
                       d.block_index, d.approval_status,
                       (SELECT COUNT(*) FROM ownership_transfers ot WHERE ot.document_id = d.id) AS transfer_count
                FROM documents d
                ORDER BY d.id DESC
                """
            ).fetchall()

    def get_document_by_hash(self, file_hash: str) -> Optional[sqlite3.Row]:
        """Get a document by file hash."""
        with self.get_db() as conn:
            return conn.execute(
                """
                SELECT d.*, b.created_at AS chain_timestamp
                FROM documents d
                JOIN blockchain b ON d.tx_hash = b.tx_hash
                WHERE d.file_hash = ?
                """,
                (file_hash,),
            ).fetchone()

    def get_transfers(self, doc_id: int) -> List[sqlite3.Row]:
        """Get all ownership transfers for a document."""
        with self.get_db() as conn:
            return conn.execute(
                """
                SELECT from_owner, to_owner, tx_hash, transferred_at, block_index
                FROM ownership_transfers WHERE document_id = ? ORDER BY id ASC
                """,
                (doc_id,),
            ).fetchall()

    def get_audit_logs(self, doc_id: int) -> List[sqlite3.Row]:
        """Get all audit logs for a document."""
        with self.get_db() as conn:
            return conn.execute(
                """
                SELECT action, performed_by, role, details, created_at, tx_hash, block_index
                FROM audit_log WHERE document_id = ? ORDER BY id ASC
                """,
                (doc_id,),
            ).fetchall()

    def insert_document(
        self,
        filename: str,
        file_hash: str,
        tx_hash: str,
        owner: str,
        creator: str,
        created_at: str,
        block_index: int,
    ) -> int:
        """Insert a new document."""
        with self.get_db() as conn:
            conn.execute(
                """
                INSERT INTO documents(filename, file_hash, tx_hash, owner, creator, created_at, block_index, approval_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (filename, file_hash, tx_hash, owner, creator, created_at, block_index, "Pending Censor Review"),
            )
            return conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

    def update_document_status(self, doc_id: int, status: str) -> None:
        """Update document approval status."""
        with self.get_db() as conn:
            conn.execute("UPDATE documents SET approval_status = ? WHERE id = ?", (status, doc_id))

    def update_document_approval(self, doc_id: int, approved_by: str, approved_at: str) -> None:
        """Mark document as approved."""
        with self.get_db() as conn:
            conn.execute(
                "UPDATE documents SET approval_status = ?, approved_by = ?, approved_at = ? WHERE id = ?",
                ("Approved", approved_by, approved_at, doc_id),
            )

    def update_document_rejection(
        self, doc_id: int, rejected_by: str, rejected_at: str, reason: str
    ) -> None:
        """Mark document as rejected."""
        with self.get_db() as conn:
            conn.execute(
                "UPDATE documents SET approval_status = ?, rejected_by = ?, rejected_at = ?, rejection_reason = ? WHERE id = ?",
                ("Rejected", rejected_by, rejected_at, reason, doc_id),
            )

    def update_document_owner(self, doc_id: int, new_owner: str) -> None:
        """Update document owner."""
        with self.get_db() as conn:
            conn.execute("UPDATE documents SET owner = ? WHERE id = ?", (new_owner, doc_id))

    def insert_transfer(
        self, doc_id: int, from_owner: str, to_owner: str, tx_hash: str, transferred_at: str, block_index: int
    ) -> None:
        """Insert ownership transfer record."""
        with self.get_db() as conn:
            conn.execute(
                """
                INSERT INTO ownership_transfers(document_id, from_owner, to_owner, tx_hash, transferred_at, block_index)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (doc_id, from_owner, to_owner, tx_hash, transferred_at, block_index),
            )

    def insert_blockchain_block(
        self, block_index: int, previous_hash: str, payload: str, tx_hash: str, created_at: str
    ) -> None:
        """Insert blockchain block."""
        with self.get_db() as conn:
            conn.execute(
                """
                INSERT INTO blockchain(block_index, previous_hash, payload, tx_hash, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (block_index, previous_hash, payload, tx_hash, created_at),
            )

    def get_last_blockchain_block(self) -> Optional[sqlite3.Row]:
        """Get the last blockchain block."""
        with self.get_db() as conn:
            return conn.execute(
                "SELECT block_index, tx_hash FROM blockchain ORDER BY block_index DESC LIMIT 1"
            ).fetchone()

    def insert_audit_log(
        self,
        document_id: Optional[int],
        action: str,
        performed_by: str,
        role: str,
        details: str,
        created_at: str,
        tx_hash: Optional[str] = None,
        block_index: Optional[int] = None,
    ) -> None:
        """Insert audit log entry."""
        with self.get_db() as conn:
            conn.execute(
                """
                INSERT INTO audit_log(document_id, action, performed_by, role, details, created_at, tx_hash, block_index)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (document_id, action, performed_by, role, details, created_at, tx_hash, block_index),
            )

    def delete_document(self, doc_id: int) -> None:
        """Delete a document and related records."""
        with self.get_db() as conn:
            conn.execute("DELETE FROM ownership_transfers WHERE document_id = ?", (doc_id,))
            conn.execute("DELETE FROM audit_log WHERE document_id = ?", (doc_id,))
            conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

    def delete_all_documents(self) -> int:
        """Delete all documents and return count."""
        with self.get_db() as conn:
            count = conn.execute("SELECT COUNT(*) as cnt FROM documents").fetchone()["cnt"]
            conn.execute("DELETE FROM ownership_transfers")
            conn.execute("DELETE FROM audit_log")
            conn.execute("DELETE FROM documents")
        return count

    def document_exists_by_hash(self, file_hash: str) -> bool:
        """Check if document exists by hash."""
        with self.get_db() as conn:
            result = conn.execute("SELECT id FROM documents WHERE file_hash = ?", (file_hash,)).fetchone()
        return result is not None
