"""Comprehensive unit tests for AuthService.

Tests cover:
- User authentication (login, signup)
- Token management (create, refresh, revoke)
- User profile updates (email, password, display name)
- API key management (create, list, get, delete, validate)
- LLM credential management (create, list, get, update, delete)
- Admin operations (list users, update user, reset password, toggle status)
- Invite system (create, validate)
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.service import AuthService
from src.auth.schemas import TokenResponse
from src.storage.models import (
    APIKeyModel,
    DEFAULT_ORG_ID,
    LLMCredentialModel,
    RefreshTokenModel,
    UserInviteModel,
    UserModel,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_session():
    """Create a mock async database session."""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def auth_service(mock_session):
    """Create AuthService instance with mocked session."""
    return AuthService(mock_session)


@pytest.fixture
def sample_user():
    """Create a sample user model for testing."""
    return UserModel(
        id=str(uuid4()),
        email="test@example.com",
        password_hash="$2b$12$hashedpassword",
        display_name="Test User",
        org_id=DEFAULT_ORG_ID,
        is_active=True,
        is_superuser=False,
    )


@pytest.fixture
def inactive_user():
    """Create an inactive user for testing."""
    return UserModel(
        id=str(uuid4()),
        email="inactive@example.com",
        password_hash="$2b$12$hashedpassword",
        display_name="Inactive User",
        org_id=DEFAULT_ORG_ID,
        is_active=False,
        is_superuser=False,
    )


@pytest.fixture
def superuser():
    """Create a superuser for testing."""
    return UserModel(
        id=str(uuid4()),
        email="admin@example.com",
        password_hash="$2b$12$hashedpassword",
        display_name="Admin User",
        org_id=DEFAULT_ORG_ID,
        is_active=True,
        is_superuser=True,
    )


@pytest.fixture
def sample_invite():
    """Create a sample invite model for testing."""
    return UserInviteModel(
        id=str(uuid4()),
        email="invited@example.com",
        invite_code="test-invite-code-12345",
        invited_by=str(uuid4()),
        org_id=DEFAULT_ORG_ID,
        is_used=False,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )


@pytest.fixture
def sample_api_key():
    """Create a sample API key model for testing."""
    return APIKeyModel(
        id=str(uuid4()),
        user_id=str(uuid4()),
        name="Test API Key",
        key_prefix="magone_abc1",
        key_hash="sha256hashvalue",
        is_active=True,
        last_used_at=None,
    )


@pytest.fixture
def sample_llm_credential():
    """Create a sample LLM credential model for testing."""
    return LLMCredentialModel(
        id=str(uuid4()),
        user_id=str(uuid4()),
        provider="openai",
        display_name="My OpenAI Key",
        secret_ref="users/test-user/llm/openai/credential-id",
        api_key_preview="sk-proj-xxxxxxxxx",
        api_base=None,
        is_active=True,
        last_used_at=None,
    )


@pytest.fixture
def sample_refresh_token():
    """Create a sample refresh token model for testing."""
    return RefreshTokenModel(
        id=str(uuid4()),
        user_id=str(uuid4()),
        token_hash="sha256hashvalue",
        is_revoked=False,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )


# ============================================================================
# Helper to mock query results
# ============================================================================


def mock_scalar_result(value):
    """Helper to mock session.execute().scalar_one_or_none()."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = value
    return mock_result


def mock_scalars_result(values):
    """Helper to mock session.execute().scalars().all()."""
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = values
    mock_result.scalars.return_value = mock_scalars
    return mock_result


# ============================================================================
# Tests: get_user_by_email
# ============================================================================


class TestGetUserByEmail:
    """Tests for get_user_by_email method."""

    @pytest.mark.asyncio
    async def test_returns_user_when_found(self, auth_service, mock_session, sample_user):
        """Test that method returns user when email exists."""
        mock_session.execute.return_value = mock_scalar_result(sample_user)

        result = await auth_service.get_user_by_email("test@example.com")

        assert result == sample_user
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, auth_service, mock_session):
        """Test that method returns None when email does not exist."""
        mock_session.execute.return_value = mock_scalar_result(None)

        result = await auth_service.get_user_by_email("nonexistent@example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_normalizes_email_to_lowercase(self, auth_service, mock_session, sample_user):
        """Test that email is normalized to lowercase before query."""
        mock_session.execute.return_value = mock_scalar_result(sample_user)

        await auth_service.get_user_by_email("TEST@EXAMPLE.COM")

        # Email should be lowercased in the query
        mock_session.execute.assert_called_once()


# ============================================================================
# Tests: get_user_by_id
# ============================================================================


class TestGetUserById:
    """Tests for get_user_by_id method."""

    @pytest.mark.asyncio
    async def test_returns_user_when_found(self, auth_service, mock_session, sample_user):
        """Test that method returns user when ID exists."""
        mock_session.execute.return_value = mock_scalar_result(sample_user)

        result = await auth_service.get_user_by_id(sample_user.id)

        assert result == sample_user

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, auth_service, mock_session):
        """Test that method returns None when ID does not exist."""
        mock_session.execute.return_value = mock_scalar_result(None)

        result = await auth_service.get_user_by_id("nonexistent-id")

        assert result is None


# ============================================================================
# Tests: authenticate_user
# ============================================================================


