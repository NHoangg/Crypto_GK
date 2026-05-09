# Dashboard Hướng dẫn - Từng Vai trò Có Trang Riêng

## Tổng Quan

Hệ thống đã được cải tiến với **Dashboard riêng cho mỗi vai trò**. Khi người dùng đăng nhập, họ sẽ thấy một dashboard được thiết kế đặc biệt cho vai trò của họ với các thống kê và hành động cụ thể.

## Cấu Trúc Dashboard

```
/dashboard              → Redirect dựa trên vai trò người dùng
/dashboard/content-creator    → Dashboard cho Content Creator
/dashboard/censor              → Dashboard cho Censor
/dashboard/publisher           → Dashboard cho Publisher
/dashboard/customer            → Dashboard cho Customer
/dashboard/legal-authority     → Dashboard cho Legal Authority
```

## Chi tiết Từng Role Dashboard

### 1. Content Creator Dashboard (`/dashboard/content-creator`)

**Ở đây người dùng có thể:**

| Hành động | Mô tả |
|-----------|-------|
| 📄 Đăng ký chứng từ mới | Tải lên PDF để tạo chứng từ |
| 📋 Xem chứng từ đã tạo | Danh sách toàn bộ chứng từ của bạn |
| ➡️ Chuyển giao quyền sở hữu | Chuyển ownership cho người khác |
| ✅ Xác thực chứng từ | Kiểm tra tính hợp lệ tài liệu |

**Thống kê hiển thị:**
- Tổng chứng từ đã tạo
- Chứng từ chờ kiểm duyệt
- Chứng từ đã phê duyệt
- Chứng từ bị từ chối

**Danh sách hiển thị:**
- 5 chứng từ gần đây đang chờ kiểm duyệt
- 5 chứng từ đã phê duyệt gần đây

---

### 2. Censor Dashboard (`/dashboard/censor`)

**Ở đây người dùng có thể:**

| Hành động | Mô tả |
|-----------|-------|
| 🔍 Kiểm duyệt chứng từ | Xem danh sách cần kiểm duyệt |
| ✓ Phê duyệt hoặc từ chối | Nêu ý kiến về nội dung |
| 📊 Lịch sử phê duyệt | Xem chứng từ bạn đã phê duyệt |
| 📄 Xem chi tiết tài liệu | Kiểm tra nội dung chi tiết |

**Thống kê hiển thị:**
- Chứng từ chờ kiểm duyệt (badge)
- Chứng từ đã phê duyệt
- Chứng từ bị từ chối

**Danh sách hiển thị:**
- Các chứng từ chờ kiểm duyệt
- Link trực tiếp để kiểm duyệt

---

### 3. Publisher Dashboard (`/dashboard/publisher`)

**Ở đây người dùng có thể:**

| Hành động | Mô tả |
|-----------|-------|
| 📑 Phê duyệt chứng từ | Ký số tài liệu |
| ✍️ Ký số tài liệu | Thực hiện ký số điện tử |
| ✓ Lịch sử phê duyệt | Xem chứng từ đã ký |
| ➡️ Chuyển giao quyền | Chuyển ownership sau phê duyệt |

**Thống kê hiển thị:**
- Chứng từ chờ phê duyệt (badge)
- Chứng từ đã ký số
- Chứng từ bị từ chối
- Tổng chứng từ phê duyệt trong hệ thống

**Danh sách hiển thị:**
- Chứng từ chờ ký số với nút "Phê duyệt"
- Chứng từ đã ký gần đây

---

### 4. Customer Dashboard (`/dashboard/customer`)

**Ở đây người dùng có thể:**

| Hành động | Mô tả |
|-----------|-------|
| 💼 Chứng từ của tôi | Xem danh sách ownership |
| ✅ Xác thực chứng từ | Kiểm chứng tính hợp lệ |
| ➡️ Chuyển giao quyền | Chuyển cho người nhận |
| 📜 Lịch sử chuyển giao | Xem toàn bộ lịch sử |

**Thống kê hiển thị:**
- Tổng chứng từ sở hữu
- Chứng từ đã phê duyệt
- Chứng từ đang xử lý

**Danh sách hiển thị:**
- 5 chứng từ gần đây sở hữu
- Trạng thái phê duyệt của mỗi chứng từ

---

### 5. Legal Authority Dashboard (`/dashboard/legal-authority`)

**Ở đây người dùng có thể:**

| Hành động | Mô tả |
|-----------|-------|
| ⚖️ Giám sát toàn bộ hệ thống | Xem tất cả chứng từ |
| 🗑️ Xóa chứng từ | Xóa tài liệu (quyền toàn quyền) |
| 📚 Xem nhật ký kiểm toán | Truy cập audit log đầy đủ |
| ⚡ Phê duyệt khẩn cấp | Override quy trình bình thường |
| 📊 Báo cáo hệ thống | Xem thống kê chi tiết |

**Thống kê hiển thị:**
- Tổng chứng từ trong hệ thống
- Chứng từ đã phê duyệt
- Chứng từ bị từ chối
- Chứng từ đang xử lý

