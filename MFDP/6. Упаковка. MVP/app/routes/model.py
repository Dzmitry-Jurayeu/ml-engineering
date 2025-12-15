from fastapi import APIRouter, Body, HTTPException, status, Depends
from database.database import get_session
from routes.api_models import ModelIn, ModelOut
from typing import List
from services.crud import model as ModelService
from loguru import logger
from models.model import Model

model_route = APIRouter()


@model_route.get("/", summary="Get all models", response_model=List[ModelOut])
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


@model_route.get("/id/{model_id}", summary="Get model by ID", response_model=ModelOut)
async def retrieve_model_by_id(model_id: int, session=Depends(get_session)) -> ModelOut:
    try:
        models = ModelService.get_model_by_id(model_id, session)
        if models is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model with ID {model_id} not found"
            )
        return models
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with ID {model_id} not found"
        )
    except Exception as e:
        logger.error(f"Error retrieving model with ID {model_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving model with ID {model_id}"
        )


@model_route.get("/params", summary="Get model by params", response_model=ModelOut)
async def retrieve_model_by_params(version: int = 1, path: str = "./ml/AutogluonModels/ag-20251205_150250",
                                   session=Depends(get_session)) -> ModelOut:
    try:
        model = ModelService.get_model_by_params(session, version, path)
        if model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model with params:\n\tversion = {version}\n\tpath = {path},\nnot found"
            )
        return model
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with params:\n\tversion = {version}\n\tpath = {path},\nnot found"
        )
    except Exception as e:
        logger.error(f"Error retrieving model with params:\n\tversion = {version}\n\tpath = {path}\n {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving model with params:\n\tversion = {version}\n\tpath = {path}"
        )

@model_route.post("/new_model", summary="Add new model",)
async def create_new_model(body: ModelIn = Body(...), session=Depends(get_session)) -> dict:

    if ModelService.get_model_by_params(session, body.version, body.path):
        logger.warning(f"Model with params:\n\tversion = {body.version}\n\tpath = {body.path}\nalready exists")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Model with this params already exists"
        )
    ModelService.add_model(Model(**body.model_dump()), session)
    return {"message": f"Model with params:\n\tversion = {body.version}\n\tpath = {body.path}\n added successfully."}