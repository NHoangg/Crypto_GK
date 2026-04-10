import hashlib
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
DB_PATH = BASE_DIR / "ledger.db"
ALLOWED_EXTENSIONS = {"pdf"}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "demo-secret-key")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db() as conn:
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
                block_index INTEGER NOT NULL
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
            """
        )


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def file_sha256(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_tx_hash(previous_hash: str, payload: str, timestamp: str) -> str:
    content = f"{previous_hash}|{payload}|{timestamp}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def append_block(payload: str) -> tuple[int, str]:
    with get_db() as conn:
        last_block = conn.execute(
            "SELECT block_index, tx_hash FROM blockchain ORDER BY block_index DESC LIMIT 1"
        ).fetchone()

        if last_block:
            block_index = int(last_block["block_index"]) + 1
            previous_hash = last_block["tx_hash"]
        else:
            block_index = 1
            previous_hash = "GENESIS"

        timestamp = utc_now_iso()
        tx_hash = build_tx_hash(previous_hash, payload, timestamp)

        conn.execute(
            """
            INSERT INTO blockchain(block_index, previous_hash, payload, tx_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (block_index, previous_hash, payload, tx_hash, timestamp),
        )

    return block_index, tx_hash


@app.route("/")
def index():
    with get_db() as conn:
        documents = conn.execute(
            """
            SELECT d.id, d.filename, d.file_hash, d.owner, d.creator, d.created_at, d.tx_hash,
                   d.block_index,
                   (
                        SELECT COUNT(*) FROM ownership_transfers ot
                        WHERE ot.document_id = d.id
                   ) AS transfer_count
            FROM documents d
            ORDER BY d.id DESC
            """
        ).fetchall()
    return render_template("index.html", documents=documents)


@app.route("/register", methods=["GET", "POST"])
def register_document():
    if request.method == "POST":
        owner = request.form.get("owner", "").strip()
        creator = request.form.get("creator", "").strip()
        pdf = request.files.get("pdf")

        if not owner or not creator:
            flash("Vui lòng điền người khởi tạo và chủ sở hữu ban đầu.", "error")
            return redirect(url_for("register_document"))

        if not pdf or not pdf.filename:
            flash("Vui lòng tải lên tệp PDF.", "error")
            return redirect(url_for("register_document"))

        if not allowed_file(pdf.filename):
            flash("Chỉ hỗ trợ tệp PDF.", "error")
            return redirect(url_for("register_document"))

        safe_name = secure_filename(pdf.filename)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        storage_name = f"{timestamp}_{safe_name}"
        save_path = UPLOAD_DIR / storage_name
        pdf.save(save_path)

        doc_hash = file_sha256(save_path)

        with get_db() as conn:
            existing = conn.execute(
                "SELECT id FROM documents WHERE file_hash = ?", (doc_hash,)
            ).fetchone()

        if existing:
            save_path.unlink(missing_ok=True)
            flash("Chứng từ đã tồn tại trên hệ thống (trùng hash).", "error")
            return redirect(url_for("index"))

        payload = f"REGISTER|file_hash:{doc_hash}|creator:{creator}|owner:{owner}"
        block_index, tx_hash = append_block(payload)
        created_at = utc_now_iso()

        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO documents(filename, file_hash, tx_hash, owner, creator, created_at, block_index)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (storage_name, doc_hash, tx_hash, owner, creator, created_at, block_index),
            )

        flash("Đăng ký chứng từ thành công: đã tạo Digital Fingerprint + Proof of Existence.", "success")
        return redirect(url_for("index"))

    return render_template("register.html")


@app.route("/verify", methods=["GET", "POST"])
def verify_document():
    result = None
    if request.method == "POST":
        pdf = request.files.get("pdf")
        if not pdf or not pdf.filename:
            flash("Vui lòng chọn tệp PDF để xác thực.", "error")
            return redirect(url_for("verify_document"))

        if not allowed_file(pdf.filename):
            flash("Chỉ hỗ trợ tệp PDF.", "error")
            return redirect(url_for("verify_document"))

        temp_name = f"tmp_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{secure_filename(pdf.filename)}"
        temp_path = UPLOAD_DIR / temp_name
        pdf.save(temp_path)
        doc_hash = file_sha256(temp_path)
        temp_path.unlink(missing_ok=True)

        with get_db() as conn:
            result = conn.execute(
                """
                SELECT d.*, b.created_at AS chain_timestamp
                FROM documents d
                JOIN blockchain b ON d.tx_hash = b.tx_hash
                WHERE d.file_hash = ?
                """,
                (doc_hash,),
            ).fetchone()

        if not result:
            flash("Không tìm thấy chứng từ trên sổ cái.", "error")

    return render_template("verify.html", result=result)


@app.route("/transfer/<int:doc_id>", methods=["GET", "POST"])
def transfer_ownership(doc_id: int):
    with get_db() as conn:
        document = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        if not document:
            flash("Không tìm thấy chứng từ.", "error")
            return redirect(url_for("index"))

    if request.method == "POST":
        new_owner = request.form.get("new_owner", "").strip()
        if not new_owner:
            flash("Vui lòng nhập chủ sở hữu mới.", "error")
            return redirect(url_for("transfer_ownership", doc_id=doc_id))

        from_owner = document["owner"]
        payload = (
            f"TRANSFER|doc_id:{doc_id}|file_hash:{document['file_hash']}|"
            f"from:{from_owner}|to:{new_owner}"
        )
        block_index, tx_hash = append_block(payload)
        transferred_at = utc_now_iso()

        with get_db() as conn:
            conn.execute("UPDATE documents SET owner = ? WHERE id = ?", (new_owner, doc_id))
            conn.execute(
                """
                INSERT INTO ownership_transfers(
                    document_id, from_owner, to_owner, tx_hash, transferred_at, block_index
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (doc_id, from_owner, new_owner, tx_hash, transferred_at, block_index),
            )

        flash("Chuyển quyền sở hữu thành công và đã ghi lên blockchain demo.", "success")
        return redirect(url_for("document_detail", doc_id=doc_id))

    return render_template("transfer.html", document=document)


@app.route("/document/<int:doc_id>")
def document_detail(doc_id: int):
    with get_db() as conn:
        document = conn.execute(
            "SELECT * FROM documents WHERE id = ?", (doc_id,)
        ).fetchone()
        transfers = conn.execute(
            """
            SELECT from_owner, to_owner, tx_hash, transferred_at, block_index
            FROM ownership_transfers
            WHERE document_id = ?
            ORDER BY id ASC
            """,
            (doc_id,),
        ).fetchall()

    if not document:
        flash("Không tìm thấy chứng từ.", "error")
        return redirect(url_for("index"))

    return render_template("detail.html", document=document, transfers=transfers)


@app.route("/uploads/<path:filename>")
def uploaded_file(filename: str):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
