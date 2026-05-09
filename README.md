# Blockchain-based Inter-Organizational Financial Document Verification System

## 1. Giới thiệu đề tài

### Tên đề tài (Tiếng Việt)
Hệ thống xác thực và quản lý chứng từ tài chính liên tổ chức dựa trên Blockchain

### Tên đề tài (Tiếng Anh)
Blockchain-based Inter-Organizational Financial Document Verification System

---

## 2. Bối cảnh thực tế

Trong lĩnh vực tài chính và logistics, các chứng từ như:

- Bill of Lading (Vận đơn)
- Hợp đồng ngoại thương
- Hóa đơn tài chính
- Giấy chứng nhận quyền sở hữu tài sản

có thể bị:
- giả mạo
- chỉnh sửa nội dung
- thay đổi ngày ký kết
- chuyển nhượng trái phép

Điều này gây thiệt hại lớn cho:
- doanh nghiệp
- ngân hàng
- công ty bảo hiểm
- đơn vị logistics

Do đó, cần có một hệ thống:
- xác minh tính nguyên gốc tài liệu
- theo dõi lịch sử sở hữu
- đảm bảo minh bạch giữa nhiều tổ chức

---

## 3. Mục tiêu hệ thống

Hệ thống được xây dựng nhằm:

- Ngăn chặn giả mạo chứng từ
- Xác thực tính toàn vẹn của tài liệu
- Chứng minh thời điểm tài liệu được tạo
- Theo dõi lịch sử ownership
- Hỗ trợ kiểm toán và truy vết
- Tạo môi trường chia sẻ dữ liệu tin cậy giữa nhiều tổ chức

---

## 4. Ý tưởng giải pháp

Hệ thống sử dụng:

- Blockchain
- SHA-256 Hashing
- Digital Signature
- Timestamp Verification

để tạo:
- Digital Fingerprint
- Proof of Existence
- Ownership Tracking

Mỗi tài liệu sẽ được:
1. Tạo mã hash duy nhất
2. Ghi hash lên blockchain
3. Theo dõi lịch sử ownership
4. Kiểm tra tính hợp lệ khi cần

---

## 5. Yếu tố tổ chức (Multi-Organization)

### 5.1 Các tổ chức tham gia

Hệ thống không chỉ dành cho một công ty mà hoạt động theo mô hình liên tổ chức.

Các bên tham gia gồm:

| Tổ chức | Vai trò |
|---|---|
| Export Company | Tạo chứng từ |
| Import Company | Nhận ownership |
| Bank | Xác minh chứng từ tài chính |
| Customs | Kiểm tra thông quan |
| Insurance Company | Xác minh quyền sở hữu |
| Auditor | Kiểm toán |
| Blockchain Network | Xác thực giao dịch |

---

### 5.2 Mô hình Consortium Blockchain

Hệ thống sử dụng mô hình:

### Consortium Blockchain

Trong đó:
- nhiều tổ chức cùng vận hành blockchain node
- không có một bên duy nhất kiểm soát dữ liệu

Ví dụ:

| Blockchain Node | Tổ chức |
|---|---|
| Node 1 | Export Company |
| Node 2 | Bank |
| Node 3 | Customs |
| Node 4 | Insurance Company |

Ý nghĩa:
- tăng tính minh bạch
- giảm gian lận
- tạo shared trusted ledger

---

## 6. Chức năng chính của hệ thống

### 6.1 User Management

Chức năng:
- Đăng ký
- Đăng nhập
- Phân quyền

Vai trò:
- Admin
- Finance Staff
- Legal Staff
- Director
- Auditor
- External Partner

---

### 6.2 Upload và xác thực tài liệu

Người dùng:
- Finance Staff

Chức năng:
- Upload PDF
- Tạo SHA-256 Hash
- Tạo Digital Fingerprint

Kết quả:
- Mỗi tài liệu có mã định danh duy nhất.

---

### 6.3 Proof of Existence

Mục tiêu:
- Chứng minh tài liệu tồn tại tại một thời điểm cụ thể.

Cách hoạt động:
- Sau khi upload:
  - hash
  - timestamp

  được ghi lên blockchain.

Ý nghĩa:
- ngăn chặn việc lùi ngày chứng từ
- chống chỉnh sửa trái phép

---

### 6.4 Phê duyệt tài liệu

Quy trình:
1. Finance tạo tài liệu
2. Legal kiểm tra
3. Director ký số
4. Blockchain xác nhận

Chức năng:
- Approve
- Reject
- Audit log

---

### 6.5 Ownership Transfer

Mục tiêu:
- Quản lý việc chuyển giao ownership giữa các tổ chức.

Ví dụ:

Exporter
↓
Shipping Company
↓
Bank
↓
Importer

Blockchain ghi lại:
- owner cũ
- owner mới
- timestamp
- hash tài liệu

---

### 6.6 Verification

External Partner có thể:
- upload lại file
- hash lại tài liệu
- so sánh với blockchain

Kết quả:
- hợp lệ
- không hợp lệ

---

### 6.7 Audit & Tracking

Auditor có thể:
- kiểm tra lịch sử giao dịch
- xem ownership chain
- truy vết tài liệu
- phát hiện gian lận

---

## 7. Workflow nghiệp vụ

Quy trình chính:

```text
Upload File
    ↓
Generate SHA-256 Hash
    ↓
Legal Verification
    ↓
Digital Signature
    ↓
Store Hash on Blockchain
    ↓
Ownership Transfer
    ↓
Audit & Verification
```

---

## 8. Demo hiện tại

`Crypto_GK` là bản demo hệ thống chứng thực tài liệu tài chính với:

- Python + Flask
- SQLite làm sổ cái mô phỏng
- SHA-256 hashing cho digital fingerprint
- Block chaining bằng `tx_hash` và `previous_hash`

Tính năng đã triển khai trong demo:

1. Đăng ký chứng từ với upload PDF và tạo hash duy nhất.
2. Lưu giao dịch proof-of-existence lên bảng blockchain.
3. Xác thực lại file bằng cách hash và so sánh với dữ liệu lưu trữ.
4. Lưu lịch sử ownership và hiển thị số lần chuyển giao.

---

## 9. Cách chạy demo

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Mở trình duyệt và truy cập: `http://127.0.0.1:5000`

---

## 10. Lưu ý

- Đây là demo kiến trúc; blockchain được mô phỏng bằng chuỗi block lưu trong SQLite.
- Có thể mở rộng sang smart contract hoặc mạng consortium blockchain thực tế ở giai đoạn production.
- Hiện tại hệ thống chỉ hỗ trợ file PDF và dùng SQLite nội bộ.
