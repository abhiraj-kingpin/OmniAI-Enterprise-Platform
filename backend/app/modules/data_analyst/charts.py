"""Chart rendering with matplotlib (Agg backend — no display needed)."""

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from app.modules.data_analyst.schemas import ChartRequest  # noqa: E402

_AGG_FUNCS = {"sum": "sum", "mean": "mean", "count": "count", "max": "max", "min": "min"}


def render_chart(df: pd.DataFrame, req: ChartRequest) -> bytes:
    if req.x not in df.columns:
        raise ValueError(f"Column '{req.x}' not found")
    if req.y and req.y not in df.columns:
        raise ValueError(f"Column '{req.y}' not found")

    fig, ax = plt.subplots(figsize=(8, 5))

    if req.chart_type == "hist":
        df[req.x].dropna().plot(kind="hist", ax=ax, bins=30)
    elif req.chart_type == "box":
        df.boxplot(column=req.y or req.x, ax=ax)
    elif req.chart_type == "scatter":
        ax.scatter(df[req.x], df[req.y])
        ax.set_xlabel(req.x)
        ax.set_ylabel(req.y)
    elif req.chart_type == "line":
        df.plot(x=req.x, y=req.y, kind="line", ax=ax)
    else:  # bar, with aggregation over x
        agg_func = _AGG_FUNCS.get(req.agg or "sum", "sum")
        grouped = df.groupby(req.x)[req.y].agg(agg_func) if req.y else df[req.x].value_counts()
        grouped.sort_values(ascending=False).head(20).plot(kind="bar", ax=ax)

    ax.set_title(req.title or f"{req.chart_type} of {req.y or req.x} by {req.x}")
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def suggest_charts(df: pd.DataFrame) -> list[dict]:
    """Auto-pick a handful of sensible charts from the dataset's schema —
    the "Dashboard Generation" skill: no user input required."""
    numeric_cols = list(df.select_dtypes(include="number").columns)
    categorical_cols = [
        c for c in df.columns if df[c].dtype == "object" and df[c].nunique() <= 30
    ]

    specs: list[dict] = []
    if categorical_cols and numeric_cols:
        specs.append(
            {
                "chart_type": "bar",
                "x": categorical_cols[0],
                "y": numeric_cols[0],
                "title": f"{numeric_cols[0]} by {categorical_cols[0]}",
            }
        )
    if len(numeric_cols) >= 1:
        specs.append(
            {
                "chart_type": "hist",
                "x": numeric_cols[0],
                "y": None,
                "title": f"Distribution of {numeric_cols[0]}",
            }
        )
    if len(numeric_cols) >= 2:
        specs.append(
            {
                "chart_type": "scatter",
                "x": numeric_cols[0],
                "y": numeric_cols[1],
                "title": f"{numeric_cols[1]} vs {numeric_cols[0]}",
            }
        )
    return specs
