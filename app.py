import hashlib
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
DB_PATH = BASE_DIR / "ledger.db"
ALLOWED_EXTENSIONS = {"pdf"}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "demo-secret-key")

# ── Vai trò hệ thống (5 bên) ──────────────────────────────────────────────────
# Content Creator  : Công ty sáng tạo nội dung – đăng ký chứng từ
# Censor           : Đơn vị kiểm duyệt         – kiểm duyệt lần 1
# Publisher        : Nhà phát hành              – phê duyệt & ký số cuối
# Customer         : Khách hàng                 – xem / xác thực / nhận quyền
# Legal Authority  : Cơ quan pháp lý            – toàn quyền giám sát & xóa
ROLES = {
    "Content Creator": {
        "label": "Công ty sáng tạo nội dung",
        "icon": "ph-pencil-simple",
        "color": "#60a5fa",
    },
    "Censor": {
        "label": "Đơn vị kiểm duyệt",
        "icon": "ph-magnifying-glass",
        "color": "#f59e0b",
    },
    "Publisher": {
        "label": "Nhà phát hành",
        "icon": "ph-broadcast",
        "color": "#10b981",
    },
    "Customer": {
        "label": "Khách hàng",
        "icon": "ph-user",
        "color": "#a78bfa",
    },
    "Legal Authority": {
        "label": "Cơ quan pháp lý",
        "icon": "ph-scales",
        "color": "#f87171",
    },
}

# Luồng trạng thái phê duyệt
STATUS_FLOW = {
    "Pending Censor Review": "Chờ kiểm duyệt",
    "Pending Publisher Approval": "Chờ nhà phát hành phê duyệt",
    "Approved": "Đã phê duyệt",
    "Rejected": "Bị từ chối",
}


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


def get_current_user() -> dict:
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


@app.context_processor
def inject_globals():
    return {
        "current_user": get_current_user(),
        "ROLES": ROLES,
        "STATUS_FLOW": STATUS_FLOW,
    }


def log_audit(document_id, action: str, details: str, role: str, performed_by: str,
              tx_hash=None, block_index=None) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO audit_log(document_id, action, performed_by, role, details, created_at, tx_hash, block_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (document_id, action, performed_by, role, details, utc_now_iso(), tx_hash, block_index),
        )


# ── Auth ───────────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        role = request.form.get("role", "").strip()
        if not name or role not in ROLES:
            flash("Vui lòng nhập tên và chọn vai trò hợp lệ.", "error")
            return redirect(url_for("login"))
        session["user_name"] = name
        session["user_role"] = role
        flash(f"Đăng nhập thành công với vai trò: {ROLES[role]['label']}.", "success")
        return redirect(url_for("index"))
    return render_template("login.html", roles=ROLES)


@app.route("/logout")
def logout():
    session.clear()
    flash("Đã đăng xuất.", "success")
    return redirect(url_for("index"))


# ── Trang chủ ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    with get_db() as conn:
        documents = conn.execute(
            """
            SELECT d.id, d.filename, d.file_hash, d.owner, d.creator, d.created_at, d.tx_hash,
                   d.block_index, d.approval_status,
                   (SELECT COUNT(*) FROM ownership_transfers ot WHERE ot.document_id = d.id) AS transfer_count
            FROM documents d
            ORDER BY d.id DESC
            """
        ).fetchall()
    return render_template("index.html", documents=documents)


# ── Đăng ký chứng từ (Content Creator) ───────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register_document():
    user = get_current_user()
    if request.method == "POST":
        if not user["is_authenticated"] or user["role"] not in ("Content Creator", "Legal Authority"):
            flash("Chỉ Công ty sáng tạo nội dung mới có quyền đăng ký chứng từ.", "error")
            return redirect(url_for("register_document"))

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
                INSERT INTO documents(filename, file_hash, tx_hash, owner, creator, created_at, block_index, approval_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (storage_name, doc_hash, tx_hash, owner, creator, created_at, block_index, "Pending Censor Review"),
            )
            new_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

        log_audit(
            document_id=new_id, action="Register",
            details=f"Công ty sáng tạo nội dung đăng ký chứng từ, chủ sở hữu ban đầu: {owner}.",
            role=user["role"], performed_by=user["name"],
            tx_hash=tx_hash, block_index=block_index,
        )

        flash("Đăng ký chứng từ thành công. Chứng từ đang chờ Đơn vị kiểm duyệt xem xét.", "success")
        return redirect(url_for("index"))

    return render_template("register.html")


# ── Xác thực chứng từ ─────────────────────────────────────────────────────────

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

        user = get_current_user()
        if result:
            log_audit(
                document_id=result["id"], action="Verify",
                details="Xác thực file PDF upload với hash đã lưu.",
                role=user["role"], performed_by=user["name"],
                tx_hash=result["tx_hash"], block_index=result["block_index"],
            )
        else:
            flash("Không tìm thấy chứng từ trên sổ cái.", "error")

    return render_template("verify.html", result=result)


