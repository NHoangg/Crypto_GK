"""Dashboard routes for role-specific views."""

from flask import Blueprint, render_template, session, redirect, url_for
from models.database import DatabaseManager
from config import ROLES

dashboard_bp = Blueprint("dashboard", __name__)

db_manager = DatabaseManager()


def get_current_user():
    """Get current user from session."""
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


@dashboard_bp.route("/dashboard")
def dashboard():
    """Route to role-specific dashboard."""
    user = get_current_user()
    
    if not user["is_authenticated"]:
        return redirect(url_for("auth.login"))
    
    # Route to role-specific dashboard
    if user["role"] == "Content Creator":
        return redirect(url_for("dashboard.content_creator_dashboard"))
    elif user["role"] == "Censor":
        return redirect(url_for("dashboard.censor_dashboard"))
    elif user["role"] == "Publisher":
        return redirect(url_for("dashboard.publisher_dashboard"))
    elif user["role"] == "Customer":
        return redirect(url_for("dashboard.customer_dashboard"))
    elif user["role"] == "Legal Authority":
        return redirect(url_for("dashboard.legal_authority_dashboard"))
    
    return redirect(url_for("document.index"))


@dashboard_bp.route("/dashboard/content-creator")
def content_creator_dashboard():
    """Content Creator Dashboard."""
    user = get_current_user()
    
    if not user["is_authenticated"] or user["role"] != "Content Creator":
        return redirect(url_for("auth.login"))
    
    # Get statistics
    all_docs = db_manager.get_all_documents()
    created_docs = [d for d in all_docs if d["creator"] == user["name"]]
    pending_docs = [d for d in created_docs if d["approval_status"] == "Pending Censor Review"]
    approved_docs = [d for d in created_docs if d["approval_status"] == "Approved"]
    rejected_docs = [d for d in created_docs if d["approval_status"] == "Rejected"]
    
    stats = {
        "total_created": len(created_docs),
        "pending_review": len(pending_docs),
        "approved": len(approved_docs),
        "rejected": len(rejected_docs),
    }
    
    actions = [
        {
            "title": "Đăng ký chứng từ mới",
            "description": "Tải lên tài liệu PDF để tạo tài liệu mới",
            "icon": "ph-plus-circle",
            "url": url_for("document.register_document"),
            "color": "#60a5fa",
        },
        {
            "title": "Xem chứng từ đã tạo",
            "description": f"Bạn đã tạo {stats['total_created']} chứng từ",
            "icon": "ph-list",
            "url": url_for("document.index"),
            "color": "#3b82f6",
        },
        {
            "title": "Chuyển giao quyền sở hữu",
            "description": "Chuyển quyền sở hữu chứng từ cho người khác",
            "icon": "ph-arrow-right",
            "url": url_for("document.index"),
            "color": "#06b6d4",
        },
        {
            "title": "Xác thực chứng từ",
            "description": "Kiểm tra tính hợp lệ của chứng từ",
            "icon": "ph-check-circle",
            "url": url_for("verification.verify_document"),
            "color": "#10b981",
        },
    ]
    
    return render_template(
        "dashboard/content_creator.html",
        user=user,
        stats=stats,
        actions=actions,
        pending_docs=pending_docs[:5],
        approved_docs=approved_docs[:5],
    )


