"""Real SQL over an in-memory DataFrame, via DuckDB — no server, no schema
migration, register the frame as a view and query it."""

import duckdb
import pandas as pd

from app.modules.data_analyst.schemas import SqlQueryResponse


def run_sql(df: pd.DataFrame, sql: str) -> SqlQueryResponse:
    con = duckdb.connect(database=":memory:")
    con.register("dataset", df)
    try:
        result = con.execute(sql).fetchdf()
    finally:
        con.close()

    return SqlQueryResponse(
        columns=list(result.columns),
        rows=result.astype(object).where(result.notna(), None).values.tolist(),
        row_count=len(result),
    )
