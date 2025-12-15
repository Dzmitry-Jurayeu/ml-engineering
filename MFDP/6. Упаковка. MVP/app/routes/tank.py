from fastapi import APIRouter, HTTPException, status, Depends
from database.database import get_session
from routes.api_models import Tank, UserOut
from typing import List
from services.crud import tank as TankService
from loguru import logger
from routes.user import get_current_active_user

tank_route = APIRouter()


@tank_route.get("/retrieve_all_tanks", response_model=List[Tank])
async def retrieve_all_tanks(session=Depends(get_session)) -> List[Tank]:
    try:
        tanks = TankService.get_all_tanks(session)
        logger.info(f"Retrieved {len(tanks)} tanks")
        return tanks
    except Exception as e:
        logger.error(f"Error retrieving tanks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving tanks"
        )


@tank_route.get("/tanks/{tank_id}", response_model=Tank)
async def retrieve_tank(tank_id: int, session=Depends(get_session)) -> Tank:
    try:
        tanks = TankService.get_tank_by_id(tank_id, session)
        if tanks is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tank with ID {tank_id} not found"
            )
        return tanks
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tank with ID {tank_id} not found"
            )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Tank with supplied ID does not exist")