@dashboard_bp.route("/dashboard/censor")
def censor_dashboard():
    """Censor Dashboard."""
    user = get_current_user()
    
    if not user["is_authenticated"] or user["role"] != "Censor":
        return redirect(url_for("auth.login"))
    
    # Get statistics
    all_docs = db_manager.get_all_documents()
    pending_review = [d for d in all_docs if d["approval_status"] == "Pending Censor Review"]
    approved_by_censor = [d for d in all_docs if d["approval_status"] == "Pending Publisher Approval"]
    rejected_by_censor = [d for d in all_docs if d["approval_status"] == "Rejected"]
    
    stats = {
        "pending_review": len(pending_review),
        "approved_by_me": len(approved_by_censor),
        "rejected": len(rejected_by_censor),
    }
    
    actions = [
        {
            "title": "Kiểm duyệt chứng từ",
            "description": f"Có {stats['pending_review']} chứng từ đang chờ kiểm duyệt",
            "icon": "ph-magnifying-glass",
            "url": url_for("document.index"),
            "color": "#f59e0b",
            "badge": stats["pending_review"],
        },
        {
            "title": "Lịch sử phê duyệt",
            "description": f"Bạn đã phê duyệt {stats['approved_by_me']} chứng từ",
            "icon": "ph-check-double",
            "url": url_for("document.index"),
            "color": "#fbbf24",
        },
        {
            "title": "Chứng từ bị từ chối",
            "description": f"Tổng cộng {stats['rejected']} chứng từ bị từ chối",
            "icon": "ph-x-circle",
            "url": url_for("document.index"),
            "color": "#f87171",
        },
        {
            "title": "Xem chi tiết tài liệu",
            "description": "Kiểm tra nội dung chi tiết của các chứng từ",
            "icon": "ph-file-text",
            "url": url_for("document.index"),
            "color": "#a78bfa",
        },
    ]
    
    return render_template(
        "dashboard/censor.html",
        user=user,
        stats=stats,
        actions=actions,
        pending_docs=pending_review[:5],
    )


@dashboard_bp.route("/dashboard/publisher")
def publisher_dashboard():
    """Publisher Dashboard."""
    user = get_current_user()
    
    if not user["is_authenticated"] or user["role"] != "Publisher":
        return redirect(url_for("auth.login"))
    
    # Get statistics
    all_docs = db_manager.get_all_documents()
    pending_publisher = [d for d in all_docs if d["approval_status"] == "Pending Publisher Approval"]
    approved_by_me = [d for d in all_docs if d["approval_status"] == "Approved" and d["approved_by"] == user["name"]]
    rejected_by_me = [d for d in all_docs if d["approval_status"] == "Rejected" and d["rejected_by"] == user["name"]]
    
    stats = {
        "pending_approval": len(pending_publisher),
        "approved_by_me": len(approved_by_me),
        "rejected_by_me": len(rejected_by_me),
        "total_approved": len([d for d in all_docs if d["approval_status"] == "Approved"]),
    }
    
    actions = [
        {
            "title": "Phê duyệt chứng từ",
            "description": f"Có {stats['pending_approval']} chứng từ chờ ký số",
            "icon": "ph-broadcast",
            "url": url_for("document.index"),
            "color": "#10b981",
            "badge": stats["pending_approval"],
        },
        {
            "title": "Ký số tài liệu",
            "description": "Thực hiện ký số điện tử trên chứng từ",
            "icon": "ph-signature",
            "url": url_for("document.index"),
            "color": "#059669",
        },
        {
            "title": "Lịch sử phê duyệt",
            "description": f"Bạn đã ký số {stats['approved_by_me']} chứng từ",
            "icon": "ph-check-circle",
            "url": url_for("document.index"),
            "color": "#34d399",
        },
        {
            "title": "Chuyển giao quyền",
            "description": "Chuyển quyền sở hữu chứng từ đã phê duyệt",
            "icon": "ph-arrow-right",
            "url": url_for("document.index"),
            "color": "#6ee7b7",
        },
    ]
    
    return render_template(
        "dashboard/publisher.html",
        user=user,
        stats=stats,
        actions=actions,
        pending_docs=pending_publisher[:5],
        approved_docs=approved_by_me[:5],
    )


