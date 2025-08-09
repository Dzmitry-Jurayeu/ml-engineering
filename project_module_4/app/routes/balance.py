from fastapi import APIRouter, Body, HTTPException, status, Depends
from database.database import get_session
from routes.api_models import Balance, UserOut
from typing import List, Annotated
from services.crud import balance as BalanceService
from loguru import logger
from routes.user import get_current_active_user

balance_router = APIRouter()


@balance_router.get("/", response_model=List[Balance])
async def retrieve_balances(current_user: Annotated[UserOut, Depends(get_current_active_user)],
                            session=Depends(get_session)) -> List[Balance]:
    try:
        if current_user.is_admin:
            balances = BalanceService.get_all_balances(session)
            logger.info(f"Retrieved {len(balances)} balances")
            return balances
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
        logger.error(f"Error retrieving balances: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving balances"
        )


@balance_router.get("/me", response_model=Balance)
async def retrieve_my_balance(current_user: Annotated[UserOut, Depends(get_current_active_user)],
                              session=Depends(get_session)) -> Balance:
    try:
        balance = BalanceService.get_balance_by_user(current_user, session)
        return balance
    except Exception as e:
        logger.error(f"Error retrieving balance for user {current_user}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving balance for user {current_user}"
        )


@balance_router.get("/balance_id/{balance_id}", response_model=Balance)
async def retrieve_balance_by_id(current_user: Annotated[UserOut, Depends(get_current_active_user)], balance_id: int,
                                 session=Depends(get_session)) -> Balance:
    try:
        if current_user.is_admin:
            balance = BalanceService.get_balance_by_id(balance_id, session)
            if balance is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Balance with ID {balance_id} not found"
                )
            return balance
        else:
            logger.error(f"Insufficient permissions. User: {current_user}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Balance with ID {balance_id} not found"
            )
        elif e.status_code == 403:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
    except Exception as e:
        logger.error(f"Error retrieving balance with ID {balance_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving balance with ID {balance_id}"
        )
