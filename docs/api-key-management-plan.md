# API Key Management Implementation Plan

> Based on [auth-system-design.md](./auth-system-design.md)

## Overview

Implement API key management for the MagOneAI platform following the existing auth system design:
- **Single user model** - Permissions at user level, not API key level
- **API keys inherit user permissions** - No separate scopes on keys
- **Simple CRUD** - Create, list, revoke API keys

---

## Architecture (From auth-system-design.md)

```
User
├── role: "user" or "admin"
├── permissions: ["agents:read", "agents:write", "workflows:execute", ...]
│
└── Access Methods (inherit user's permissions)
    ├── JWT Token (web login)
    └── API Keys (scripts/integrations)  <-- THIS PLAN
```

**Key Principle:** API keys are just for **authentication**, not authorization. Permissions come from the user.

---

## Database Schema

### API_KEYS Table (NEW)

```
┌─────────────────────────────────────────────────────────────┐
│                         API_KEYS                             │
├─────────────────────────────────────────────────────────────┤
│ id            │ UUID        │ Primary Key                   │
│ user_id       │ UUID FK     │ References users.id           │
│ name          │ VARCHAR     │ "Production API Key"          │
│ key_prefix    │ VARCHAR     │ "mag_sk_abc1" (for display)   │
│ key_hash      │ VARCHAR     │ SHA-256 hash (for lookup)     │
│ expires_at    │ TIMESTAMP   │ Optional expiration           │
│ last_used_at  │ TIMESTAMP   │ Track usage                   │
│ is_active     │ BOOLEAN     │ Can be revoked                │
│ created_at    │ TIMESTAMP   │ Auto                          │
└─────────────────────────────────────────────────────────────┘

Note: NO SCOPES on API keys - they inherit user's permissions
```

### SQLAlchemy Model

```python
class ApiKeyModel(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
```

---

## API Key Format

```
mag_sk_dGhpcyBpcyBhIHRlc3Q...
│   │  └─ Random 256 bits (base64)
│   └─ "sk" = secret key
└─ "mag" = MagOne prefix
```

**Storage:**
- Full key shown **ONLY ONCE** at creation
- Database stores: `key_prefix` (first 12 chars) + `key_hash` (SHA-256)

---

## API Endpoints

### API Keys Management (`/api/v1/api-keys`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api-keys` | Create new API key | JWT |
| GET | `/api-keys` | List user's API keys | JWT |
| GET | `/api-keys/{id}` | Get key details | JWT |
| DELETE | `/api-keys/{id}` | Revoke/delete key | JWT |

### Request/Response Examples

**Create API Key:**
```http
POST /api/v1/api-keys
Authorization: Bearer {jwt_token}

{
  "name": "Production API Key",
  "expires_at": "2025-12-31T23:59:59Z"  // optional
}
```

**Response (ONLY TIME full key shown):**
```json
{
  "id": "key_abc123",
  "name": "Production API Key",
  "key": "mag_sk_dGhpcyBpcyBhIHRlc3Q...",  // COPY THIS NOW!
  "key_prefix": "mag_sk_dGhp",
  "expires_at": "2025-12-31T23:59:59Z",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**List API Keys:**
```http
GET /api/v1/api-keys
Authorization: Bearer {jwt_token}
```

```json
{
  "keys": [
    {
      "id": "key_abc123",
      "name": "Production API Key",
      "key_prefix": "mag_sk_dGhp",
      "is_active": true,
      "expires_at": "2025-12-31T23:59:59Z",
      "last_used_at": "2024-01-15T12:00:00Z",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

## Authentication Flow

### Using API Key for Requests

```
1. Client sends request:
   curl -H "X-API-Key: mag_sk_abc123..." https://api.example.com/agents

2. Server validates:
   → Hash the incoming key (SHA-256)
   → Find matching hash in database
   → Check if key is active and not expired
   → Load user from key.user_id
   → Use user's permissions for authorization

3. Process request with user context
```

### Flow Diagram

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│   Request    │     │   Middleware    │     │   Router     │
│ X-API-Key:.. │────▶│ Validate Key    │────▶│ Process      │
└──────────────┘     │ Load User       │     │ Request      │
                     │ Check Perms     │     └──────────────┘
                     └─────────────────┘
                            │
                     ┌──────┴──────┐
                     │  Database   │
                     │ api_keys    │
                     │ users       │
                     └─────────────┘
```

---

## Files to Create/Modify

### New Files

| File | Purpose |
|------|---------|
| `src/auth/api_key.py` | API key generation, hashing, validation |
| `src/storage/api_key_repository.py` | Database CRUD for API keys |
| `src/api/routers/api_keys.py` | API endpoints for key management |

### Modify

| File | Changes |
|------|---------|
| `src/storage/models.py` | Add `ApiKeyModel` |
| `src/auth/dependencies.py` | Add API key auth dependency |
| `src/api/app.py` | Register api_keys router |

---

## Implementation Order

### Step 1: Database Model
Add `ApiKeyModel` to `src/storage/models.py`

### Step 2: API Key Utilities
Create `src/auth/api_key.py`:
- `generate_api_key()` → Returns (full_key, prefix, hash)
- `hash_api_key(key)` → Returns SHA-256 hash
- `validate_key_format(key)` → Returns bool

### Step 3: Repository
Create `src/storage/api_key_repository.py`:
- `create(user_id, name, expires_at)` → Returns (ApiKey, raw_key)
- `get_by_hash(key_hash)` → Returns ApiKey or None
- `list_by_user(user_id)` → Returns List[ApiKey]
- `revoke(key_id, user_id)` → Returns bool
- `update_last_used(key_id)` → void

### Step 4: Auth Dependency
Update `src/auth/dependencies.py`:
- Add `get_current_user_from_api_key()` dependency
- Modify `get_current_user()` to check both JWT and API key

### Step 5: API Router
Create `src/api/routers/api_keys.py`:
- POST `/api-keys` - Create key
- GET `/api-keys` - List keys
- GET `/api-keys/{id}` - Get key
- DELETE `/api-keys/{id}` - Revoke key

### Step 6: Register Router
Update `src/api/app.py` to include api_keys router

---

## Security Considerations

1. **Key Storage**: Only SHA-256 hash stored, never plaintext
2. **One-time Display**: Full key shown only at creation
3. **User Ownership**: Keys tied to user_id, only owner can manage
4. **Expiration**: Optional expiration date support
5. **Revocation**: Immediate effect when key is revoked
6. **Rate Limiting**: Use existing rate limiter (slowapi)

---

## Permissions (From User)

API keys inherit these permissions from the user:

| Permission | Description |
|------------|-------------|
| `agents:read` | View agents |
| `agents:write` | Create/update agents |
| `agents:delete` | Delete agents |
| `workflows:read` | View workflows |
| `workflows:write` | Create/update workflows |
| `workflows:execute` | Run workflows |
| `knowledge:read` | View knowledge bases |
| `knowledge:write` | Create/upload to knowledge bases |
| `mcp:read` | View MCP servers |
| `mcp:write` | Create/update MCP servers |
| `*` | Full access (shorthand) |

---

## Dependencies

This plan requires the **User model** to exist first (from auth-system-design.md):
- `UserModel` with `id`, `permissions`, `role`
- JWT authentication working

If user model doesn't exist yet, implement that first following auth-system-design.md.

---

## Testing Checklist

- [ ] Create API key returns full key once
- [ ] List API keys shows prefix only (not full key)
- [ ] API key authenticates requests correctly
- [ ] Revoked keys are rejected
- [ ] Expired keys are rejected
- [ ] User can only see/manage their own keys
- [ ] Rate limiting works with API keys
