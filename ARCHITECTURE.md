# Architecture Documentation

## System Overview

This is a blockchain-based multi-party document verification system that manages financial documents through a secure approval workflow involving 5 different stakeholders.

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Flask App (app.py)                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Auth Routes │  │Document Routes│  │Admin Routes  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Approval Rts │  │Transfer Routes│  │ Verify Routes│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                │               │
│         └──────────────────┼──────────────────┘             │
│                            ▼                               │
│      ┌────────────────────────────────────┐               │
│      │       Service Layer (Business      │               │
│      │            Logic)                  │               │
│      ├────────────────────────────────────┤               │
│      │ • DocumentService                  │               │
│      │ • ApprovalService                  │               │
│      │ • TransferService                  │               │
│      │ • VerificationService              │               │
│      │ • BlockchainService                │               │
│      │ • AuditService                     │               │
│      └────────────────────────────────────┘               │
│                            │                               │
│      ┌────────────────────┴────────────────┐              │
│      ▼                                     ▼              │
│  ┌─────────────┐                 ┌────────────────┐     │
│  │   Auth      │                 │   Models       │     │
│  │  (RBAC)     │                 │  (Database)    │     │
│  └─────────────┘                 └────────────────┘     │
│      │                                     │              │
│      └─────────────────┬────────────────────┘              │
│                        ▼                                   │
│              ┌──────────────────┐                         │
│              │    SQLite DB     │                         │
│              │  - documents     │                         │
│              │  - blockchain    │                         │
│              │  - audit_log     │                         │
│              │  - transfers     │                         │
│              └──────────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow: Document Registration

```
User (Content Creator) uploads PDF
         ↓
DocumentService.register_document()
         ↓
├─ Save PDF to disk
├─ Calculate SHA256 hash
├─ Check for duplicates
└─ Insert into documents table
         ↓
BlockchainService.append_block()
         ↓
├─ Create payload (REGISTER|hash|creator|owner)
├─ Calculate tx_hash from previous block
└─ Insert into blockchain table
         ↓
AuditService.log_document_registration()
         ↓
└─ Create audit log entry
```

## Data Flow: Document Approval

```
Censor reviews document
         ↓
ApprovalService.approve_document(role="Censor", status="Pending Censor Review")
         ↓
├─ Verify permission (role + status combination)
├─ Determine next status ("Pending Publisher Approval")
└─ Update document approval_status
         ↓
AuditService.log_document_approval()
         ↓
└─ Create audit log entry
         ↓
Publisher reviews document
         ↓
ApprovalService.approve_document(role="Publisher", status="Pending Publisher Approval")
         ↓
├─ Update approval_status to "Approved"
├─ Set approved_by and approved_at
└─ Update document
         ↓
AuditService.log_document_approval()
         ↓
└─ Create audit log entry
```

## Data Flow: Ownership Transfer

```
Current Owner transfers ownership
         ↓
BlockchainService.create_transfer_payload()
         ↓
└─ Create TRANSFER|doc_id|hash|from|to
         ↓
BlockchainService.append_block()
         ↓
└─ Add block to blockchain
         ↓
TransferService.transfer_ownership()
         ↓
├─ Update documents.owner
└─ Insert ownership_transfer record
         ↓
AuditService.log_document_transfer()
         ↓
└─ Create audit log entry
```

## Permission Matrix

```
┌──────────────────┬─────────────┬────────┬──────────┬──────────┬─────────────┐
│ Operation        │ Content Cr. │ Censor │Publisher │ Customer │Legal Auth. │
├──────────────────┼─────────────┼────────┼──────────┼──────────┼─────────────┤
│ View Documents   │      ✓      │   ✓    │    ✓     │    ✓     │      ✓      │
│ Register Doc     │      ✓      │        │          │          │      ✓      │
│ Review Doc       │             │   ✓    │    ✓     │          │      ✓      │
│ Approve Doc      │             │   ✓    │    ✓     │          │      ✓      │
│ Reject Doc       │             │   ✓    │    ✓     │          │      ✓      │
│ Transfer Owner   │      ✓      │        │    ✓     │    ✓     │      ✓      │
│ Verify Doc       │      ✓      │   ✓    │    ✓     │    ✓     │      ✓      │
│ Delete Doc       │             │        │          │          │      ✓      │
│ View Audit Logs  │             │        │          │          │      ✓      │
└──────────────────┴─────────────┴────────┴──────────┴──────────┴─────────────┘
```

## Database Schema

### documents table
```
id (PK)
filename - Storage filename
file_hash - SHA256 of file
tx_hash - Transaction hash on blockchain
owner - Current owner
creator - Original creator
created_at - ISO timestamp
block_index - Blockchain block number
approval_status - (Pending Censor Review | Pending Publisher Approval | Approved | Rejected)
approved_by - User who approved
approved_at - Approval timestamp
rejected_by - User who rejected
rejected_at - Rejection timestamp
rejection_reason - Reason for rejection
```

### blockchain table
```
id (PK)
block_index - UNIQUE sequential block number
previous_hash - Hash of previous block (or "GENESIS")
payload - Transaction data (REGISTER|TRANSFER|...)
tx_hash - Current block hash
created_at - ISO timestamp
```

### ownership_transfers table
```
id (PK)
document_id (FK) - Reference to document
from_owner - Previous owner
to_owner - New owner
tx_hash - Blockchain transaction hash
transferred_at - ISO timestamp
block_index - Blockchain block number
```