class TestAuthenticateUser:
    """Tests for authenticate_user method."""

    @pytest.mark.asyncio
    async def test_returns_user_on_valid_credentials(self, auth_service, mock_session, sample_user):
        """Test successful authentication with valid credentials."""
        mock_session.execute.return_value = mock_scalar_result(sample_user)

        with patch("src.auth.service.verify_password", return_value=True):
            result = await auth_service.authenticate_user("test@example.com", "correct-password")

        assert result == sample_user

    @pytest.mark.asyncio
    async def test_returns_none_when_user_not_found(self, auth_service, mock_session):
        """Test returns None when user does not exist."""
        mock_session.execute.return_value = mock_scalar_result(None)

        result = await auth_service.authenticate_user("nonexistent@example.com", "password")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_wrong_password(self, auth_service, mock_session, sample_user):
        """Test returns None when password is incorrect."""
        mock_session.execute.return_value = mock_scalar_result(sample_user)

        with patch("src.auth.service.verify_password", return_value=False):
            result = await auth_service.authenticate_user("test@example.com", "wrong-password")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_inactive_user(self, auth_service, mock_session, inactive_user):
        """Test returns None when user is inactive."""
        mock_session.execute.return_value = mock_scalar_result(inactive_user)

        with patch("src.auth.service.verify_password", return_value=True):
            result = await auth_service.authenticate_user("inactive@example.com", "password")

        assert result is None


# ============================================================================
# Tests: create_tokens
# ============================================================================


class TestCreateTokens:
    """Tests for create_tokens method."""

    @pytest.mark.asyncio
    async def test_returns_token_response(self, auth_service, mock_session, sample_user):
        """Test that method returns proper TokenResponse."""
        with patch("src.auth.service.create_access_token", return_value="access-token"):
            with patch(
                "src.auth.service.create_refresh_token",
                return_value=("raw-refresh", "hash-refresh", datetime.now(timezone.utc) + timedelta(days=7)),
            ):
                result = await auth_service.create_tokens(sample_user)

        assert isinstance(result, TokenResponse)
        assert result.access_token == "access-token"
        assert result.refresh_token == "raw-refresh"
        assert result.token_type == "bearer"
        assert result.expires_in > 0

    @pytest.mark.asyncio
    async def test_stores_refresh_token_in_database(self, auth_service, mock_session, sample_user):
        """Test that refresh token is stored in database."""
        with patch("src.auth.service.create_access_token", return_value="access-token"):
            with patch(
                "src.auth.service.create_refresh_token",
                return_value=("raw-refresh", "hash-refresh", datetime.now(timezone.utc) + timedelta(days=7)),
            ):
                await auth_service.create_tokens(sample_user)

        # Verify session.add was called with RefreshTokenModel
        mock_session.add.assert_called()
        added_obj = mock_session.add.call_args[0][0]
        assert isinstance(added_obj, RefreshTokenModel)
        assert added_obj.user_id == sample_user.id
        assert added_obj.token_hash == "hash-refresh"

    @pytest.mark.asyncio
    async def test_updates_last_login_timestamp(self, auth_service, mock_session, sample_user):
        """Test that user's last_login_at is updated."""
        original_login = sample_user.last_login_at

        with patch("src.auth.service.create_access_token", return_value="access-token"):
            with patch(
                "src.auth.service.create_refresh_token",
                return_value=("raw-refresh", "hash-refresh", datetime.now(timezone.utc) + timedelta(days=7)),
            ):
                await auth_service.create_tokens(sample_user)

        assert sample_user.last_login_at is not None
        assert sample_user.last_login_at != original_login


# ============================================================================
# Tests: refresh_tokens
# ============================================================================


class TestRefreshTokens:
    """Tests for refresh_tokens method."""

    @pytest.mark.asyncio
    async def test_returns_new_tokens_on_valid_refresh(
        self, auth_service, mock_session, sample_user, sample_refresh_token
    ):
        """Test successful token refresh."""
        sample_refresh_token.user_id = sample_user.id

        # First call returns the refresh token, second returns the user
        mock_session.execute.side_effect = [
            mock_scalar_result(sample_refresh_token),
            mock_scalar_result(sample_user),
        ]

        with patch("src.auth.service.hash_token", return_value="hash-value"):
            with patch("src.auth.service.create_access_token", return_value="new-access-token"):
                with patch(
                    "src.auth.service.create_refresh_token",
                    return_value=("new-refresh", "new-hash", datetime.now(timezone.utc) + timedelta(days=7)),
                ):
                    result = await auth_service.refresh_tokens("old-refresh-token")

        assert result is not None
        assert result.access_token == "new-access-token"
        assert result.refresh_token == "new-refresh"

    @pytest.mark.asyncio
    async def test_revokes_old_refresh_token(self, auth_service, mock_session, sample_user, sample_refresh_token):
        """Test that old refresh token is revoked during rotation."""
        sample_refresh_token.user_id = sample_user.id

        mock_session.execute.side_effect = [
            mock_scalar_result(sample_refresh_token),
            mock_scalar_result(sample_user),
        ]

        with patch("src.auth.service.hash_token", return_value="hash-value"):
            with patch("src.auth.service.create_access_token", return_value="new-access-token"):
                with patch(
                    "src.auth.service.create_refresh_token",
                    return_value=("new-refresh", "new-hash", datetime.now(timezone.utc) + timedelta(days=7)),
                ):
                    await auth_service.refresh_tokens("old-refresh-token")

        assert sample_refresh_token.is_revoked is True

    @pytest.mark.asyncio
    async def test_returns_none_for_invalid_token(self, auth_service, mock_session):
        """Test returns None when refresh token is not found."""
        mock_session.execute.return_value = mock_scalar_result(None)

        with patch("src.auth.service.hash_token", return_value="hash-value"):
            result = await auth_service.refresh_tokens("invalid-token")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_inactive_user(
        self, auth_service, mock_session, inactive_user, sample_refresh_token
    ):
        """Test returns None when user is inactive."""
        sample_refresh_token.user_id = inactive_user.id

        mock_session.execute.side_effect = [
            mock_scalar_result(sample_refresh_token),
            mock_scalar_result(inactive_user),
        ]

        with patch("src.auth.service.hash_token", return_value="hash-value"):
            result = await auth_service.refresh_tokens("refresh-token")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_user_not_found(self, auth_service, mock_session, sample_refresh_token):
        """Test returns None when user no longer exists."""
        mock_session.execute.side_effect = [
            mock_scalar_result(sample_refresh_token),
            mock_scalar_result(None),
        ]

        with patch("src.auth.service.hash_token", return_value="hash-value"):
            result = await auth_service.refresh_tokens("refresh-token")

        assert result is None


