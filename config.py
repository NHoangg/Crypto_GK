"""Configuration for the multi-party document verification system."""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
DB_PATH = BASE_DIR / "ledger.db"

# Flask configuration
SECRET_KEY = os.environ.get("FLASK_SECRET", "demo-secret-key")
DEBUG = os.environ.get("FLASK_DEBUG", "True") == "True"

# File upload configuration
ALLOWED_EXTENSIONS = {"pdf"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

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
        "priority": 1,
    },
    "Censor": {
        "label": "Đơn vị kiểm duyệt",
        "icon": "ph-magnifying-glass",
        "color": "#f59e0b",
        "priority": 2,
    },
    "Publisher": {
        "label": "Nhà phát hành",
        "icon": "ph-broadcast",
        "color": "#10b981",
        "priority": 3,
    },
    "Customer": {
        "label": "Khách hàng",
        "icon": "ph-user",
        "color": "#a78bfa",
        "priority": 4,
    },
    "Legal Authority": {
        "label": "Cơ quan pháp lý",
        "icon": "ph-scales",
        "color": "#f87171",
        "priority": 5,
    },
}

# Luồng trạng thái phê duyệt
STATUS_FLOW = {
    "Pending Censor Review": "Chờ kiểm duyệt",
    "Pending Publisher Approval": "Chờ nhà phát hành phê duyệt",
    "Approved": "Đã phê duyệt",
    "Rejected": "Bị từ chối",
}

# Approval workflow stages
APPROVAL_STAGES = [
    ("Pending Censor Review", "Censor", "Content Creator"),
    ("Pending Publisher Approval", "Publisher", "Censor"),
    ("Approved", None, "Publisher"),
]