# ── Chuyển quyền sở hữu ───────────────────────────────────────────────────────

@app.route("/transfer/<int:doc_id>", methods=["GET", "POST"])
def transfer_ownership(doc_id: int):
    user = get_current_user()
    with get_db() as conn:
        document = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        if not document:
            flash("Không tìm thấy chứng từ.", "error")
            return redirect(url_for("index"))

    if request.method == "POST":
        # Chỉ Publisher, Content Creator, Legal Authority mới có thể chuyển quyền
        if user["is_authenticated"] and user["role"] not in ("Publisher", "Content Creator", "Legal Authority"):
            flash("Bạn không có quyền chuyển quyền sở hữu.", "error")
            return redirect(url_for("document_detail", doc_id=doc_id))

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
                INSERT INTO ownership_transfers(document_id, from_owner, to_owner, tx_hash, transferred_at, block_index)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (doc_id, from_owner, new_owner, tx_hash, transferred_at, block_index),
            )

        log_audit(
            document_id=doc_id, action="Transfer",
            details=f"Chuyển quyền sở hữu từ '{from_owner}' sang '{new_owner}'.",
            role=user["role"], performed_by=user["name"],
            tx_hash=tx_hash, block_index=block_index,
        )

        flash("Chuyển quyền sở hữu thành công và đã ghi lên blockchain.", "success")
        return redirect(url_for("document_detail", doc_id=doc_id))

    return render_template("transfer.html", document=document)


# ── Chi tiết chứng từ ─────────────────────────────────────────────────────────

@app.route("/document/<int:doc_id>")
def document_detail(doc_id: int):
    with get_db() as conn:
        document = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        transfers = conn.execute(
            """
            SELECT from_owner, to_owner, tx_hash, transferred_at, block_index
            FROM ownership_transfers WHERE document_id = ? ORDER BY id ASC
            """,
            (doc_id,),
        ).fetchall()
        audit_logs = conn.execute(
            """
            SELECT action, performed_by, role, details, created_at, tx_hash, block_index
            FROM audit_log WHERE document_id = ? ORDER BY id ASC
            """,
            (doc_id,),
        ).fetchall()

    if not document:
        flash("Không tìm thấy chứng từ.", "error")
        return redirect(url_for("index"))

    return render_template("detail.html", document=document, transfers=transfers, audit_logs=audit_logs)


# ── Quy trình phê duyệt (Censor → Publisher) ─────────────────────────────────

@app.route("/document/<int:doc_id>/review", methods=["POST"])
def review_document(doc_id: int):
    user = get_current_user()
    if not user["is_authenticated"]:
        flash("Vui lòng đăng nhập để thực hiện thao tác này.", "error")
        return redirect(url_for("login"))

    action = request.form.get("action")
    reason = request.form.get("reason", "").strip()

    with get_db() as conn:
        document = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()

    if not document:
        flash("Không tìm thấy chứng từ.", "error")
        return redirect(url_for("index"))

    status = document["approval_status"]

    if action == "approve":
        # Bước 1: Censor kiểm duyệt → Pending Publisher Approval
        if user["role"] == "Censor" and status == "Pending Censor Review":
            new_status = "Pending Publisher Approval"
            details = "Đơn vị kiểm duyệt đã xác nhận nội dung. Chờ Nhà phát hành phê duyệt."
            with get_db() as conn:
                conn.execute("UPDATE documents SET approval_status = ? WHERE id = ?", (new_status, doc_id))

        # Bước 2: Publisher phê duyệt cuối → Approved
        elif user["role"] == "Publisher" and status == "Pending Publisher Approval":
            new_status = "Approved"
            approved_at = utc_now_iso()
            details = f"Nhà phát hành '{user['name']}' đã ký số và phê duyệt chứng từ."
            with get_db() as conn:
                conn.execute(
                    "UPDATE documents SET approval_status = ?, approved_by = ?, approved_at = ? WHERE id = ?",
                    (new_status, user["name"], approved_at, doc_id),
                )

        # Legal Authority có thể phê duyệt ở bất kỳ bước nào
        elif user["role"] == "Legal Authority":
            new_status = "Approved"
            approved_at = utc_now_iso()
            details = f"Cơ quan pháp lý '{user['name']}' phê duyệt khẩn cấp chứng từ."
            with get_db() as conn:
                conn.execute(
                    "UPDATE documents SET approval_status = ?, approved_by = ?, approved_at = ? WHERE id = ?",
                    (new_status, user["name"], approved_at, doc_id),
                )

        else:
            flash("Bạn không có quyền thực hiện thao tác này hoặc tài liệu không ở trạng thái phù hợp.", "error")
            return redirect(url_for("document_detail", doc_id=doc_id))

        log_audit(
            document_id=doc_id, action="Approve", details=details,
            role=user["role"], performed_by=user["name"],
            tx_hash=document["tx_hash"], block_index=document["block_index"],
        )
        flash("Cập nhật trạng thái phê duyệt thành công.", "success")
        return redirect(url_for("document_detail", doc_id=doc_id))

    if action == "reject":
        allowed_to_reject = (
            (user["role"] == "Censor" and status == "Pending Censor Review") or
            (user["role"] == "Publisher" and status == "Pending Publisher Approval") or
            user["role"] == "Legal Authority"
        )
        if allowed_to_reject and status not in ("Approved", "Rejected"):
            rejected_at = utc_now_iso()
            with get_db() as conn:
                conn.execute(
                    "UPDATE documents SET approval_status = ?, rejected_by = ?, rejected_at = ?, rejection_reason = ? WHERE id = ?",
                    ("Rejected", user["name"], rejected_at, reason or "Không có lý do cụ thể", doc_id),
                )
            log_audit(
                document_id=doc_id, action="Reject",
                details=f"Từ chối: {reason or 'Không có lý do cụ thể'}.",
                role=user["role"], performed_by=user["name"],
                tx_hash=document["tx_hash"], block_index=document["block_index"],
            )
            flash("Tài liệu đã bị từ chối.", "success")
            return redirect(url_for("document_detail", doc_id=doc_id))

        flash("Bạn không có quyền từ chối hoặc tài liệu không ở trạng thái phù hợp.", "error")
        return redirect(url_for("document_detail", doc_id=doc_id))

    flash("Hành động không hợp lệ.", "error")
    return redirect(url_for("document_detail", doc_id=doc_id))