# ============================================================================
# Tests: revoke_refresh_token
# ============================================================================


class TestRevokeRefreshToken:
    """Tests for revoke_refresh_token method."""

    @pytest.mark.asyncio
    async def test_revokes_valid_token(self, auth_service, mock_session, sample_refresh_token):
        """Test successfully revoking a refresh token."""
        mock_session.execute.return_value = mock_scalar_result(sample_refresh_token)

        with patch("src.auth.service.hash_token", return_value="hash-value"):
            result = await auth_service.revoke_refresh_token("refresh-token")

        assert result is True
        assert sample_refresh_token.is_revoked is True

    @pytest.mark.asyncio
    async def test_returns_false_for_nonexistent_token(self, auth_service, mock_session):
        """Test returns False when token not found."""
        mock_session.execute.return_value = mock_scalar_result(None)

        with patch("src.auth.service.hash_token", return_value="hash-value"):
            result = await auth_service.revoke_refresh_token("nonexistent-token")

        assert result is False


# ============================================================================
# Tests: validate_invite
# ============================================================================


class TestValidateInvite:
    """Tests for validate_invite method."""

    @pytest.mark.asyncio
    async def test_returns_invite_when_valid(self, auth_service, mock_session, sample_invite):
        """Test returns invite when code is valid."""
        mock_session.execute.return_value = mock_scalar_result(sample_invite)

        result = await auth_service.validate_invite("test-invite-code-12345")

        assert result == sample_invite

    @pytest.mark.asyncio
    async def test_returns_none_for_invalid_code(self, auth_service, mock_session):
        """Test returns None for invalid invite code."""
        mock_session.execute.return_value = mock_scalar_result(None)

        result = await auth_service.validate_invite("invalid-code")

        assert result is None


# ============================================================================
# Tests: create_user
# ============================================================================


class TestCreateUser:
    """Tests for create_user method."""

    @pytest.mark.asyncio
    async def test_creates_user_successfully(self, auth_service, mock_session):
        """Test user creation with valid data."""
        with patch("src.auth.service.hash_password", return_value="hashed-password"):
            result = await auth_service.create_user(
                email="new@example.com",
                password="SecurePass123!",
                display_name="New User",
            )

        assert isinstance(result, UserModel)
        assert result.email == "new@example.com"
        assert result.display_name == "New User"
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_normalizes_email_to_lowercase(self, auth_service, mock_session):
        """Test that email is normalized to lowercase."""
        with patch("src.auth.service.hash_password", return_value="hashed-password"):
            result = await auth_service.create_user(
                email="NEW@EXAMPLE.COM",
                password="SecurePass123!",
                display_name=None,
            )

        assert result.email == "new@example.com"

    @pytest.mark.asyncio
    async def test_uses_default_org_id(self, auth_service, mock_session):
        """Test that default org_id is used when not specified."""
        with patch("src.auth.service.hash_password", return_value="hashed-password"):
            result = await auth_service.create_user(
                email="new@example.com",
                password="SecurePass123!",
                display_name=None,
            )

        assert result.org_id == DEFAULT_ORG_ID

    @pytest.mark.asyncio
    async def test_uses_custom_org_id(self, auth_service, mock_session):
        """Test that custom org_id can be specified."""
        custom_org = str(uuid4())

        with patch("src.auth.service.hash_password", return_value="hashed-password"):
            result = await auth_service.create_user(
                email="new@example.com",
                password="SecurePass123!",
                display_name=None,
                org_id=custom_org,
            )

        assert result.org_id == custom_org


# ============================================================================
# Tests: create_user_with_invite
# ============================================================================


class TestCreateUserWithInvite:
    """Tests for create_user_with_invite method."""

    @pytest.mark.asyncio
    async def test_creates_user_from_invite(self, auth_service, mock_session, sample_invite):
        """Test user creation from invite."""
        with patch("src.auth.service.hash_password", return_value="hashed-password"):
            result = await auth_service.create_user_with_invite(
                email="invited@example.com",
                password="SecurePass123!",
                display_name="Invited User",
                invite=sample_invite,
            )

        assert isinstance(result, UserModel)
        assert result.org_id == sample_invite.org_id
        assert result.invited_by == sample_invite.invited_by

    @pytest.mark.asyncio
    async def test_marks_invite_as_used(self, auth_service, mock_session, sample_invite):
        """Test that invite is marked as used after user creation."""
        assert sample_invite.is_used is False

        with patch("src.auth.service.hash_password", return_value="hashed-password"):
            result = await auth_service.create_user_with_invite(
                email="invited@example.com",
                password="SecurePass123!",
                display_name=None,
                invite=sample_invite,
            )

        assert sample_invite.is_used is True
        assert sample_invite.used_by == result.id


# ============================================================================
# Tests: create_invite
# ============================================================================


