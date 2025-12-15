from fastapi import APIRouter, Body, HTTPException, status, Depends, Request
from database.database import get_session
from models.event import Prediction
from routes.api_models import ModelEventOut, UserOut
from typing import List, Dict, Annotated
from services.crud import event as EventService
from services.crud import model as ModelService
from services.rm.rm import send_task
from loguru import logger
from routes.user import get_current_active_user
import json

event_route = APIRouter()


@event_route.get("/retrieve_all_model_events", response_model=List[ModelEventOut])
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


@event_route.get("/model_event/{model_event_id}", response_model=ModelEventOut)
async def retrieve_model_event(model_event_id: int, current_user: Annotated[UserOut, Depends(get_current_active_user)],
                               session=Depends(get_session)) -> ModelEventOut:
    try:
        if current_user.is_admin:
            events = EventService.get_model_event_by_id(model_event_id, session)
            if events is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Model event with ID {model_event_id} not found"
                )
            return events
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
                detail=f"Model event with ID {model_event_id} not found"
            )
        elif e.status_code == 403:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Balance event with supplied ID does not exist")


@event_route.get("/new_model_event")
async def create_model_event(current_user: Annotated[UserOut, Depends(get_current_active_user)],
                             request: Request,
                             session=Depends(get_session)) -> Dict[str, str | list | None]:
    model_event = EventService.create_model_event(Prediction(creator_id=current_user.user_id),
                                                  session)
    model = ModelService.get_model_by_params(session)
    model = ModelService.init_model(model)
    result = EventService.update_model_event(model_event, session, model, request.app.state.general_df,
                                             request.app.state.premium_df)
    return {"message": "Model event created.", "candidates": result.get("candidates")}


@event_route.get("/send_task")
async def send_task_to_queue(current_user: Annotated[UserOut, Depends(get_current_active_user)],
                             session=Depends(get_session),
                             model_path="./ml/AutogluonModels/ag-20251205_150250") -> Dict[str, str]:
    try:
        model_event = EventService.create_model_event(Prediction(creator_id=current_user.user_id),
                                                      session)
        body = {"user_id": current_user.user_id, "prediction_id": model_event.prediction_id, "model_path":model_path}
        body = json.dumps(body)
        send_task(body)
        return {"message": "Task sent successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)

@event_route.post("/task_result")
async def get_task_result(body: dict = Body(...), session=Depends(get_session), ):
    EventService.update_task_model_event(body, session)
    return {"Result": "Data received and updated."}




@event_route.delete("/model_event/{model_event_id}")
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


@event_route.delete("/")
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
