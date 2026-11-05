from datetime import UTC, datetime
from hashlib import sha256

from pwdlib import PasswordHash

from app.api.schemas.auth import AccessTokenPayload
from app.core.config import TraceLayer
from app.core.decorator import trace
from app.models.session import SessionCreate
from app.models.user import UserDB, UserStatus
from app.repositories.interfaces.session import SessionRepositoryInterface
from app.repositories.interfaces.user import UserRepositoryInterface
from app.services.token.errors import TokenServiceError
from app.services.token.service import TokenService

from .errors import (
    TokenInvalidError,
    TokenNotRevokedError,
    UserInvalidCredentialsError,
    UserInvalidError,
    UserNotPasswordError,
)

password_hash = PasswordHash.recommended()


class AuthService:
    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        session_repo: SessionRepositoryInterface,
        token_service: TokenService,
    ):
        self.user_repo = user_repo
        self.session_repo = session_repo
        self.token_service = token_service

    def hash_token(self, token: str) -> str:
        return sha256(token.encode("utf-8")).hexdigest()

    @trace(TraceLayer.SERVICE)
    async def login(self, email: str, password: str) -> tuple[str, str, UserDB]:
        """
        Login for user.

        Returns:
            tuple[str, str, UserDB]:
                - access_token: The encoded access JWT.
                - refresh_token: The encoded refresh JWT.
                - user: User data
        """
        user = await self.user_repo.getByEmail(email)
        if user is None:
            raise UserInvalidError()
        if user.status != UserStatus.ACTIVE:
            raise UserInvalidError()
        if user.password_hash is None:
            raise UserNotPasswordError()
        valid = password_hash.verify(password, user.password_hash)
        if not valid:
            raise UserInvalidCredentialsError()
        access_token, _ = await self.token_service.generateAccessToken(user.id)
        refresh_token, jti, expire = await self.token_service.generateRefreshToken(
            user.id
        )
        _ = await self.session_repo.create(
            SessionCreate(
                token_hash=self.hash_token(refresh_token),
                jti=jti,
                user_id=user.id,
                expires_at=expire,
            )
        )
        return (access_token, refresh_token, user)

    @trace(TraceLayer.SERVICE)
    async def refresh(self, refresh_token: str) -> tuple[str, AccessTokenPayload]:
        """
        Login for user.

        Returns:
            tuple[str, AccessTokenPayload]:
                - access_token: The encoded access JWT.
                - access_token_payload: The access payload JWT.
        """
        try:
            payload = await self.token_service.verifyRefreshToken(refresh_token)
        except TokenServiceError:
            raise TokenInvalidError()
        stored = await self.session_repo.getByToken(payload.jti)
        if not stored or stored.expires_at < datetime.now(UTC) or stored.revoked:
            raise TokenInvalidError()
        user = await self.user_repo.getById(int(payload.sub))
        if not user or user.status != UserStatus.ACTIVE:
            raise UserInvalidError()
        access_token, expire = await self.token_service.generateAccessToken(user.id)
        return (access_token, AccessTokenPayload(sub=str(user.id), exp=expire))

    async def revokeSession(self, refresh_token: str):
        try:
            payload = await self.token_service.verifyRefreshToken(refresh_token)
        except TokenServiceError:
            raise TokenInvalidError()
        result = await self.session_repo.revokedByJti(payload.jti)
        if not result:
            raise TokenNotRevokedError()