class TestCreateInvite:
    """Tests for create_invite method."""

    @pytest.mark.asyncio
    async def test_creates_new_invite(self, auth_service, mock_session):
        """Test creating a new invite when none exists."""
        # No existing user, no existing invite
        mock_session.execute.side_effect = [
            mock_scalar_result(None),  # get_user_by_email
            mock_scalar_result(None),  # existing invite check
        ]

        result = await auth_service.create_invite(
            email="newinvite@example.com",
            invited_by=str(uuid4()),
        )

        assert isinstance(result, UserInviteModel)
        assert result.email == "newinvite@example.com"
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_when_user_exists(self, auth_service, mock_session, sample_user):
        """Test raises ValueError when user already exists."""
        mock_session.execute.return_value = mock_scalar_result(sample_user)

        with pytest.raises(ValueError, match="User with this email already exists"):
            await auth_service.create_invite(
                email="test@example.com",
                invited_by=str(uuid4()),
            )

    @pytest.mark.asyncio
    async def test_returns_existing_valid_invite(self, auth_service, mock_session, sample_invite):
        """Test returns existing invite if still valid."""
        mock_session.execute.side_effect = [
            mock_scalar_result(None),  # get_user_by_email
            mock_scalar_result(sample_invite),  # existing invite
        ]

        result = await auth_service.create_invite(
            email="invited@example.com",
            invited_by=str(uuid4()),
        )

        assert result == sample_invite
        # Should not add new invite
        mock_session.add.assert_not_called()


# ============================================================================
# Tests: create_superuser
# ============================================================================


class TestCreateSuperuser:
    """Tests for create_superuser method."""

    @pytest.mark.asyncio
    async def test_creates_superuser(self, auth_service, mock_session):
        """Test creating a superuser."""
        with patch("src.auth.service.hash_password", return_value="hashed-password"):
            result = await auth_service.create_superuser(
                email="admin@example.com",
                password="AdminPass123!",
            )

        assert isinstance(result, UserModel)
        assert result.is_superuser is True
        assert result.display_name == "Super Admin"
        mock_session.add.assert_called_once()


# ============================================================================
# Tests: update_email
# ============================================================================


class TestUpdateEmail:
    """Tests for update_email method."""

    @pytest.mark.asyncio
    async def test_updates_email_successfully(self, auth_service, mock_session, sample_user):
        """Test successful email update."""
        mock_session.execute.side_effect = [
            mock_scalar_result(None),  # No existing user with new email
            mock_scalar_result(sample_user),  # Get user by ID
        ]

        result = await auth_service.update_email(sample_user.id, "newemail@example.com")

        assert result.email == "newemail@example.com"
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_when_email_already_used(self, auth_service, mock_session, sample_user):
        """Test raises error when email is already in use by another user."""
        other_user = UserModel(
            id=str(uuid4()),
            email="other@example.com",
            password_hash="hash",
            org_id=DEFAULT_ORG_ID,
        )
        mock_session.execute.return_value = mock_scalar_result(other_user)

        with pytest.raises(ValueError, match="Email address is already in use"):
            await auth_service.update_email(sample_user.id, "other@example.com")

    @pytest.mark.asyncio
    async def test_raises_when_user_not_found(self, auth_service, mock_session):
        """Test raises error when user not found."""
        mock_session.execute.side_effect = [
            mock_scalar_result(None),  # No existing user with new email
            mock_scalar_result(None),  # User not found
        ]

        with pytest.raises(ValueError, match="User not found"):
            await auth_service.update_email("nonexistent-id", "new@example.com")


# ============================================================================
# Tests: update_password
# ============================================================================


class TestUpdatePassword:
    """Tests for update_password method."""

    @pytest.mark.asyncio
    async def test_updates_password_successfully(self, auth_service, mock_session, sample_user):
        """Test successful password update."""
        mock_session.execute.return_value = mock_scalar_result(sample_user)

        with patch("src.auth.service.verify_password", return_value=True):
            with patch("src.auth.service.hash_password", return_value="new-hash"):
                result = await auth_service.update_password(
                    sample_user.id,
                    "current-password",
                    "new-password",
                )

        assert result is True
        assert sample_user.password_hash == "new-hash"
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_when_current_password_wrong(self, auth_service, mock_session, sample_user):
        """Test raises error when current password is incorrect."""
        mock_session.execute.return_value = mock_scalar_result(sample_user)

        with patch("src.auth.service.verify_password", return_value=False):
            with pytest.raises(ValueError, match="Current password is incorrect"):
                await auth_service.update_password(
                    sample_user.id,
                    "wrong-password",
                    "new-password",
                )

    @pytest.mark.asyncio
    async def test_raises_when_user_not_found(self, auth_service, mock_session):
        """Test raises error when user not found."""
        mock_session.execute.return_value = mock_scalar_result(None)

        with pytest.raises(ValueError, match="User not found"):
            await auth_service.update_password(
                "nonexistent-id",
                "current",
                "new",
            )


# ============================================================================
# Tests: update_display_name
# ============================================================================


class TestUpdateDisplayName:
    """Tests for update_display_name method."""

    @pytest.mark.asyncio
    async def test_updates_display_name(self, auth_service, mock_session, sample_user):
        """Test successful display name update."""
        mock_session.execute.return_value = mock_scalar_result(sample_user)

        result = await auth_service.update_display_name(sample_user.id, "New Name")

        assert result.display_name == "New Name"
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_clears_display_name(self, auth_service, mock_session, sample_user):
        """Test clearing display name to None."""
        mock_session.execute.return_value = mock_scalar_result(sample_user)

        result = await auth_service.update_display_name(sample_user.id, None)

        assert result.display_name is None

    @pytest.mark.asyncio
    async def test_raises_when_user_not_found(self, auth_service, mock_session):
        """Test raises error when user not found."""
        mock_session.execute.return_value = mock_scalar_result(None)

        with pytest.raises(ValueError, match="User not found"):
            await auth_service.update_display_name("nonexistent-id", "Name")


