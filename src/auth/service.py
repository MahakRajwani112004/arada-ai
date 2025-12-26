"""Authentication service with business logic."""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt_handler import create_access_token, create_refresh_token, hash_token
from src.auth.password import hash_password, verify_password
from src.auth.schemas import TokenResponse, UserResponse
from src.config import get_settings
from src.storage.models import (
    APIKeyModel,
    DEFAULT_ORG_ID,
    LLMCredentialModel,
    RefreshTokenModel,
    UserInviteModel,
    UserModel,
)
from src.secrets.manager import get_secrets_manager

settings = get_settings()


class AuthService:
    """Service for authentication operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """Get a user by email."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        """Get a user by ID."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        return result.scalar_one_or_none()

    async def authenticate_user(
        self, email: str, password: str
    ) -> Optional[UserModel]:
        """Authenticate a user with email and password."""
        user = await self.get_user_by_email(email)
        if user is None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user

    async def create_tokens(self, user: UserModel) -> TokenResponse:
        """Create access and refresh tokens for a user."""
        # Create access token
        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            is_superuser=user.is_superuser,
        )

        # Create refresh token
        raw_refresh, token_hash, expires_at = create_refresh_token()

        # Store refresh token in database
        refresh_token_model = RefreshTokenModel(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(refresh_token_model)

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    async def refresh_tokens(self, refresh_token: str) -> Optional[TokenResponse]:
        """Refresh tokens using a valid refresh token."""
        token_hash = hash_token(refresh_token)

        # Find the refresh token
        result = await self.session.execute(
            select(RefreshTokenModel).where(
                RefreshTokenModel.token_hash == token_hash,
                RefreshTokenModel.is_revoked == False,
                RefreshTokenModel.expires_at > datetime.now(timezone.utc),
            )
        )
        token_model = result.scalar_one_or_none()

        if token_model is None:
            return None

        # Get the user
        user = await self.get_user_by_id(token_model.user_id)
        if user is None or not user.is_active:
            return None

        # Revoke the old refresh token (rotation)
        token_model.is_revoked = True

        # Create new tokens
        return await self.create_tokens(user)

    async def revoke_refresh_token(self, refresh_token: str) -> bool:
        """Revoke a refresh token (logout)."""
        token_hash = hash_token(refresh_token)

        result = await self.session.execute(
            select(RefreshTokenModel).where(
                RefreshTokenModel.token_hash == token_hash
            )
        )
        token_model = result.scalar_one_or_none()

        if token_model is None:
            return False

        token_model.is_revoked = True
        return True

    async def validate_invite(self, invite_code: str) -> Optional[UserInviteModel]:
        """Validate an invite code."""
        result = await self.session.execute(
            select(UserInviteModel).where(
                UserInviteModel.invite_code == invite_code,
                UserInviteModel.is_used == False,
                UserInviteModel.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        password: str,
        display_name: Optional[str],
        org_id: str = DEFAULT_ORG_ID,
    ) -> UserModel:
        """Create a new user (open registration)."""
        user = UserModel(
            email=email.lower(),
            password_hash=hash_password(password),
            display_name=display_name,
            org_id=org_id,
        )
        self.session.add(user)
        await self.session.flush()  # Get the user ID
        return user

    async def create_user_with_invite(
        self,
        email: str,
        password: str,
        display_name: Optional[str],
        invite: UserInviteModel,
    ) -> UserModel:
        """Create a new user from an invite."""
        user = UserModel(
            email=email.lower(),
            password_hash=hash_password(password),
            display_name=display_name,
            org_id=invite.org_id,
            invited_by=invite.invited_by,
        )
        self.session.add(user)

        # Mark invite as used
        invite.is_used = True
        invite.used_by = user.id

        await self.session.flush()  # Get the user ID
        return user

    async def create_invite(
        self, email: str, invited_by: str, org_id: str = DEFAULT_ORG_ID
    ) -> UserInviteModel:
        """Create a new invite."""
        # Check if user already exists
        existing_user = await self.get_user_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists")

        # Check for existing unused invite
        result = await self.session.execute(
            select(UserInviteModel).where(
                UserInviteModel.email == email.lower(),
                UserInviteModel.is_used == False,
                UserInviteModel.expires_at > datetime.now(timezone.utc),
            )
        )
        existing_invite = result.scalar_one_or_none()
        if existing_invite:
            # Return existing valid invite
            return existing_invite

        # Create new invite
        invite = UserInviteModel(
            email=email.lower(),
            invite_code=secrets.token_urlsafe(32),
            invited_by=invited_by,
            org_id=org_id,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.invite_expire_days),
        )
        self.session.add(invite)
        await self.session.flush()
        return invite

    async def create_superuser(
        self, email: str, password: str, org_id: str = DEFAULT_ORG_ID
    ) -> UserModel:
        """Create a superuser (for initial setup)."""
        user = UserModel(
            email=email.lower(),
            password_hash=hash_password(password),
            display_name="Super Admin",
            is_superuser=True,
            org_id=org_id,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    # ============ Settings Methods ============

    async def update_email(self, user_id: str, new_email: str) -> UserModel:
        """Update user's email address."""
        # Check if new email is already taken
        existing = await self.get_user_by_email(new_email)
        if existing and existing.id != user_id:
            raise ValueError("Email address is already in use")

        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        user.email = new_email.lower()
        await self.session.flush()
        return user

    async def update_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> bool:
        """Update user's password after verifying current password."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")

        # Update password
        user.password_hash = hash_password(new_password)
        await self.session.flush()
        return True

    async def update_display_name(
        self, user_id: str, display_name: Optional[str]
    ) -> UserModel:
        """Update user's display name."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        user.display_name = display_name
        await self.session.flush()
        return user

    # ============ API Key Methods ============

    async def create_api_key(self, user_id: str, name: str) -> tuple[APIKeyModel, str]:
        """Create a new API key for a user.

        Returns the API key model and the raw key (only available at creation time).
        """
        # Generate a secure random key
        raw_key = f"mk_{secrets.token_urlsafe(32)}"
        key_prefix = raw_key[:12]  # Store prefix for display
        key_hash = hash_token(raw_key)

        api_key = APIKeyModel(
            user_id=user_id,
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
        )
        self.session.add(api_key)
        await self.session.flush()

        return api_key, raw_key

    async def list_api_keys(self, user_id: str) -> list[APIKeyModel]:
        """List all API keys for a user."""
        result = await self.session.execute(
            select(APIKeyModel)
            .where(APIKeyModel.user_id == user_id)
            .order_by(APIKeyModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_api_key(self, key_id: str, user_id: str) -> Optional[APIKeyModel]:
        """Get an API key by ID for a specific user."""
        result = await self.session.execute(
            select(APIKeyModel).where(
                APIKeyModel.id == key_id,
                APIKeyModel.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_api_key(self, key_id: str, user_id: str) -> bool:
        """Delete an API key."""
        api_key = await self.get_api_key(key_id, user_id)
        if not api_key:
            return False

        await self.session.delete(api_key)
        await self.session.flush()
        return True

    async def validate_api_key(self, raw_key: str) -> Optional[UserModel]:
        """Validate an API key and return the associated user."""
        key_hash = hash_token(raw_key)

        result = await self.session.execute(
            select(APIKeyModel).where(
                APIKeyModel.key_hash == key_hash,
                APIKeyModel.is_active == True,
            )
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            return None

        # Update last used timestamp
        api_key.last_used_at = datetime.now(timezone.utc)

        # Get the user
        user = await self.get_user_by_id(api_key.user_id)
        if not user or not user.is_active:
            return None

        return user

    # ============ LLM Credential Methods ============

    def _create_api_key_preview(self, api_key: str) -> str:
        """Create a masked preview of an API key.

        Args:
            api_key: The full API key

        Returns:
            First 8 characters + masked remainder
        """
        if len(api_key) <= 8:
            return api_key[:4] + "•" * (len(api_key) - 4)
        return api_key[:8] + "•" * 24

    async def create_llm_credential(
        self,
        user_id: str,
        provider: str,
        display_name: str,
        api_key: str,
        api_base: str | None = None,
    ) -> LLMCredentialModel:
        """Create a new LLM provider credential for a user.

        Args:
            user_id: The user's ID
            provider: LLM provider name (openai, anthropic, etc.)
            display_name: User-friendly name for this credential
            api_key: The API key for the provider
            api_base: Optional custom API base URL

        Returns:
            The created LLMCredentialModel
        """
        import uuid

        # Generate credential ID and secret reference
        credential_id = str(uuid.uuid4())
        secret_ref = f"users/{user_id}/llm/{provider}/{credential_id}"

        # Store API key in vault
        secrets_manager = get_secrets_manager()
        await secrets_manager.store(
            key=secret_ref,
            value={
                "api_key": api_key,
                "user_id": user_id,
                "provider": provider,
            }
        )

        # Create database record with only the reference
        llm_credential = LLMCredentialModel(
            id=credential_id,
            user_id=user_id,
            provider=provider.lower(),
            display_name=display_name,
            secret_ref=secret_ref,
            api_key_preview=self._create_api_key_preview(api_key),
            api_base=api_base,
        )
        self.session.add(llm_credential)
        await self.session.flush()

        return llm_credential

    async def list_llm_credentials(self, user_id: str) -> list[LLMCredentialModel]:
        """List all LLM credentials for a user."""
        result = await self.session.execute(
            select(LLMCredentialModel)
            .where(LLMCredentialModel.user_id == user_id)
            .order_by(LLMCredentialModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_llm_credential(
        self, credential_id: str, user_id: str
    ) -> LLMCredentialModel | None:
        """Get an LLM credential by ID for a specific user."""
        result = await self.session.execute(
            select(LLMCredentialModel).where(
                LLMCredentialModel.id == credential_id,
                LLMCredentialModel.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_llm_credential_by_provider(
        self, user_id: str, provider: str
    ) -> LLMCredentialModel | None:
        """Get an LLM credential by provider for a specific user."""
        result = await self.session.execute(
            select(LLMCredentialModel).where(
                LLMCredentialModel.user_id == user_id,
                LLMCredentialModel.provider == provider.lower(),
                LLMCredentialModel.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def update_llm_credential(
        self,
        credential_id: str,
        user_id: str,
        display_name: str | None = None,
        api_key: str | None = None,
        api_base: str | None = None,
        is_active: bool | None = None,
    ) -> LLMCredentialModel | None:
        """Update an LLM credential.

        Args:
            credential_id: The credential's ID
            user_id: The user's ID (for ownership check)
            display_name: New display name (optional)
            api_key: New API key (optional)
            api_base: New API base URL (optional)
            is_active: New active status (optional)

        Returns:
            Updated credential or None if not found
        """
        credential = await self.get_llm_credential(credential_id, user_id)
        if not credential:
            return None

        if display_name is not None:
            credential.display_name = display_name

        if api_key is not None:
            # Update API key in vault
            secrets_manager = get_secrets_manager()
            await secrets_manager.store(
                key=credential.secret_ref,
                value={
                    "api_key": api_key,
                    "user_id": user_id,
                    "provider": credential.provider,
                }
            )
            # Update the preview
            credential.api_key_preview = self._create_api_key_preview(api_key)

        if api_base is not None:
            credential.api_base = api_base

        if is_active is not None:
            credential.is_active = is_active

        await self.session.flush()
        return credential

    async def delete_llm_credential(self, credential_id: str, user_id: str) -> bool:
        """Delete an LLM credential and its vault entry."""
        credential = await self.get_llm_credential(credential_id, user_id)
        if not credential:
            return False

        # Delete from vault
        secrets_manager = get_secrets_manager()
        try:
            await secrets_manager.delete(credential.secret_ref)
        except KeyError:
            pass  # Secret already deleted

        # Delete database record
        await self.session.delete(credential)
        await self.session.flush()
        return True

    async def get_llm_api_key(self, credential_id: str, user_id: str) -> str | None:
        """Retrieve the actual API key from vault.

        Args:
            credential_id: The credential's ID
            user_id: The user's ID (for ownership check)

        Returns:
            The API key or None if not found
        """
        credential = await self.get_llm_credential(credential_id, user_id)
        if not credential:
            return None

        secrets_manager = get_secrets_manager()
        try:
            secret_data = await secrets_manager.retrieve(credential.secret_ref)
            if secret_data and "api_key" in secret_data:
                # Update last used timestamp
                credential.last_used_at = datetime.now(timezone.utc)
                await self.session.flush()
                return secret_data["api_key"]
        except KeyError:
            pass

        return None

    async def get_llm_api_key_by_provider(self, user_id: str, provider: str) -> str | None:
        """Get the API key for a specific provider for a user.

        Args:
            user_id: The user's ID
            provider: The provider name (openai, anthropic, etc.)

        Returns:
            The API key or None if not found
        """
        credential = await self.get_llm_credential_by_provider(user_id, provider)
        if not credential:
            return None

        secrets_manager = get_secrets_manager()
        try:
            secret_data = await secrets_manager.retrieve(credential.secret_ref)
            if secret_data and "api_key" in secret_data:
                # Update last used timestamp
                credential.last_used_at = datetime.now(timezone.utc)
                await self.session.flush()
                return secret_data["api_key"]
        except KeyError:
            pass

        return None

    # ============ Admin Methods ============

    async def list_all_users(
        self, skip: int = 0, limit: int = 50
    ) -> tuple[list[UserModel], int]:
        """List all users with pagination (admin only)."""
        from sqlalchemy import func

        # Get total count
        count_result = await self.session.execute(select(func.count(UserModel.id)))
        total = count_result.scalar() or 0

        # Get users
        result = await self.session.execute(
            select(UserModel)
            .order_by(UserModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        users = list(result.scalars().all())

        return users, total

    async def update_user_by_admin(
        self,
        user_id: str,
        email: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> UserModel:
        """Update a user's profile (admin only)."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if email is not None:
            # Check if new email is already taken
            existing = await self.get_user_by_email(email)
            if existing and existing.id != user_id:
                raise ValueError("Email address is already in use")
            user.email = email.lower()

        if display_name is not None:
            user.display_name = display_name

        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def reset_user_password(self, user_id: str, new_password: str) -> bool:
        """Reset a user's password (admin only, no current password needed)."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        user.password_hash = hash_password(new_password)
        await self.session.flush()
        return True

    async def toggle_user_status(self, user_id: str, is_active: bool) -> UserModel:
        """Activate or deactivate a user (admin only)."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        user.is_active = is_active
        await self.session.flush()
        await self.session.refresh(user)
        return user
