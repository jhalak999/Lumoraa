from fastapi import APIRouter, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import Depends

from app.api.deps import CurrentUser, DbSession
from app.schemas.user import RefreshRequest, TokenPair, UserCreate, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: DbSession) -> UserRead:
    user = await AuthService(db).register(payload)
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenPair)
async def login(
    db: DbSession, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> TokenPair:
    """
    Uses the standard OAuth2 password grant form (username=email, password)
    so this endpoint works directly with `OAuth2PasswordBearer`'s tokenUrl
    and with tools like Swagger UI's built-in "Authorize" button.
    """
    auth_service = AuthService(db)
    user = await auth_service.authenticate(email=form_data.username, password=form_data.password)
    return auth_service.issue_tokens(user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: DbSession) -> TokenPair:
    return await AuthService(db).refresh(payload.refresh_token)


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