### audit_log table
```
id (PK)
document_id (FK) - Document being audited (nullable)
action - Action type (Register, Approve, Reject, Transfer, Delete, Verify)
performed_by - User who performed action
role - Role of user
details - Action details (human readable)
created_at - ISO timestamp
tx_hash - Blockchain transaction hash (optional)
block_index - Blockchain block number (optional)
```

## Service Interactions

### DocumentService
- **register_document()** - Register new document with PDF upload
- **get_document()** - Retrieve document by ID
- **get_all_documents()** - List all documents
- **get_document_by_hash()** - Find document by SHA256 hash
- **delete_file()** - Delete uploaded PDF file

### ApprovalService
- **can_approve()** - Check if user can approve at current status
- **can_reject()** - Check if user can reject
- **approve_document()** - Advance document to next approval stage
- **reject_document()** - Reject document with reason
- **get_next_approver_role()** - Determine next role in workflow

### TransferService
- **can_transfer_ownership()** - Verify user role allows transfer
- **transfer_ownership()** - Update owner and create transfer record
- **get_transfer_history()** - Get all transfers for document

### VerificationService
- **verify_document()** - Upload file and verify against blockchain
- **verify_hash()** - Verify by hash value

### BlockchainService
- **append_block()** - Add block to chain
- **create_register_payload()** - Generate REGISTER transaction
- **create_transfer_payload()** - Generate TRANSFER transaction

### AuditService
- **log_action()** - Generic action logging
- **log_document_registration()** - Log registration
- **log_document_approval()** - Log approval/rejection
- **log_document_transfer()** - Log ownership transfer
- **log_document_deletion()** - Log deletion

## Authentication & Authorization

### Session Management
- User info stored in Flask session (user_name, user_role)
- get_current_user() retrieves from session
- Role-based access control via decorators

### Permission Decorators
```python
@login_required              # Requires authentication
@role_required("Publisher")  # Specific role
@permission_required("approve_document")  # Specific permission
```

### Permission System
- Defined in `auth/permissions.py`
- Maps roles to allowed operations
- Centralized, easy to update
- Can add fine-grained permissions

## Error Handling

- ValueError - Business logic errors (document exists, invalid input)
- PermissionError - Authorization failures
- 404 errors - Resource not found
- 500 errors - Server errors

All errors are caught and flashed to user.

## Scalability Considerations

### Current (Monolithic)
- All services use same database
- Services instantiated per request
- SQLite (suitable for testing/small deployments)

### Future (Microservices)
- Split services into separate services
- API Gateway for routing
- Distributed database (one per service)
- Message queue for events
- Dedicated audit service

### Optimization Points
- Cache frequently accessed documents
- Index file_hash for faster lookups
- Archive old audit logs
- Database connection pooling

## Extension Points

### Add New Role
1. Update `config.py` ROLES dict
2. Update `auth/permissions.py` with permissions
3. Update routes to check new role
4. Create templates if needed

### Add New Workflow Stage
1. Update `config.py` APPROVAL_STAGES
2. Update `ApprovalService.approve_document()`
3. Update templates to show new stage

### Add New Operation
1. Create service method in appropriate Service class
2. Create route handler with decorators
3. Create template if needed
4. Add audit logging

### Add Audit Logging
```python
audit_service.log_action(
    document_id=doc_id,
    action="MyAction",
    performed_by=user["name"],
    role=user["role"],
    details="Description"
)
```

## Configuration Management

All configuration in `config.py`:
- File upload paths and limits
- Database path
- Role definitions with colors/icons
- Approval workflow stages
- Allowed file extensions

To modify:
1. Edit `config.py`
2. No code changes needed in services
3. Changes take effect on app restart

## Testing Strategy

### Unit Tests (Services)
```python
# Test DocumentService
def test_register_document():
    service = DocumentService(db, upload_dir)
    doc_id, filename = service.register_document(pdf, "owner", "creator", 1, "hash")
    assert doc_id > 0

# Test ApprovalService
def test_censor_approval():
    service = ApprovalService(db)
    result = service.approve_document(1, "Censor", "user", "Pending Censor Review")
    assert result["new_status"] == "Pending Publisher Approval"
```

### Integration Tests (Routes + Services)
```python
def test_register_workflow():
    client = app.test_client()
    # Login as Content Creator
    # Upload document
    # Verify document appears
    # Switch role to Censor
    # Approve
    # Verify approval
```

### Permission Tests
```python
def test_permission_denied():
    # Try operation without permission
    # Should get flash error
    # Should redirect
```

## Deployment

### Development
```bash
export FLASK_DEBUG=True
python app.py
```

### Production
```bash
export FLASK_DEBUG=False
export FLASK_SECRET=$(openssl rand -hex 32)
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Monitoring & Observability

### Audit Trail
All operations logged to audit_log table:
- WHO performed the action (user + role)
- WHAT action was performed
- WHEN it happened (ISO timestamp)
- WHERE on blockchain (block_index, tx_hash)
- WHY (details field)

### Blockchain Immutability
- Each block includes previous_hash
- Transaction hash includes all data + timestamp
- Cannot modify past transactions without breaking chain

### System Health
Monitor:
- audit_log entries - Recent activity
- documents table size - Document volume
- blockchain table - Chain integrity
- File system - Uploaded documents

---

**Last Updated**: 2026-05-08  
**Version**: 2.0 (Refactored)  
**Status**: Production Ready
