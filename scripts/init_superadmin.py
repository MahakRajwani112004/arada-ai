#!/usr/bin/env python3
"""Initialize super admin user for MagOneAI.

Usage:
    python scripts/init_superadmin.py

This script will prompt for email and password to create the super admin.
"""
import asyncio
import getpass
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from src.auth.password import hash_password
from src.storage.database import init_database, get_async_session
from src.storage.models import DEFAULT_ORG_ID, OrganizationModel, UserModel


async def create_organization_if_not_exists() -> None:
    """Ensure the default organization exists."""
    async with get_async_session() as session:
        result = await session.execute(
            select(OrganizationModel).where(OrganizationModel.id == DEFAULT_ORG_ID)
        )
        org = result.scalar_one_or_none()

        if org is None:
            org = OrganizationModel(
                id=DEFAULT_ORG_ID,
                name="Default Organization",
                slug="default",
            )
            session.add(org)
            print(f"Created default organization: {DEFAULT_ORG_ID}")
        else:
            print(f"Default organization already exists: {DEFAULT_ORG_ID}")


async def create_superadmin(email: str, password: str) -> bool:
    """Create a super admin user."""
    async with get_async_session() as session:
        # Check if user already exists
        result = await session.execute(
            select(UserModel).where(UserModel.email == email.lower())
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if existing_user.is_superuser:
                print(f"Super admin already exists: {email}")
                return False
            else:
                # Upgrade to superuser
                existing_user.is_superuser = True
                print(f"Upgraded existing user to super admin: {email}")
                return True

        # Create new super admin
        user = UserModel(
            email=email.lower(),
            password_hash=hash_password(password),
            display_name="Super Admin",
            is_superuser=True,
            is_active=True,
            org_id=DEFAULT_ORG_ID,
        )
        session.add(user)
        print(f"Created super admin: {email}")
        return True


async def main() -> None:
    """Main entry point."""
    print("=" * 50)
    print("MagOneAI Super Admin Initialization")
    print("=" * 50)
    print()

    # Initialize database
    print("Initializing database...")
    await init_database()

    # Create default organization
    await create_organization_if_not_exists()

    print()

    # Get email
    email = input("Enter super admin email: ").strip()
    if not email:
        print("Error: Email is required")
        sys.exit(1)

    # Basic email validation
    if "@" not in email or "." not in email:
        print("Error: Invalid email format")
        sys.exit(1)

    # Get password
    password = getpass.getpass("Enter super admin password (min 8 chars): ")
    if len(password) < 8:
        print("Error: Password must be at least 8 characters")
        sys.exit(1)

    # Confirm password
    password_confirm = getpass.getpass("Confirm password: ")
    if password != password_confirm:
        print("Error: Passwords do not match")
        sys.exit(1)

    print()

    # Create super admin
    success = await create_superadmin(email, password)

    if success:
        print()
        print("=" * 50)
        print("Super admin created successfully!")
        print("You can now log in at your MagOneAI instance.")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
