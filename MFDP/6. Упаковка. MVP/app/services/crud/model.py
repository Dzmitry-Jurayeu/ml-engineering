from models.model import Model
from typing import List, Optional
from autogluon.tabular import TabularPredictor


def get_all_models(session) -> List[Model]:
    return session.query(Model).all()


def get_model_by_id(id: int, session) -> Optional[Model]:
    models = session.get(Model, id)
    if models:
        return models
    return None


def add_model(new_model: Model, session) -> None:
    model = get_model_by_params(session, new_model.version, new_model.path)
    if model:
        return None
    session.add(new_model)
    session.commit()
    session.refresh(new_model)


def get_model_by_params(
        session,
        version: int = 1,
        path: str = "./ml/AutogluonModels/ag-20251205_150250"
) -> Optional[Model]:
    model = session.query(Model).filter(
        Model.version == version,
        Model.path == path
    ).first()
    if model:
        return model
    return None


def init_model(model: Model):
    return TabularPredictor.load(model.path)
