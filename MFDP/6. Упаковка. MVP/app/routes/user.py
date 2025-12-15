from fastapi import APIRouter, HTTPException, status, Depends, Response, Cookie, Request, Query
from database.database import get_session
from models.user import User
from routes.api_models import ModelEventOut, UserOut, Token
from services.crud import user as UserService
from typing import List, Dict, Union, Annotated, Optional
from loguru import logger
import os
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse, JSONResponse
import jwt
from jwt.exceptions import InvalidTokenError
from helper.helper import make_auth_url
import secrets
import time

_state_store: dict[str, dict] = {}
_STATE_TTL_SECONDS = 300
STATE_COOKIE_NAME = "auth_state"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REDIRECT_DEFAULT = "http://localhost/api/docs"


user_route = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/signin")
logger.info(oauth2_scheme)

def _store_state(state: str, payload: dict):
    payload["_ts"] = int(time.time())
    _state_store[state] = payload

def _pop_state(state: str) -> Optional[dict]:
    data = _state_store.pop(state, None)
    if not data:
        return None
    if int(time.time()) - data.get("_ts", 0) > _STATE_TTL_SECONDS:
        return None
    return data

def is_request_from_swagger(request: Request) -> bool:
    referer = request.headers.get("referer", "")
    if request.query_params.get("from_swagger") in ("1", "true", "yes"):
        return True
    if "/docs" in referer or "swagger" in referer or "redoc" in referer:
        return True
    return False


async def get_current_user(token: Annotated[str | None, Cookie(alias="access_token")] = None,
                           session=Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = int(token)
        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = UserService.get_user_by_id(user_id, session)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
        current_user: Annotated[UserOut, Depends(get_current_user)],
):
    return current_user


@user_route.get("/signin")
async def signin(request: Request, response: Response):
    """
    Start auth flow: redirect user to provider or return auth_url for Swagger.
    """
    redirect_to = request.query_params.get("redirect") or REDIRECT_DEFAULT

    # generate state and store it in memory
    state = secrets.token_urlsafe(32)
    _store_state(state, {"next": redirect_to})

    CALLBACK_URL = os.getenv("AUTH_CALLBACK_URL", "http://localhost/api/users/callback")
    auth_url = make_auth_url(redirect_uri=CALLBACK_URL, state=state)

    # if is_request_from_swagger(request):
    #     resp = JSONResponse({"auth_url": auth_url})
    #     resp.set_cookie(
    #         key=STATE_COOKIE_NAME,
    #         value=state,
    #         httponly=True,
    #         samesite="lax",
    #         max_age=_STATE_TTL_SECONDS,
    #         path="/",
    #         secure=False
    #     )
    #     return resp

    resp = RedirectResponse(url=auth_url, status_code=302)
    # store state in cookie as well (optional for dev)
    resp.set_cookie(STATE_COOKIE_NAME, state, httponly=True, samesite="lax", max_age=_STATE_TTL_SECONDS, path="/")
    return resp

@user_route.get("/callback")
async def auth_callback(request: Request,
                        auth_status: Optional[str] = Query(None, alias="status"),
                        access_token: Optional[str] = None,
                        expires_at: Optional[str] = None,
                        account_id: Optional[str] = None,
                        nickname: Optional[str] = None,
                        state: Optional[str] = None,
                        session=Depends(get_session)):
    """
    Callback endpoint that provider redirects to.
    Provider returns auth_status, access_token, expires_at, account_id, nickname, and state.
    """
    # 1. check auth_status
    if auth_status != "ok":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Authentication failed: {auth_status}")

    # 2. resolve state: prefer query param, fallback to cookie
    cookie_state = request.cookies.get(STATE_COOKIE_NAME)
    signed_state = state or cookie_state
    if not signed_state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing state")

    state_data = _pop_state(signed_state)
    if not state_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired state")

    next_url = state_data.get("next", REDIRECT_DEFAULT)


    # 3. validate account_id and create/update user
    if not account_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing account_id")

    # create or update user in DB (implement in UserService)
    user = UserService.create_user(User(user_id=int(account_id)), session)

    # 4. set cookie with user_id (dev). In prod use session id or secure JWT.
    redirect_url = (
        f"{next_url}"
        f"?access_token={user.user_id}"
    )
    response = RedirectResponse(url=redirect_url, status_code=302)
    response.set_cookie(
        key="access_token",
        value=str(user.user_id),
        httponly=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )

    # cleanup state cookie
    response.delete_cookie(STATE_COOKIE_NAME, path="/")
    return response


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


@user_route.get(
    "/get_user_history",
    response_model=List[Union[ModelEventOut]],
    summary="Get all user's events",
    response_description="List of all user's events"
)
async def get_user_history(current_user: Annotated[UserOut, Depends(get_current_active_user)],
                           session=Depends(get_session)) -> List[Union[ModelEventOut]]:
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


@user_route.post("/signout", summary="User Sign-out")
async def signout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Signed out successfully"}


@user_route.get(
    "/me",
    response_model=UserOut,
    summary="Get current user",
    response_description="Current user info"
)
async def get_me(current_user: Annotated[UserOut, Depends(get_current_active_user)],
                 session=Depends(get_session)) -> UserOut:
    """
    Get list of all users.

    Args:
        session: Database session

    Returns:
        List[UserResponse]: List of users
    """
    try:
        user = UserService.get_user_by_id(current_user.user_id, session)
        logger.info(f"User retrieved")
        return user
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving users"
        )


@user_route.post(
    "/grant_admin",
    response_model=Dict,
    summary="Grant Admin status to user",
)
async def grant_admin(user_id: int,
                      current_user: Annotated[UserOut, Depends(get_current_active_user)],
                      session=Depends(get_session)) -> Dict[str, str]:
    """
    Grant Admin status to user.

    Args:
        user_id: User ID

    Returns:
        Dict[str, str]
    """
    try:
        if current_user.is_admin:
            users = UserService.grant_admin_status(user_id, session)
            logger.info(f"User {current_user.user_id} grant admin status to user with ID {user_id}.")
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
        logger.error(f"Error grant admin status to users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error grant admin status to users"
        )


@user_route.post(
    "/revoke_admin",
    response_model=Dict,
    summary="Revoke Admin status to user",
)
async def revoke_admin(user_id: int,
                       current_user: Annotated[UserOut, Depends(get_current_active_user)],
                       session=Depends(get_session)) -> Dict[str, str]:
    """
    Revoke Admin status to user.

    Args:
        user_id: User ID

    Returns:
        Dict[str, str]
    """
    try:
        if current_user.is_admin:
            users = UserService.revoke_admin_status(user_id, session)
            logger.info(f"User {current_user.user_id} revoke admin status from user with ID {user_id}.")
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
        logger.error(f"Error grant admin status to users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error grant admin status to users"
        )
