from fastapi import APIRouter, Body, HTTPException, status, Depends
from database.database import get_session
from routes.api_models import ModelIn, ModelOut
from typing import List
from services.crud import model as ModelService
from loguru import logger

model_router = APIRouter()


@model_router.get("/", response_model=List[ModelOut])
async def retrieve_models(session=Depends(get_session)) -> List[ModelOut]:
    try:
        models = ModelService.get_all_models(session)
        logger.info(f"Retrieved {len(models)} models")
        return models
    except Exception as e:
        logger.error(f"Error retrieving models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving models"
        )


@model_router.get("/{model_id}", response_model=ModelOut)
async def retrieve_model_by_id(model_id: int, session=Depends(get_session)) -> ModelOut:
    try:
        models = ModelService.get_model_by_id(model_id, session)
        return models
    except Exception as e:
        logger.error(f"Error retrieving model with ID {model_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving model with ID {model_id}"
        )


@model_router.get("/params/", response_model=ModelOut)
async def retrieve_model_by_params(task: str = "text-classification", model_name: str = "unitary/toxic-bert",
                                   session=Depends(get_session)) -> ModelOut:
    try:
        model = ModelService.get_model_by_params(session, task, model_name)
        return model
    except Exception as e:
        logger.error(f"Error retrieving model with params:\n\ttask = {task}\n\tmodel_name = {model_name}\n {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving model with params:\n\ttask = {task}\n\tmodel_name = {model_name}\n "
        )

@model_router.post("/new_model")
async def create_new_model(body: ModelIn = Body(...), session=Depends(get_session)) -> dict:

    if ModelService.get_model_by_params(session, body.task, body.model_name):
        logger.warning(f"Model with params:\n\ttask = {body.task}\n\tmodel_name = {body.model_name}\nalready exists")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Model with this params already exists"
        )
    ModelService.add_model(body, session)
    return {"message": "Model with params:\n\ttask = {body.task}\n\tmodel_name = {body.model_name}\n added successfully."}