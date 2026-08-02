"""In-memory dataset registry, backed by CSV files on disk so uploads
survive a restart. One process, one DataFrame per dataset — fine at the
scale this module targets (ad-hoc analysis of a spreadsheet, not a
warehouse).
"""

import io
import uuid
from pathlib import Path

import pandas as pd

from app.config import settings

_STORE_DIR = Path(settings.data_dir) / "data_analyst"
_datasets: dict[str, tuple[str, pd.DataFrame]] = {}  # id -> (filename, df)


def _read_any(filename: str, content: bytes) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()
    buf = io.BytesIO(content)
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(buf)
    if suffix == ".csv":
        return pd.read_csv(buf)
    if suffix == ".json":
        return pd.read_json(buf)
    raise ValueError(f"Unsupported dataset file type: {suffix}")


def register_dataset(filename: str, content: bytes) -> tuple[str, pd.DataFrame]:
    df = _read_any(filename, content)
    dataset_id = str(uuid.uuid4())
    _datasets[dataset_id] = (filename, df)

    _STORE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(_STORE_DIR / f"{dataset_id}.csv", index=False)
    (_STORE_DIR / f"{dataset_id}.meta").write_text(filename, encoding="utf-8")

    return dataset_id, df


def get_dataset(dataset_id: str) -> tuple[str, pd.DataFrame] | None:
    if dataset_id in _datasets:
        return _datasets[dataset_id]

    csv_path = _STORE_DIR / f"{dataset_id}.csv"
    meta_path = _STORE_DIR / f"{dataset_id}.meta"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        filename = meta_path.read_text(encoding="utf-8") if meta_path.exists() else dataset_id
        _datasets[dataset_id] = (filename, df)
        return _datasets[dataset_id]

    return None


def list_datasets() -> list[tuple[str, str, pd.DataFrame]]:
    if _STORE_DIR.exists():
        for csv_path in _STORE_DIR.glob("*.csv"):
            dataset_id = csv_path.stem
            if dataset_id not in _datasets:
                get_dataset(dataset_id)
    return [(did, fname, df) for did, (fname, df) in _datasets.items()]
