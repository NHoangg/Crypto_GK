# Multi-Party Architecture Refactoring Complete

## Overview

Your blockchain-based document verification system has been refactored into a **modular, role-based architecture** with clean separation of concerns. The system supports 5 distinct stakeholders in a document approval workflow.

## New Structure

```
crypto_gk/
├── app_new.py                  # Main Flask app (refactored)
├── config.py                   # Configuration & roles
├── models/
│   ├── __init__.py
│   └── database.py            # Database operations
├── services/                  # Business logic by concern
│   ├── __init__.py
│   ├── blockchain_service.py  # Blockchain operations
│   ├── audit_service.py       # Audit logging
│   ├── document_service.py    # Document management
│   ├── approval_service.py    # Approval workflow
│   ├── transfer_service.py    # Ownership transfer
│   └── verification_service.py # Document verification
├── auth/                      # Authentication & authorization
│   ├── __init__.py
│   ├── permissions.py         # Role permissions
│   └── decorators.py          # RBAC decorators
├── routes/                    # Route handlers by feature
│   ├── __init__.py
│   ├── auth_routes.py         # Login/logout
│   ├── document_routes.py     # Document listing & registration
│   ├── approval_routes.py     # Review/approve/reject
│   ├── transfer_routes.py     # Ownership transfer
│   ├── verification_routes.py # Document verification
│   └── admin_routes.py        # Legal Authority operations
├── utils/                     # Utility functions
│   ├── __init__.py
│   └── crypto.py              # Hashing & crypto
└── [existing templates & static files]
```

## Key Improvements

### 1. **Clean Separation of Concerns**
Each module handles one responsibility:
- **Services**: Business logic (Document, Approval, Transfer, Verification, Blockchain, Audit)
- **Routes**: HTTP endpoints organized by feature
- **Auth**: Authentication and permission management
- **Models**: Database operations
- **Utils**: Reusable functions (crypto, hashing)

### 2. **Role-Based Access Control (RBAC)**
```python
# Easy permission checking
@permission_required("register_document")
def register_document():
    ...

# Or role-specific
@role_required("Legal Authority")
def delete_document():
    ...
```

### 3. **Service Classes**
Each service encapsulates related business logic:

- **DocumentService**: Register, retrieve, delete documents
- **ApprovalService**: Multi-stage approval workflow
- **TransferService**: Ownership transfer management
- **VerificationService**: Document authenticity verification
- **BlockchainService**: Block creation and payload management
- **AuditService**: Comprehensive audit trail

### 4. **Configuration Management**
Centralized configuration in `config.py`:
- Role definitions
- Approval workflow stages
- File upload settings
- Database paths

## Multi-Party Roles

```
1. Content Creator (Công ty sáng tạo nội dung)
   ├─ Register documents
   ├─ View documents
   └─ Transfer ownership

2. Censor (Đơn vị kiểm duyệt)
   ├─ Review documents
   ├─ Approve to next stage
   └─ Reject documents

3. Publisher (Nhà phát hành)
   ├─ Final approval & digital signature
   ├─ Approve documents
   └─ Transfer ownership

4. Customer (Khách hàng)
   ├─ View documents
   ├─ Verify authenticity
   └─ Receive ownership

5. Legal Authority (Cơ quan pháp lý)
   ├─ Full monitoring rights
   ├─ Override approvals
   ├─ Delete documents
   └─ Access audit logs
```

## Approval Workflow

```
Content Creator registers document
        ↓
Document → "Pending Censor Review"
        ↓
Censor reviews and approves
        ↓
Document → "Pending Publisher Approval"
        ↓
Publisher signs and approves
        ↓
Document → "Approved"
        ↓
Legal Authority can access and monitor
Legal Authority can delete at any stage
```

## Migration Guide

### Step 1: Install the New Structure
All new files are already created. The original `app.py` remains for reference.

### Step 2: Update Requirements (if needed)
```bash
pip install Flask==3.1.0 Werkzeug==3.1.3
```