**Danh sách hiển thị:**
- Chứng từ đang xử lý
- Chứng từ đã phê duyệt gần đây

**Thông tin đặc biệt:**
- Trạng thái hệ thống
- Quyền hạn và trách nhiệm
- Lưu ý bảo mật

---

## Cấu Trúc Template

### Base Template: `templates/dashboard/base.html`
- Định nghĩa layout chung
- CSS cho các component (stat-card, action-card, document-list)
- Block `dashboard_content` cho nội dung riêng

### Role-Specific Templates:
```
templates/dashboard/
├── base.html                    ← Base layout
├── content_creator.html         ← Content Creator dashboard
├── censor.html                  ← Censor dashboard
├── publisher.html               ← Publisher dashboard
├── customer.html                ← Customer dashboard
└── legal_authority.html         ← Legal Authority dashboard
```

## Routes

### Điểm vào chung:
```python
@dashboard_bp.route("/dashboard")
def dashboard():
    # Redirect dựa trên role của người dùng hiện tại
```

### Routes cụ thể:
```python
@dashboard_bp.route("/dashboard/content-creator")
def content_creator_dashboard():
    ...

@dashboard_bp.route("/dashboard/censor")
def censor_dashboard():
    ...

@dashboard_bp.route("/dashboard/publisher")
def publisher_dashboard():
    ...

@dashboard_bp.route("/dashboard/customer")
def customer_dashboard():
    ...

@dashboard_bp.route("/dashboard/legal-authority")
def legal_authority_dashboard():
    ...
```

## Navigation

Dashboard được thêm vào navigation chính với icon:
```html
{% if current_user.is_authenticated %}
  <a href="{{ url_for('dashboard.dashboard') }}">
    <i class="ph ph-monitor"></i> Dashboard
  </a>
{% endif %}
```

## Action Cards

Mỗi dashboard có 4-5 action card với:
- **Icon** - Biểu tượng Phosphor
- **Title** - Tiêu đề hành động
- **Description** - Mô tả chi tiết
- **Color** - Màu theo vai trò
- **URL** - Link đến trang thực hiện
- **Badge** (tùy chọn) - Hiển thị số lượng chứng từ cần xử lý

## Statistics Cards

Mỗi dashboard hiển thị các thống kê liên quan:
- Định dạng grid tự động
- Giá trị lớn, tiêu đề nhỏ
- Border trái màu theo vai trò

## Document Lists

Hiển thị danh sách chứng từ với:
- Tên file (link đến chi tiết)
- Metadata (ID, hash, ngày tạo, người tạo, v.v.)
- Status badge (Pending, Approved, Rejected)
- Action button (khi cần)

## Styling

Dashboard sử dụng:
- **Color scheme** - Mỗi role có màu đặc trưng từ config.py
- **Gradient header** - Gradient từ color của role
- **Responsive grid** - `grid-template-columns: repeat(auto-fit, minmax(...))`
- **Hover effects** - Card nâng lên khi hover
- **Information boxes** - Hướng dẫn đặc biệt cho mỗi role

## Cách Sử Dụng

### 1. Truy cập Dashboard:
```
Sau khi đăng nhập → Bấm "Dashboard" trong navigation
hoặc truy cập trực tiếp: http://localhost:5000/dashboard
```

### 2. Tự động Redirect:
```python
/dashboard → /dashboard/{role-specific}
# Ví dụ:
/dashboard → /dashboard/content-creator
```

### 3. Các hành động:
- Bấm vào action card để thực hiện hành động
- Các chứng từ trong danh sách có thể bấm để xem chi tiết
- Status badge cho thấy trạng thái hiện tại

## Lợi ích

✅ **Trực quan** - Mỗi role có giao diện phù hợp  
✅ **Hiệu quả** - Nhanh chóng tìm hành động cần làm  
✅ **Thông tin tức thì** - Xem thống kê ngay lập tức  
✅ **Hướng dẫn** - Hộp thông tin giúp người dùng  
✅ **Chuyên nghiệp** - Thiết kế phù hợp với từng vai trò  

## Mở rộng

Để thêm hành động mới cho một role:

```python
# 1. Cập nhật dashboard_routes.py
actions.append({
    "title": "Tiêu đề",
    "description": "Mô tả",
    "icon": "ph-icon-name",
    "url": url_for("route.handler"),
    "color": "#color",
    "badge": count,  # tùy chọn
})

# 2. Template sẽ tự động hiển thị
{% for action in actions %}
  <a href="{{ action.url }}" class="action-card">
    <!-- Auto rendered -->
  </a>
{% endfor %}
```

## Xem thêm

- [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) - Hướng dẫn refactor kiến trúc
- [ARCHITECTURE.md](ARCHITECTURE.md) - Tài liệu kiến trúc hệ thống
- `routes/dashboard_routes.py` - Dashboard routes
- `templates/dashboard/` - Dashboard templates
