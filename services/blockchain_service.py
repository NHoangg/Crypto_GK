"""Blockchain operations and management."""

from typing import Tuple
from models.database import DatabaseManager
from utils.crypto import build_tx_hash, utc_now_iso


class BlockchainService:
    """Handle blockchain operations."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def append_block(self, payload: str) -> Tuple[int, str]:
        """Append a new block to the blockchain."""
        last_block = self.db.get_last_blockchain_block()

        if last_block:
            block_index = int(last_block["block_index"]) + 1
            previous_hash = last_block["tx_hash"]
        else:
            block_index = 1
            previous_hash = "GENESIS"

        timestamp = utc_now_iso()
        tx_hash = build_tx_hash(previous_hash, payload, timestamp)

        self.db.insert_blockchain_block(block_index, previous_hash, payload, tx_hash, timestamp)

        return block_index, tx_hash

    def create_register_payload(self, file_hash: str, creator: str, owner: str) -> str:
        """Create payload for document registration."""
        return f"REGISTER|file_hash:{file_hash}|creator:{creator}|owner:{owner}"

    def create_transfer_payload(
        self, doc_id: int, file_hash: str, from_owner: str, to_owner: str
    ) -> str:
        """Create payload for ownership transfer."""
        return (
            f"TRANSFER|doc_id:{doc_id}|file_hash:{file_hash}|"
            f"from:{from_owner}|to:{to_owner}"
        )
