from fastapi import APIRouter, Body, HTTPException, status, Depends
from database.database import get_session
from models.event import ModelEvent, BalanceReplenishmentEvent
from routes.api_models import ModelEventIn, ModelEventOut, BalanceReplenishmentEventIn, BalanceReplenishmentEventOut, \
    UserOut
from typing import List, Union, Dict, Annotated
from services.crud import event as EventService
from services.crud import balance as BalanceService
from services.crud import model as ModelService
from services.crud import user as UserService
from services.rm.rm import send_task
from loguru import logger
from routes.user import get_current_active_user
import json

event_router = APIRouter()


@event_router.get("/retrieve_all_balance_events", response_model=List[BalanceReplenishmentEventOut])
async def retrieve_all_balance_events(current_user: Annotated[UserOut, Depends(get_current_active_user)],
                                      session=Depends(get_session)) -> List[BalanceReplenishmentEventOut]:
    try:
        events = EventService.get_all_balance_events(current_user, session)
        logger.info(f"Retrieved {len(events)} balance events")
        return events
    except Exception as e:
        logger.error(f"Error retrieving balance events: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving balance events"
        )


@event_router.get("/retrieve_all_model_events", response_model=List[ModelEventOut])
async def retrieve_all_model_events(current_user: Annotated[UserOut, Depends(get_current_active_user)],
                                    session=Depends(get_session)) -> List[ModelEventOut]:
    try:
        events = EventService.get_all_model_events(current_user, session)
        logger.info(f"Retrieved {len(events)} model events")
        return events
    except Exception as e:
        logger.error(f"Error retrieving model events: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving model events"
        )


@event_router.get("/balance_event/{balance_event_id}", response_model=BalanceReplenishmentEventOut)
async def retrieve_balance_event(balance_event_id: int,
                                 current_user: Annotated[UserOut, Depends(get_current_active_user)],
                                 session=Depends(get_session)) -> BalanceReplenishmentEventOut:
    try:
        if current_user.is_admin:
            events = EventService.get_balance_event_by_id(balance_event_id, session)
            return events
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Balance event with supplied ID does not exist")


@event_router.get("/model_event/{model_event_id}", response_model=ModelEventOut)
async def retrieve_model_event(model_event_id: int, current_user: Annotated[UserOut, Depends(get_current_active_user)],
                               session=Depends(get_session)) -> ModelEventOut:
    try:
        if current_user.is_admin:
            events = EventService.get_model_event_by_id(model_event_id, session)
            return events
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Balance event with supplied ID does not exist")


@event_router.post("/new_my_balance_event")
async def create_my_balance_event(current_user: Annotated[UserOut, Depends(get_current_active_user)],
                               body: BalanceReplenishmentEventIn = Body(...),
                               session=Depends(get_session)) -> Dict[str, str]:
    balance_event = EventService.create_balance_event(
        BalanceReplenishmentEvent(creator_id=current_user.user_id, **body.model_dump()), session)
    BalanceService.balance_replenishment(balance_event, session)
    return {"message": "Balance event created successfully. Balance replenished."}


@event_router.post("/new_balance_event")
async def create_balance_event(user_id: int,
                               current_user: Annotated[UserOut, Depends(get_current_active_user)],
                               body: BalanceReplenishmentEventIn = Body(...),
                               session=Depends(get_session)) -> Dict[str, str]:
    if current_user.is_admin:
        user = UserService.get_user_by_id(user_id, session)
        if user is None:
            logger.warning(f"Balance replenishment event attempt with non-existent user id: {user_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")
        balance_event = EventService.create_balance_event(
            BalanceReplenishmentEvent(creator_id=user_id, **body.model_dump()), session)
        BalanceService.balance_replenishment(balance_event, session)
        return {"message": "Balance replenishment event created successfully. Balance replenished."}
    else:
        logger.error(f"Insufficient permissions. User: {current_user}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )


@event_router.post("/new_model_event")
async def create_model_event(current_user: Annotated[UserOut, Depends(get_current_active_user)],
                             body: ModelEventIn = Body(...),
                             session=Depends(get_session),
                             task: str = "text-classification",
                             model_name: str = "unitary/toxic-bert") -> Dict[str, str | float | int]:
    model_event = EventService.create_model_event(ModelEvent(creator_id=current_user.user_id, **body.model_dump()),
                                                  session)
    model = ModelService.get_model_by_params(session, task, model_name)
    model = ModelService.init_model(model)
    result = EventService.update_model_event(model_event, session, model)
    return {"message": "Model event created.", "score": result.score, "response": result.response,
            "amount": result.amount}

@event_router.post("/send_task")
async def send_task_to_queue(current_user: Annotated[UserOut, Depends(get_current_active_user)],
                    body: ModelEventIn = Body(...),
                    session=Depends(get_session),
                    task: str = "text-classification",
                    model_name: str = "unitary/toxic-bert") -> Dict[str, str]:
    try:
        model_event = EventService.create_model_event(ModelEvent(creator_id=current_user.user_id, **body.model_dump()),
                                                      session)
        balance = BalanceService.get_balance_by_user(current_user, session).balance_value
        body = body.model_dump()
        body["user_id"] = current_user.user_id
        body["event_id"] = model_event.event_id
        body["balance"] = balance
        body["task"] = task
        body["model_name"] = model_name
        body = json.dumps(body)
        send_task(body)
        return {"message": "Task sent successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)

@event_router.post("/task_result")
async def get_task_result(body: dict = Body(...), session=Depends(get_session),):
    EventService.update_task_model_event(body, session)
    return {"Result": "Data received and updated."}


@event_router.delete("/balance_event/{balance_event_id}")
async def delete_balance_event(current_user: Annotated[UserOut, Depends(get_current_active_user)],
                               balance_event_id: int, session=Depends(get_session)) -> Dict[str, str]:
    try:
        if current_user.is_admin:
            EventService.delete_balance_events_by_id(balance_event_id, session)
            return {"message": "Balance event deleted successfully"}
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Balance event with supplied ID does not exist")


@event_router.delete("/model_event/{model_event_id}")
async def delete_model_event(current_user: Annotated[UserOut, Depends(get_current_active_user)], model_event_id: int,
                             session=Depends(get_session)) -> Dict[str, str]:
    try:
        if current_user.is_admin:
            EventService.delete_model_events_by_id(model_event_id, session)
            return {"message": "Model event deleted successfully"}
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model event with supplied ID does not exist")


@event_router.delete("/")
async def delete_all_events(current_user: Annotated[UserOut, Depends(get_current_active_user)],
                            session=Depends(get_session)) -> Dict[str, str]:
    if current_user.is_admin:
        EventService.delete_all_events(session)
        return {"message": "Events deleted successfully"}
    else:
        logger.error(f"Insufficient permissions. User: {current_user}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
