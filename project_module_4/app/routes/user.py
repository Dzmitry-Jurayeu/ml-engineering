from fastapi import APIRouter, HTTPException, status, Depends
from database.database import get_session
from models.user import User
from routes.api_models import ModelEventOut, BalanceReplenishmentEventOut, UserSignUp, UserOut, UserSignIn, UserEmail, \
    Token
from services.crud import user as UserService
from typing import List, Dict, Union, Annotated
from loguru import logger
import bcrypt
import os
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

user_route = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/signin")
logger.info(oauth2_scheme)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session=Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = UserService.get_user_by_email(email, session)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
        current_user: Annotated[UserOut, Depends(get_current_user)],
):
    # if current_user.disabled:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@user_route.post(
    '/signup',
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Register a new user with email and password")
async def signup(data: UserSignUp, session=Depends(get_session)) -> Dict[str, str]:
    """
    Create new user account.

    Args:
        data: User registration data
        session: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If user already exists
    """
    try:
        if UserService.get_user_by_email(data.email, session):
            logger.warning(f"Signup attempt with existing email: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )

        user = User(**data.model_dump())
        UserService.create_user(user, session)
        logger.info(f"New user registered: {data.email}")
        return {"message": "User successfully registered"}

    except Exception as e:
        logger.error(f"Error during signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )


@user_route.post('/signin')
async def signin(data: Annotated[OAuth2PasswordRequestForm, Depends()], session=Depends(get_session)) -> Token:
    """
    Authenticate existing user.

    Args:
        data: User credentials
        session: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If authentication fails
    """
    email = data.username
    user = UserService.get_user_by_email(email, session)
    if user is None:
        logger.warning(f"Login attempt with non-existent email: {email}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")

    if not bcrypt.checkpw(data.password.encode("utf-8"), user.password.encode("utf-8")):
        logger.warning(f"Failed login attempt for user: {email}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Wrong credentials passed")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@user_route.get(
    "/get_all_users",
    response_model=List[UserOut],
    summary="Get all users",
    response_description="List of all users"
)
async def get_all_users(current_user: Annotated[UserOut, Depends(get_current_active_user)],
                        session=Depends(get_session)) -> List[UserOut]:
    """
    Get list of all users.

    Args:
        session: Database session

    Returns:
        List[UserResponse]: List of users
    """
    try:
        if current_user.is_admin:
            users = UserService.get_all_users(session)
            logger.info(f"Retrieved {len(users)} users")
            return users
        else:
            logger.error(f"Insufficient permissions. User: {current_user}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving users"
        )


@user_route.post(
    "/get_user_history",
    response_model=List[Union[ModelEventOut, BalanceReplenishmentEventOut]],
    summary="Get all user's events",
    response_description="List of all user's events"
)
async def get_user_history(current_user: Annotated[UserOut, Depends(get_current_active_user)],
                           session=Depends(get_session)) -> List[
    Union[ModelEventOut, BalanceReplenishmentEventOut]]:
    """
    Get list of all user's events.

    Args:
        data: User data
        session: Database session

    Returns:
        List[UserResponse]: List of user's events
    """
    try:
        events = UserService.get_user_history(current_user, session)
        logger.info(f"Retrieved {len(events)} history events.")
        return events
    except Exception as e:
        logger.error(f"Error retrieving user's history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user's history."
        )
