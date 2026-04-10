# Crypto_GK - Demo Hệ thống Quản lý Bản quyền Kỹ thuật số

Demo này mô phỏng một hệ thống **Số hóa và Xác thực Chứng từ Tài chính** cho các tài liệu như:
- Vận đơn (Bill of Lading)
- Hợp đồng ngoại thương
- Chứng nhận quyền sử dụng tài sản

## Mục tiêu nghiệp vụ

Hệ thống giúp giảm rủi ro làm giả chứng từ bằng cách ghi nhận “dấu vân tay số” lên một sổ cái blockchain mô phỏng.

### Tính năng đã triển khai
1. **Digital Fingerprinting**
   - Tải file PDF lên.
   - Tạo mã định danh duy nhất bằng SHA-256 hash.

2. **Proof of Existence**
   - Khi đăng ký chứng từ, hệ thống tạo giao dịch với timestamp UTC.
   - Ghi block chứa hash và thông tin nghiệp vụ để chứng minh tài liệu tồn tại tại thời điểm đó.

3. **Ownership Transfer**
   - Cho phép chuyển quyền sở hữu chứng từ.
   - Mỗi lần chuyển tạo giao dịch mới, lưu lịch sử từ chủ cũ sang chủ mới.

## Công nghệ
- Python 3.10+
- Flask
- SQLite (lưu sổ cái và dữ liệu chứng từ)

## Cách chạy demo

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Truy cập: `http://127.0.0.1:5000`

## Luồng demo gợi ý

1. Vào **Đăng ký chứng từ** và tải lên 1 file PDF.
2. Hệ thống tạo hash + block timestamp.
3. Vào **Xác thực chứng từ**, tải lại file để kiểm tra tính nguyên gốc.
4. Vào **Chi tiết** và thực hiện **Chuyển quyền sở hữu**.
5. Kiểm tra lịch sử chuyển quyền được ghi nhận đầy đủ.

## Lưu ý
- Đây là demo kiến trúc, blockchain được mô phỏng bằng chuỗi block lưu trong SQLite.
- Có thể mở rộng sang smart contract thực tế (Ethereum, Hyperledger, v.v.) ở giai đoạn production.
