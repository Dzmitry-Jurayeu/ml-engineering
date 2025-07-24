from models.model import Model
from typing import List, Optional
from transformers import pipeline


def get_all_models(session) -> List[Model]:
    return session.query(Model).all()


def get_model_by_id(id: int, session) -> Optional[Model]:
    models = session.get(Model, id)
    if models:
        return models
    return None


def add_model(new_model: Model, session) -> None:
    model = get_model_by_params(session, new_model.task, new_model.model_name)
    if model:
        return None
    session.add(new_model)
    session.commit()
    session.refresh(new_model)


def get_model_by_params(
        session,
        task: str = "text-classification",
        model_name: str = "unitary/toxic-bert",
) -> Optional[Model]:
    model = session.query(Model).filter(
        Model.task == task,
        Model.model_name == model_name
    ).first()
    if model:
        return model
    return None


def init_model(model: Model):
    return pipeline(model.task, model=model.model_name)