# ── Xóa chứng từ (Legal Authority) ───────────────────────────────────────────

@app.route("/document/<int:doc_id>/delete", methods=["POST"])
def delete_document(doc_id: int):
    user = get_current_user()
    if not user["is_authenticated"]:
        flash("Vui lòng đăng nhập để thực hiện thao tác này.", "error")
        return redirect(url_for("login"))

    if user["role"] != "Legal Authority":
        flash("Chỉ Cơ quan pháp lý mới có quyền xóa tài liệu.", "error")
        return redirect(url_for("document_detail", doc_id=doc_id))

    with get_db() as conn:
        document = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()

    if not document:
        flash("Không tìm thấy chứng từ.", "error")
        return redirect(url_for("index"))

    log_audit(
        document_id=doc_id, action="Delete",
        details=f"Cơ quan pháp lý xóa chứng từ '{document['filename']}' (hash: {document['file_hash'][:16]}...).",
        role=user["role"], performed_by=user["name"],
        tx_hash=document["tx_hash"], block_index=document["block_index"],
    )

    file_path = UPLOAD_DIR / document["filename"]
    file_path.unlink(missing_ok=True)

    with get_db() as conn:
        conn.execute("DELETE FROM ownership_transfers WHERE document_id = ?", (doc_id,))
        conn.execute("DELETE FROM audit_log WHERE document_id = ?", (doc_id,))
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

    flash(f"Đã xóa chứng từ #{doc_id} thành công.", "success")
    return redirect(url_for("index"))


@app.route("/documents/delete-all", methods=["POST"])
def delete_all_documents():
    user = get_current_user()
    if not user["is_authenticated"]:
        flash("Vui lòng đăng nhập để thực hiện thao tác này.", "error")
        return redirect(url_for("login"))

    if user["role"] != "Legal Authority":
        flash("Chỉ Cơ quan pháp lý mới có quyền xóa toàn bộ tài liệu.", "error")
        return redirect(url_for("index"))

    with get_db() as conn:
        documents = conn.execute("SELECT id, filename, file_hash, tx_hash, block_index FROM documents").fetchall()

    if not documents:
        flash("Không có chứng từ nào để xóa.", "error")
        return redirect(url_for("index"))

    count = len(documents)

    for doc in documents:
        log_audit(
            document_id=doc["id"], action="Delete",
            details=f"Cơ quan pháp lý xóa hàng loạt: '{doc['filename']}' (hash: {doc['file_hash'][:16]}...).",
            role=user["role"], performed_by=user["name"],
            tx_hash=doc["tx_hash"], block_index=doc["block_index"],
        )

    for doc in documents:
        file_path = UPLOAD_DIR / doc["filename"]
        file_path.unlink(missing_ok=True)

    with get_db() as conn:
        conn.execute("DELETE FROM ownership_transfers")
        conn.execute("DELETE FROM audit_log")
        conn.execute("DELETE FROM documents")

    flash(f"Đã xóa toàn bộ {count} chứng từ thành công.", "success")
    return redirect(url_for("index"))


@app.route("/uploads/<path:filename>")
def uploaded_file(filename: str):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
