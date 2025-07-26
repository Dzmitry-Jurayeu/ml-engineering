from fastapi import APIRouter, HTTPException, status, Depends
from database.database import get_session
from models.user import User
from models.event import ModelEvent, BalanceReplenishmentEvent
from services.crud import user as UserService
from typing import List, Dict, Union
from loguru import logger
import bcrypt

user_route = APIRouter()


@user_route.post(
    '/signup',
    response_model=Dict[str, str],
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Register a new user with email and password")
async def signup(data: User, session=Depends(get_session)) -> Dict[str, str]:
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

        user = User(
            email=data.email,
            password=data.password,
            is_admin=data.is_admin
        )
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
async def signin(data: User, session=Depends(get_session)) -> Dict[str, str]:
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
    user = UserService.get_user_by_email(data.email, session)
    if user is None:
        logger.warning(f"Login attempt with non-existent email: {data.email}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")

    if not bcrypt.checkpw(data.password.encode("utf-8"), user.password.encode("utf-8")):
        logger.warning(f"Failed login attempt for user: {data.email}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Wrong credentials passed")

    return {"message": "User signed in successfully"}


@user_route.get(
    "/get_all_users",
    response_model=List[User],
    summary="Get all users",
    response_description="List of all users"
)
async def get_all_users(session=Depends(get_session)) -> List[User]:
    """
    Get list of all users.

    Args:
        session: Database session

    Returns:
        List[UserResponse]: List of users
    """
    try:
        users = UserService.get_all_users(session)
        logger.info(f"Retrieved {len(users)} users")
        return users
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving users"
        )


@user_route.post(
    "/get_user_history",
    response_model=List[Union[ModelEvent, BalanceReplenishmentEvent]],
    summary="Get all user's events",
    response_description="List of all user's events"
)
async def get_user_history(data: User, session=Depends(get_session)) -> List[
    Union[ModelEvent, BalanceReplenishmentEvent]]:
    """
    Get list of all user's events.

    Args:
        data: User data
        session: Database session

    Returns:
        List[UserResponse]: List of user's events
    """
    try:
        events = UserService.get_user_history(data, session)
        logger.info(f"Retrieved {len(events)} history events.")
        return events
    except Exception as e:
        logger.error(f"Error retrieving user's history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user's history."
        )
