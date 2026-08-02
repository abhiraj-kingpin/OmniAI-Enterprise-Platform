"""Real PySpark job, local[*] master — no cluster needed to run this one,
just a JVM (PySpark ships as a pip package, but the Spark engine itself
runs on the JVM via py4j). Not runnable on this host: no Java Runtime
installed (`java -version` fails). On a host with a JDK, `local[*]` alone
is enough — no separate Spark cluster required, only a real multi-node
`spark://master:7077` deployment needs one.

Sketches Spark's fit in this platform: batch-scoring the Recommendation
System's item catalog, or aggregating the Forecasting module's historical
datasets, at a scale pandas/duckdb (used in app/modules/data_analyst) stop
being the right tool for.
"""


def check_available() -> None:
    import shutil

    if shutil.which("java") is None:
        raise RuntimeError(
            "PySpark needs a Java Runtime — none found on PATH (`java -version` "
            "fails on this host). Install a JDK (e.g. `winget install "
            "Microsoft.OpenJDK.21`) to run this."
        )
    try:
        import pyspark  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("pyspark isn't installed (`pip install pyspark`).") from exc


def aggregate_revenue_by_region(rows: list[dict]) -> list[dict]:
    """rows: [{"region": str, "revenue": float}, ...] — mirrors the shape
    app/modules/data_analyst accepts, run through Spark instead of DuckDB."""
    check_available()

    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F

    spark = SparkSession.builder.appName("omniai-revenue-aggregation").master("local[*]").getOrCreate()
    try:
        df = spark.createDataFrame(rows)
        result = df.groupBy("region").agg(F.sum("revenue").alias("total_revenue"))
        return [row.asDict() for row in result.collect()]
    finally:
        spark.stop()
