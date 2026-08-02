"""Statistics computation (pandas) + narrative generation (Claude)."""

import json

import anthropic
import pandas as pd

from app.modules.data_analyst.schemas import InsightsResponse


def _clean(value: float) -> float | None:
    if pd.isna(value):
        return None
    return float(value)


def compute_stats(df: pd.DataFrame) -> tuple[dict, dict, dict]:
    numeric = df.select_dtypes(include="number")

    describe = {
        col: {stat: _clean(val) for stat, val in numeric[col].describe().items()}
        for col in numeric.columns
    }
    missing = {col: int(df[col].isna().sum()) for col in df.columns}

    correlations: dict[str, dict[str, float]] = {}
    if numeric.shape[1] >= 2:
        corr = numeric.corr(numeric_only=True)
        correlations = {
            col: {other: _clean(corr.loc[col, other]) for other in corr.columns}
            for col in corr.columns
        }

    return describe, missing, correlations


async def generate_narrative(
    dataset_id: str, df: pd.DataFrame, describe: dict, missing: dict, correlations: dict
) -> str:
    summary = {
        "columns": list(df.columns),
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "row_count": len(df),
        "describe": describe,
        "missing_values": missing,
        "strong_correlations": {
            a: {b: v for b, v in row.items() if a != b and v is not None and abs(v) > 0.6}
            for a, row in correlations.items()
        },
        "sample_rows": df.head(5).to_dict(orient="records"),
    }

    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-opus-5",
        max_tokens=1024,
        system=(
            "You are a data analyst. Given dataset statistics, write a short, "
            "concrete narrative: what stands out, notable distributions or "
            "outliers, any strong correlations, and data-quality issues "
            "(missing values). Plain prose, no headers, 4-8 sentences."
        ),
        messages=[{"role": "user", "content": json.dumps(summary, default=str)}],
    )
    return next(b.text for b in response.content if b.type == "text")


async def build_insights(dataset_id: str, df: pd.DataFrame) -> InsightsResponse:
    describe, missing, correlations = compute_stats(df)
    narrative = await generate_narrative(dataset_id, df, describe, missing, correlations)
    return InsightsResponse(
        dataset_id=dataset_id,
        describe=describe,
        missing_values=missing,
        correlations=correlations,
        narrative=narrative,
    )
