import uuid
from pathlib import Path

import pandas as pd

from app.config import settings
from app.modules.recommendations.mf import MatrixFactorizationModel

_STORE_DIR = Path(settings.data_dir) / "recommendations"

_interactions: dict[str, pd.DataFrame] = {}
_models: dict[str, MatrixFactorizationModel] = {}


def register_interactions(df: pd.DataFrame) -> str:
    dataset_id = str(uuid.uuid4())
    _interactions[dataset_id] = df
    _STORE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(_STORE_DIR / f"{dataset_id}.csv", index=False)
    return dataset_id


def get_interactions(dataset_id: str) -> pd.DataFrame | None:
    if dataset_id in _interactions:
        return _interactions[dataset_id]
    csv_path = _STORE_DIR / f"{dataset_id}.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        _interactions[dataset_id] = df
        return df
    return None


def set_model(dataset_id: str, model: MatrixFactorizationModel) -> None:
    _models[dataset_id] = model


def get_model(dataset_id: str) -> MatrixFactorizationModel | None:
    return _models.get(dataset_id)