### Step 3: Test the New App
```bash
# Option A: Keep both running for comparison
python app_new.py  # New refactored version (port 5000)

# Option B: Replace the old app
mv app.py app_old.py
mv app_new.py app.py
python app.py
```

### Step 4: Database
The new app uses the same database schema and is fully compatible with the old data.

## Benefits of New Architecture

### 1. **Maintainability**
- Each module has single responsibility
- Easy to find and modify specific functionality
- Clear code organization

### 2. **Testability**
- Services are easy to unit test
- Decorators for permission testing
- Isolated business logic

### 3. **Extensibility**
- Add new roles: Just update config.py
- Add new operations: Create new service + route
- Add new workflow stages: Extend ApprovalService

### 4. **Scalability**
- Services can be moved to separate microservices
- Database layer is abstracted
- Permission system is flexible

### 5. **Security**
- Role-based access control enforcement
- Permission-based decorators
- Centralized authentication
- Audit trail for all operations

## Example: Adding New Role

```python
# 1. Add to config.py
ROLES["New Role"] = {
    "label": "...",
    "icon": "...",
    "color": "..."
}

# 2. Define permissions in auth/permissions.py
ROLE_PERMISSIONS["New Role"] = {"permission1", "permission2"}

# 3. Create routes/use @role_required("New Role")
@role_required("New Role")
def my_operation():
    ...
```

## Example: Adding New Workflow Stage

```python
# 1. Update config.py
APPROVAL_STAGES = [
    ("Pending Stage 1", "Role1", "Previous"),
    ("Pending Stage 2", "Role2", "Role1"),  # Add new
    ("Approved", None, "Role2"),
]

# 2. Update ApprovalService.approve_document()
if user_role == "Role2" and current_status == "Pending Stage 2":
    new_status = "Approved"
    # ...
```

## API/Route Summary

### Authentication
- `POST /login` - User login
- `GET /logout` - User logout

### Documents
- `GET /` - List all documents
- `GET/POST /register` - Register document
- `GET /document/<id>` - Document details

### Approval
- `POST /document/<id>/review` - Review/approve/reject

### Transfer
- `GET/POST /transfer/<id>` - Transfer ownership

### Verification
- `GET/POST /verify` - Verify document authenticity

### Admin (Legal Authority)
- `POST /document/<id>/delete` - Delete document
- `POST /documents/delete-all` - Delete all documents

### File Download
- `GET /uploads/<filename>` - Download file

## Next Steps

1. **Test the new structure**: Compare outputs with old app
2. **Verify all existing data**: Ensure database compatibility
3. **Update any custom templates**: If you have modified them
4. **Deploy**: Replace app.py with app_new.py
5. **Monitor**: Check audit logs for all operations

## Files Comparison

| Functionality | Old Location | New Location |
|---|---|---|
| Configuration | Scattered in app.py | config.py |
| Database | Inline in app.py | models/database.py |
| Auth | Inline in app.py | routes/auth_routes.py + auth/permissions.py |
| Documents | Routes in app.py | routes/document_routes.py + services/document_service.py |
| Approval | Routes in app.py | routes/approval_routes.py + services/approval_service.py |
| Transfer | Routes in app.py | routes/transfer_routes.py + services/transfer_service.py |
| Verification | Routes in app.py | routes/verification_routes.py + services/verification_service.py |
| Blockchain | Inline functions | services/blockchain_service.py |
| Audit | Inline functions | services/audit_service.py |

## Troubleshooting

### Import Errors
Make sure all __init__.py files are created in directories.

### Database Errors
The new app uses the same database. Old data is compatible.

### Route Not Found
Check that blueprints are registered in app_new.py.

### Permission Denied
Verify user role and permissions in auth/permissions.py.

## Support

For questions or issues, refer to:
- `config.py` - System configuration
- `auth/permissions.py` - Role permissions
- `services/*.py` - Business logic
- `routes/*.py` - HTTP endpoints