# ============================================================================
# Tests: create_api_key
# ============================================================================


class TestCreateApiKey:
    """Tests for create_api_key method."""

    @pytest.mark.asyncio
    async def test_creates_api_key_successfully(self, auth_service, mock_session):
        """Test successful API key creation."""
        user_id = str(uuid4())

        with patch("src.auth.service.hash_token", return_value="hashed-key"):
            api_key, raw_key = await auth_service.create_api_key(user_id, "My API Key")

        assert isinstance(api_key, APIKeyModel)
        assert api_key.user_id == user_id
        assert api_key.name == "My API Key"
        assert raw_key.startswith("magone_")
        assert api_key.key_prefix == raw_key[:12]
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_raw_key_only_once(self, auth_service, mock_session):
        """Test that raw key is returned only at creation time."""
        with patch("src.auth.service.hash_token", return_value="hashed-key"):
            _, raw_key = await auth_service.create_api_key(str(uuid4()), "Test Key")

        # Raw key should be a substantial length
        assert len(raw_key) > 20
        # Should contain the magone prefix
        assert raw_key.startswith("magone_")


# ============================================================================
# Tests: list_api_keys
# ============================================================================


class TestListApiKeys:
    """Tests for list_api_keys method."""

    @pytest.mark.asyncio
    async def test_returns_user_api_keys(self, auth_service, mock_session, sample_api_key):
        """Test listing API keys for a user."""
        user_id = sample_api_key.user_id
        mock_session.execute.return_value = mock_scalars_result([sample_api_key])

        result = await auth_service.list_api_keys(user_id)

        assert len(result) == 1
        assert result[0] == sample_api_key

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_keys(self, auth_service, mock_session):
        """Test returns empty list when user has no API keys."""
        mock_session.execute.return_value = mock_scalars_result([])

        result = await auth_service.list_api_keys(str(uuid4()))

        assert result == []


# ============================================================================
# Tests: get_api_key
# ============================================================================


class TestGetApiKey:
    """Tests for get_api_key method."""

    @pytest.mark.asyncio
    async def test_returns_api_key_when_found(self, auth_service, mock_session, sample_api_key):
        """Test returns API key when found."""
        mock_session.execute.return_value = mock_scalar_result(sample_api_key)

        result = await auth_service.get_api_key(sample_api_key.id, sample_api_key.user_id)

        assert result == sample_api_key

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, auth_service, mock_session):
        """Test returns None when API key not found."""
        mock_session.execute.return_value = mock_scalar_result(None)

        result = await auth_service.get_api_key("nonexistent-id", str(uuid4()))

        assert result is None


# ============================================================================
# Tests: delete_api_key
# ============================================================================


class TestDeleteApiKey:
    """Tests for delete_api_key method."""

    @pytest.mark.asyncio
    async def test_deletes_api_key_successfully(self, auth_service, mock_session, sample_api_key):
        """Test successful API key deletion."""
        mock_session.execute.return_value = mock_scalar_result(sample_api_key)

        result = await auth_service.delete_api_key(sample_api_key.id, sample_api_key.user_id)

        assert result is True
        mock_session.delete.assert_called_once_with(sample_api_key)
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_false_when_not_found(self, auth_service, mock_session):
        """Test returns False when API key not found."""
        mock_session.execute.return_value = mock_scalar_result(None)

        result = await auth_service.delete_api_key("nonexistent-id", str(uuid4()))

        assert result is False
        mock_session.delete.assert_not_called()


# ============================================================================
# Tests: validate_api_key
# ============================================================================


class TestValidateApiKey:
    """Tests for validate_api_key method."""

    @pytest.mark.asyncio
    async def test_returns_user_for_valid_key(self, auth_service, mock_session, sample_api_key, sample_user):
        """Test returns user for valid API key."""
        sample_api_key.user_id = sample_user.id

        mock_session.execute.side_effect = [
            mock_scalar_result(sample_api_key),
            mock_scalar_result(sample_user),
        ]

        with patch("src.auth.service.hash_token", return_value="hash-value"):
            result = await auth_service.validate_api_key("magone_abc123xyz")

        assert result == sample_user
        assert sample_api_key.last_used_at is not None

    @pytest.mark.asyncio
    async def test_returns_none_for_invalid_key(self, auth_service, mock_session):
        """Test returns None for invalid API key."""
        mock_session.execute.return_value = mock_scalar_result(None)

        with patch("src.auth.service.hash_token", return_value="hash-value"):
            result = await auth_service.validate_api_key("invalid-key")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_inactive_user(self, auth_service, mock_session, sample_api_key, inactive_user):
        """Test returns None when user is inactive."""
        sample_api_key.user_id = inactive_user.id

        mock_session.execute.side_effect = [
            mock_scalar_result(sample_api_key),
            mock_scalar_result(inactive_user),
        ]

        with patch("src.auth.service.hash_token", return_value="hash-value"):
            result = await auth_service.validate_api_key("magone_abc123xyz")

        assert result is None


# ============================================================================
# Tests: _create_api_key_preview
# ============================================================================


