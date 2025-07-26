from fastapi import APIRouter, Body, HTTPException, status, Depends
from database.database import get_session
from models.event import ModelEvent, BalanceReplenishmentEvent
from typing import List, Union
from services.crud import event as EventService
from services.crud import balance as BalanceService
from services.crud import model as ModelService
from loguru import logger

event_router = APIRouter()


@event_router.get("/", response_model=List[Union[ModelEvent, BalanceReplenishmentEvent]])
async def retrieve_all_events(session=Depends(get_session)) -> List[Union[ModelEvent, BalanceReplenishmentEvent]]:
    try:
        events = EventService.get_all_events(session)
        logger.info(f"Retrieved {len(events)} events")
        return events
    except Exception as e:
        logger.error(f"Error retrieving events: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving events"
        )


@event_router.get("/retrieve_all_balance_events", response_model=List[BalanceReplenishmentEvent])
async def retrieve_all_balance_events(session=Depends(get_session)) -> List[BalanceReplenishmentEvent]:
    try:
        events = EventService.get_all_balance_events(session)
        logger.info(f"Retrieved {len(events)} balance events")
        return events
    except Exception as e:
        logger.error(f"Error retrieving balance events: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving balance events"
        )


@event_router.get("/retrieve_all_model_events", response_model=List[ModelEvent])
async def retrieve_all_events(session=Depends(get_session)) -> List[ModelEvent]:
    try:
        events = EventService.get_all_model_events(session)
        logger.info(f"Retrieved {len(events)} model events")
        return events
    except Exception as e:
        logger.error(f"Error retrieving model events: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving model events"
        )


@event_router.get("/balance_event/{balance_event_id}", response_model=BalanceReplenishmentEvent)
async def retrieve_balance_event(balance_event_id: int, session=Depends(get_session)) -> BalanceReplenishmentEvent:
    try:
        events = EventService.get_balance_event_by_id(balance_event_id, session)
        return events
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Balance event with supplied ID does not exist")


@event_router.get("/model_event/{model_event_id}", response_model=ModelEvent)
async def retrieve_model_event(model_event_id: int, session=Depends(get_session)) -> ModelEvent:
    try:
        events = EventService.get_model_event_by_id(model_event_id, session)
        return events
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Balance event with supplied ID does not exist")


@event_router.post("/new_balance_event")
async def create_balance_event(body: BalanceReplenishmentEvent = Body(...), session=Depends(get_session)) -> dict:
    balance_event = EventService.create_balance_event(body, session)
    BalanceService.balance_replenishment(balance_event, session)
    return {"message": "Balance event created successfully. Balance replenished."}


@event_router.post("/new_model_event")
async def create_model_event(body: ModelEvent = Body(...), session=Depends(get_session),
                             task: str = "text-classification", model_name: str = "unitary/toxic-bert") -> dict:
    model_event = EventService.create_model_event(body, session)
    model = ModelService.get_model_by_params(session, task, model_name)
    model = ModelService.init_model(model)
    result = EventService.update_model_event(model_event, session, model)
    return {"message": "Model event created.", "score": result.score, "response": result.response,
            "amount": result.amount}


@event_router.delete("/balance_event/{balance_event_id}")
async def delete_balance_event(balance_event_id: int, session=Depends(get_session)) -> dict:
    try:
        EventService.delete_balance_events_by_id(balance_event_id, session)
        return {"message": "Balance event deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Balance event with supplied ID does not exist")


@event_router.delete("/model_event/{model_event_id}")
async def delete_model_event(model_event_id: int, session=Depends(get_session)) -> dict:
    try:
        EventService.delete_model_events_by_id(model_event_id, session)
        return {"message": "Model event deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model event with supplied ID does not exist")


@event_router.delete("/")
async def delete_all_events(session=Depends(get_session)) -> dict:
    EventService.delete_all_events(session)
    return {"message": "Events deleted successfully"}