@dashboard_bp.route("/dashboard/customer")
def customer_dashboard():
    """Customer Dashboard."""
    user = get_current_user()
    
    if not user["is_authenticated"] or user["role"] != "Customer":
        return redirect(url_for("auth.login"))
    
    # Get statistics
    all_docs = db_manager.get_all_documents()
    owned_docs = [d for d in all_docs if d["owner"] == user["name"]]
    approved_docs = [d for d in owned_docs if d["approval_status"] == "Approved"]
    
    stats = {
        "total_owned": len(owned_docs),
        "approved": len(approved_docs),
        "pending": len([d for d in owned_docs if d["approval_status"] != "Approved"]),
    }
    
    actions = [
        {
            "title": "Chứng từ của tôi",
            "description": f"Bạn sở hữu {stats['total_owned']} chứng từ",
            "icon": "ph-briefcase",
            "url": url_for("document.index"),
            "color": "#a78bfa",
        },
        {
            "title": "Xác thực chứng từ",
            "description": "Kiểm chứng tính hợp lệ của tài liệu",
            "icon": "ph-check-circle",
            "url": url_for("verification.verify_document"),
            "color": "#c4b5fd",
        },
        {
            "title": "Chuyển giao quyền",
            "description": "Chuyển quyền sở hữu cho đối tượng khác",
            "icon": "ph-arrow-right",
            "url": url_for("document.index"),
            "color": "#ddd6fe",
        },
        {
            "title": "Lịch sử chuyển giao",
            "description": "Xem toàn bộ lịch sử ownership",
            "icon": "ph-list",
            "url": url_for("document.index"),
            "color": "#e9d5ff",
        },
    ]
    
    return render_template(
        "dashboard/customer.html",
        user=user,
        stats=stats,
        actions=actions,
        owned_docs=owned_docs[:5],
    )


@dashboard_bp.route("/dashboard/legal-authority")
def legal_authority_dashboard():
    """Legal Authority Dashboard."""
    user = get_current_user()
    
    if not user["is_authenticated"] or user["role"] != "Legal Authority":
        return redirect(url_for("auth.login"))
    
    # Get statistics
    all_docs = db_manager.get_all_documents()
    approved_docs = [d for d in all_docs if d["approval_status"] == "Approved"]
    rejected_docs = [d for d in all_docs if d["approval_status"] == "Rejected"]
    pending_docs = [d for d in all_docs if d["approval_status"] in ("Pending Censor Review", "Pending Publisher Approval")]
    
    stats = {
        "total_documents": len(all_docs),
        "approved": len(approved_docs),
        "rejected": len(rejected_docs),
        "pending": len(pending_docs),
    }
    
    actions = [
        {
            "title": "Giám sát toàn bộ chứng từ",
            "description": f"Quản lý {stats['total_documents']} chứng từ trong hệ thống",
            "icon": "ph-scales",
            "url": url_for("document.index"),
            "color": "#f87171",
            "badge": stats["total_documents"],
        },
        {
            "title": "Xóa chứng từ",
            "description": "Xóa tài liệu khỏi hệ thống (quyền toàn quyền)",
            "icon": "ph-trash",
            "url": url_for("document.index"),
            "color": "#ef4444",
        },
        {
            "title": "Xem nhật ký kiểm toán",
            "description": "Kiểm tra lịch sử tất cả hoạt động trong hệ thống",
            "icon": "ph-books",
            "url": url_for("document.index"),
            "color": "#dc2626",
        },
        {
            "title": "Phê duyệt khẩn cấp",
            "description": "Override quy trình phê duyệt khi cần thiết",
            "icon": "ph-lightning",
            "url": url_for("document.index"),
            "color": "#b91c1c",
        },
        {
            "title": "Báo cáo hệ thống",
            "description": "Xem các báo cáo thống kê chi tiết",
            "icon": "ph-chart-bar",
            "url": url_for("document.index"),
            "color": "#991b1b",
        },
    ]
    
    return render_template(
        "dashboard/legal_authority.html",
        user=user,
        stats=stats,
        actions=actions,
        pending_docs=pending_docs[:5],
        approved_docs=approved_docs[:5],
    )