class TestCreateApiKeyPreview:
    """Tests for _create_api_key_preview helper method."""

    def test_normal_length_key(self, auth_service):
        """Test preview for normal length API key."""
        preview = auth_service._create_api_key_preview("sk-proj-1234567890abcdef")

        assert preview.startswith("sk-proj-")
        assert len(preview) == 32  # 8 chars + 24 dots

    def test_short_key(self, auth_service):
        """Test preview for short API key."""
        preview = auth_service._create_api_key_preview("abc123")

        assert len(preview) == 6
        assert preview.startswith("abc1")

    def test_exact_eight_char_key(self, auth_service):
        """Test preview for exactly 8 character key."""
        preview = auth_service._create_api_key_preview("12345678")

        assert preview.startswith("1234")


# ============================================================================
# Tests: create_llm_credential
# ============================================================================


class TestCreateLlmCredential:
    """Tests for create_llm_credential method."""

    @pytest.mark.asyncio
    async def test_creates_credential_successfully(self, auth_service, mock_session):
        """Test successful LLM credential creation."""
        user_id = str(uuid4())
        mock_secrets_manager = AsyncMock()

        with patch("src.auth.service.get_secrets_manager", return_value=mock_secrets_manager):
            result = await auth_service.create_llm_credential(
                user_id=user_id,
                provider="openai",
                display_name="My OpenAI Key",
                api_key="sk-proj-1234567890",
            )

        assert isinstance(result, LLMCredentialModel)
        assert result.user_id == user_id
        assert result.provider == "openai"
        assert result.display_name == "My OpenAI Key"
        assert result.api_key_preview.startswith("sk-proj-")
        mock_secrets_manager.store.assert_called_once()
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_normalizes_provider_to_lowercase(self, auth_service, mock_session):
        """Test that provider is normalized to lowercase."""
        mock_secrets_manager = AsyncMock()

        with patch("src.auth.service.get_secrets_manager", return_value=mock_secrets_manager):
            result = await auth_service.create_llm_credential(
                user_id=str(uuid4()),
                provider="OPENAI",
                display_name="Test",
                api_key="sk-test",
            )

        assert result.provider == "openai"

    @pytest.mark.asyncio
    async def test_stores_api_key_in_vault(self, auth_service, mock_session):
        """Test that API key is stored in vault, not database."""
        user_id = str(uuid4())
        mock_secrets_manager = AsyncMock()

        with patch("src.auth.service.get_secrets_manager", return_value=mock_secrets_manager):
            result = await auth_service.create_llm_credential(
                user_id=user_id,
                provider="anthropic",
                display_name="Test",
                api_key="sk-ant-1234567890",
            )

        # Verify vault was called with the API key
        mock_secrets_manager.store.assert_called_once()
        call_kwargs = mock_secrets_manager.store.call_args
        assert call_kwargs[1]["value"]["api_key"] == "sk-ant-1234567890"

        # Verify secret_ref is set
        assert result.secret_ref is not None
        assert "anthropic" in result.secret_ref


# ============================================================================
# Tests: list_llm_credentials
# ============================================================================


class TestListLlmCredentials:
    """Tests for list_llm_credentials method."""

    @pytest.mark.asyncio
    async def test_returns_user_credentials(self, auth_service, mock_session, sample_llm_credential):
        """Test listing LLM credentials for a user."""
        mock_session.execute.return_value = mock_scalars_result([sample_llm_credential])

        result = await auth_service.list_llm_credentials(sample_llm_credential.user_id)

        assert len(result) == 1
        assert result[0] == sample_llm_credential

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_credentials(self, auth_service, mock_session):
        """Test returns empty list when user has no credentials."""
        mock_session.execute.return_value = mock_scalars_result([])

        result = await auth_service.list_llm_credentials(str(uuid4()))

        assert result == []


# ============================================================================
# Tests: get_llm_credential
# ============================================================================


class TestGetLlmCredential:
    """Tests for get_llm_credential method."""

    @pytest.mark.asyncio
    async def test_returns_credential_when_found(self, auth_service, mock_session, sample_llm_credential):
        """Test returns credential when found."""
        mock_session.execute.return_value = mock_scalar_result(sample_llm_credential)

        result = await auth_service.get_llm_credential(
            sample_llm_credential.id,
            sample_llm_credential.user_id,
        )

        assert result == sample_llm_credential

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, auth_service, mock_session):
        """Test returns None when credential not found."""
        mock_session.execute.return_value = mock_scalar_result(None)

        result = await auth_service.get_llm_credential("nonexistent-id", str(uuid4()))

        assert result is None


# ============================================================================
# Tests: get_llm_credential_by_provider
# ============================================================================


class TestGetLlmCredentialByProvider:
    """Tests for get_llm_credential_by_provider method."""

    @pytest.mark.asyncio
    async def test_returns_credential_for_provider(self, auth_service, mock_session, sample_llm_credential):
        """Test returns credential for specific provider."""
        mock_session.execute.return_value = mock_scalar_result(sample_llm_credential)

        result = await auth_service.get_llm_credential_by_provider(
            sample_llm_credential.user_id,
            "openai",
        )

        assert result == sample_llm_credential

    @pytest.mark.asyncio
    async def test_normalizes_provider_to_lowercase(self, auth_service, mock_session, sample_llm_credential):
        """Test that provider is normalized to lowercase in query."""
        mock_session.execute.return_value = mock_scalar_result(sample_llm_credential)

        await auth_service.get_llm_credential_by_provider(
            sample_llm_credential.user_id,
            "OPENAI",
        )

        mock_session.execute.assert_called_once()


# ============================================================================
# Tests: update_llm_credential
# ============================================================================


