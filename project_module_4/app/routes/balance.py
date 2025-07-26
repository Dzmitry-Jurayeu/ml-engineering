from fastapi import APIRouter, Body, HTTPException, status, Depends
from database.database import get_session
from models.balance import Balance
from typing import List
from services.crud import balance as BalanceService
from loguru import logger

balance_router = APIRouter()

@balance_router.get("/", response_model=List[Balance])
async def retrieve_balances(session=Depends(get_session)) -> List[Balance]:
    try:
        balances = BalanceService.get_all_balances(session)
        logger.info(f"Retrieved {len(balances)} balances")
        return balances
    except Exception as e:
        logger.error(f"Error retrieving balances: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving balances"
        )


@balance_router.get("/{balance_id}", response_model=Balance)
async def retrieve_balance_by_id(balance_id: int, session=Depends(get_session)) -> Balance:
    try:
        models = BalanceService.get_balance_by_id(balance_id, session)
        return models
    except Exception as e:
        logger.error(f"Error retrieving balance with ID {balance_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving balance with ID {balance_id}"
        )
