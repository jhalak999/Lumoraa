from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AlreadyExistsError, InvalidCredentialsError, NotFoundError
from app.core.logging import get_logger
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.user import TokenPair, UserCreate

logger = get_logger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, payload: UserCreate) -> User:
        existing = await self.db.scalar(select(User).where(User.email == payload.email))
        if existing:
            raise AlreadyExistsError("An account with this email already exists.")

        user = User(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
        )
        self.db.add(user)
        await self.db.flush()
        logger.info("New user registered: %s", user.email)
        return user

    async def authenticate(self, *, email: str, password: str) -> User:
        user = await self.db.scalar(select(User).where(User.email == email))
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Incorrect email or password.")
        if not user.is_active:
            raise InvalidCredentialsError("This account has been deactivated.")
        return user

    def issue_tokens(self, user: User) -> TokenPair:
        return TokenPair(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )

    async def refresh(self, refresh_token: str) -> TokenPair:
        user_id = decode_token(refresh_token, TokenType.REFRESH)
        user = await self.db.get(User, uuid.UUID(user_id))
        if not user or not user.is_active:
            raise InvalidCredentialsError("User no longer exists or is inactive.")
        return self.issue_tokens(user)

    async def get_user_by_id(self, user_id: uuid.UUID) -> User:
        user = await self.db.get(User, user_id)
        if not user:
            raise NotFoundError("User not found.")
        return user