class TestUpdateLlmCredential:
    """Tests for update_llm_credential method."""

    @pytest.mark.asyncio
    async def test_updates_display_name(self, auth_service, mock_session, sample_llm_credential):
        """Test updating display name."""
        mock_session.execute.return_value = mock_scalar_result(sample_llm_credential)

        result = await auth_service.update_llm_credential(
            sample_llm_credential.id,
            sample_llm_credential.user_id,
            display_name="New Name",
        )

        assert result.display_name == "New Name"
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_api_key(self, auth_service, mock_session, sample_llm_credential):
        """Test updating API key."""
        mock_session.execute.return_value = mock_scalar_result(sample_llm_credential)
        mock_secrets_manager = AsyncMock()

        with patch("src.auth.service.get_secrets_manager", return_value=mock_secrets_manager):
            result = await auth_service.update_llm_credential(
                sample_llm_credential.id,
                sample_llm_credential.user_id,
                api_key="new-api-key",
            )

        mock_secrets_manager.store.assert_called_once()
        assert result.api_key_preview.startswith("new-api-")

    @pytest.mark.asyncio
    async def test_updates_api_base(self, auth_service, mock_session, sample_llm_credential):
        """Test updating API base URL."""
        mock_session.execute.return_value = mock_scalar_result(sample_llm_credential)

        result = await auth_service.update_llm_credential(
            sample_llm_credential.id,
            sample_llm_credential.user_id,
            api_base="https://custom.api.com",
        )

        assert result.api_base == "https://custom.api.com"

    @pytest.mark.asyncio
    async def test_updates_is_active(self, auth_service, mock_session, sample_llm_credential):
        """Test updating active status."""
        mock_session.execute.return_value = mock_scalar_result(sample_llm_credential)

        result = await auth_service.update_llm_credential(
            sample_llm_credential.id,
            sample_llm_credential.user_id,
            is_active=False,
        )

        assert result.is_active is False

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, auth_service, mock_session):
        """Test returns None when credential not found."""
        mock_session.execute.return_value = mock_scalar_result(None)

        result = await auth_service.update_llm_credential(
            "nonexistent-id",
            str(uuid4()),
            display_name="New Name",
        )

        assert result is None


# ============================================================================
# Tests: delete_llm_credential
# ============================================================================


class TestDeleteLlmCredential:
    """Tests for delete_llm_credential method."""

    @pytest.mark.asyncio
    async def test_deletes_credential_and_vault_entry(self, auth_service, mock_session, sample_llm_credential):
        """Test deleting credential and vault entry."""
        mock_session.execute.return_value = mock_scalar_result(sample_llm_credential)
        mock_secrets_manager = AsyncMock()

        with patch("src.auth.service.get_secrets_manager", return_value=mock_secrets_manager):
            result = await auth_service.delete_llm_credential(
                sample_llm_credential.id,
                sample_llm_credential.user_id,
            )

        assert result is True
        mock_secrets_manager.delete.assert_called_once_with(sample_llm_credential.secret_ref)
        mock_session.delete.assert_called_once_with(sample_llm_credential)

    @pytest.mark.asyncio
    async def test_handles_missing_vault_entry(self, auth_service, mock_session, sample_llm_credential):
        """Test handles case when vault entry is already deleted."""
        mock_session.execute.return_value = mock_scalar_result(sample_llm_credential)
        mock_secrets_manager = AsyncMock()
        mock_secrets_manager.delete.side_effect = KeyError("Not found")

        with patch("src.auth.service.get_secrets_manager", return_value=mock_secrets_manager):
            result = await auth_service.delete_llm_credential(
                sample_llm_credential.id,
                sample_llm_credential.user_id,
            )

        # Should still succeed even if vault entry is missing
        assert result is True
        mock_session.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_false_when_not_found(self, auth_service, mock_session):
        """Test returns False when credential not found."""
        mock_session.execute.return_value = mock_scalar_result(None)

        result = await auth_service.delete_llm_credential("nonexistent-id", str(uuid4()))

        assert result is False


# ============================================================================
# Tests: get_llm_api_key
# ============================================================================


class TestGetLlmApiKey:
    """Tests for get_llm_api_key method."""

    @pytest.mark.asyncio
    async def test_retrieves_api_key_from_vault(self, auth_service, mock_session, sample_llm_credential):
        """Test retrieving API key from vault."""
        mock_session.execute.return_value = mock_scalar_result(sample_llm_credential)
        mock_secrets_manager = AsyncMock()
        mock_secrets_manager.retrieve.return_value = {"api_key": "sk-secret-key"}

        with patch("src.auth.service.get_secrets_manager", return_value=mock_secrets_manager):
            result = await auth_service.get_llm_api_key(
                sample_llm_credential.id,
                sample_llm_credential.user_id,
            )

        assert result == "sk-secret-key"
        assert sample_llm_credential.last_used_at is not None

    @pytest.mark.asyncio
    async def test_returns_none_when_credential_not_found(self, auth_service, mock_session):
        """Test returns None when credential not found."""
        mock_session.execute.return_value = mock_scalar_result(None)

        result = await auth_service.get_llm_api_key("nonexistent-id", str(uuid4()))

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_vault_key_error(self, auth_service, mock_session, sample_llm_credential):
        """Test returns None when vault raises KeyError."""
        mock_session.execute.return_value = mock_scalar_result(sample_llm_credential)
        mock_secrets_manager = AsyncMock()
        mock_secrets_manager.retrieve.side_effect = KeyError("Not found")

        with patch("src.auth.service.get_secrets_manager", return_value=mock_secrets_manager):
            result = await auth_service.get_llm_api_key(
                sample_llm_credential.id,
                sample_llm_credential.user_id,
            )

        assert result is None


# ============================================================================
# Tests: get_llm_api_key_by_provider
# ============================================================================


class TestGetLlmApiKeyByProvider:
    """Tests for get_llm_api_key_by_provider method."""

    @pytest.mark.asyncio
    async def test_retrieves_api_key_by_provider(self, auth_service, mock_session, sample_llm_credential):
        """Test retrieving API key by provider."""
        mock_session.execute.return_value = mock_scalar_result(sample_llm_credential)
        mock_secrets_manager = AsyncMock()
        mock_secrets_manager.retrieve.return_value = {"api_key": "sk-provider-key"}

        with patch("src.auth.service.get_secrets_manager", return_value=mock_secrets_manager):
            result = await auth_service.get_llm_api_key_by_provider(
                sample_llm_credential.user_id,
                "openai",
            )

        assert result == "sk-provider-key"

    @pytest.mark.asyncio
    async def test_returns_none_when_no_credential(self, auth_service, mock_session):
        """Test returns None when no credential for provider."""
        mock_session.execute.return_value = mock_scalar_result(None)

        result = await auth_service.get_llm_api_key_by_provider(str(uuid4()), "anthropic")

        assert result is None


# ============================================================================
# Tests: list_all_users
# ============================================================================


class TestListAllUsers:
    """Tests for list_all_users method."""

    @pytest.mark.asyncio
    async def test_returns_users_with_pagination(self, auth_service, mock_session, sample_user, superuser):
        """Test listing users with pagination."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2

        mock_session.execute.side_effect = [
            mock_count_result,
            mock_scalars_result([sample_user, superuser]),
        ]

        users, total = await auth_service.list_all_users(skip=0, limit=10)

        assert len(users) == 2
        assert total == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_users(self, auth_service, mock_session):
        """Test returns empty list when no users."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_session.execute.side_effect = [
            mock_count_result,
            mock_scalars_result([]),
        ]

        users, total = await auth_service.list_all_users()

        assert users == []
        assert total == 0


# ============================================================================
# Tests: update_user_by_admin
# ============================================================================


class TestUpdateUserByAdmin:
    """Tests for update_user_by_admin method."""

    @pytest.mark.asyncio
    async def test_updates_email_by_admin(self, auth_service, mock_session, sample_user):
        """Test admin updating user email."""
        mock_session.execute.side_effect = [
            mock_scalar_result(sample_user),  # get_user_by_id
            mock_scalar_result(None),  # check email not taken
        ]

        result = await auth_service.update_user_by_admin(
            sample_user.id,
            email="admin-set@example.com",
        )

        assert result.email == "admin-set@example.com"

    @pytest.mark.asyncio
    async def test_updates_display_name_by_admin(self, auth_service, mock_session, sample_user):
        """Test admin updating user display name."""
        mock_session.execute.return_value = mock_scalar_result(sample_user)

        result = await auth_service.update_user_by_admin(
            sample_user.id,
            display_name="Admin Set Name",
        )

        assert result.display_name == "Admin Set Name"

    @pytest.mark.asyncio
    async def test_raises_when_email_taken(self, auth_service, mock_session, sample_user):
        """Test raises error when email is already taken."""
        other_user = UserModel(
            id=str(uuid4()),
            email="other@example.com",
            password_hash="hash",
            org_id=DEFAULT_ORG_ID,
        )

        mock_session.execute.side_effect = [
            mock_scalar_result(sample_user),  # get_user_by_id
            mock_scalar_result(other_user),  # email taken by other user
        ]

        with pytest.raises(ValueError, match="Email address is already in use"):
            await auth_service.update_user_by_admin(
                sample_user.id,
                email="other@example.com",
            )


# ============================================================================
# Tests: reset_user_password
# ============================================================================


class TestResetUserPassword:
    """Tests for reset_user_password method."""

    @pytest.mark.asyncio
    async def test_resets_password_successfully(self, auth_service, mock_session, sample_user):
        """Test admin resetting user password."""
        mock_session.execute.return_value = mock_scalar_result(sample_user)

        with patch("src.auth.service.hash_password", return_value="new-admin-hash"):
            result = await auth_service.reset_user_password(sample_user.id, "new-password")

        assert result is True
        assert sample_user.password_hash == "new-admin-hash"

    @pytest.mark.asyncio
    async def test_raises_when_user_not_found(self, auth_service, mock_session):
        """Test raises error when user not found."""
        mock_session.execute.return_value = mock_scalar_result(None)

        with pytest.raises(ValueError, match="User not found"):
            await auth_service.reset_user_password("nonexistent-id", "new-password")


# ============================================================================
# Tests: toggle_user_status
# ============================================================================


class TestToggleUserStatus:
    """Tests for toggle_user_status method."""

    @pytest.mark.asyncio
    async def test_activates_user(self, auth_service, mock_session, inactive_user):
        """Test activating an inactive user."""
        mock_session.execute.return_value = mock_scalar_result(inactive_user)

        result = await auth_service.toggle_user_status(inactive_user.id, is_active=True)

        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_deactivates_user(self, auth_service, mock_session, sample_user):
        """Test deactivating an active user."""
        mock_session.execute.return_value = mock_scalar_result(sample_user)

        result = await auth_service.toggle_user_status(sample_user.id, is_active=False)

        assert result.is_active is False

    @pytest.mark.asyncio
    async def test_raises_when_user_not_found(self, auth_service, mock_session):
        """Test raises error when user not found."""
        mock_session.execute.return_value = mock_scalar_result(None)

        with pytest.raises(ValueError, match="User not found"):
            await auth_service.toggle_user_status("nonexistent-id", is_active=True)
