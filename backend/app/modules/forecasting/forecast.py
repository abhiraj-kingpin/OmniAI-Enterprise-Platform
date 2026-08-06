"""Classical time series forecasting: ETS and ARIMA (statsmodels, always
available) plus Prophet when it's installed.

No LSTM/Transformer forecaster here — those need PyTorch, and this host's
Smart App Control policy blocks PyTorch's unsigned DLLs outright (see
app/modules/rag/models.py for the full story). ETS/ARIMA/Prophet cover the
"Time Series" and "Prophet" skills for real; the deep-learning forecasters
are the one part of this module's skill list that's out of reach here.
"""

import numpy as np
import pandas as pd

from app.modules.forecasting.schemas import ForecastPoint


def _prepare_series(df: pd.DataFrame, date_col: str, value_col: str) -> pd.Series:
    ts = df[[date_col, value_col]].dropna().copy()
    ts[date_col] = pd.to_datetime(ts[date_col])
    ts = ts.sort_values(date_col)
    series = pd.Series(ts[value_col].values, index=pd.DatetimeIndex(ts[date_col]))
    inferred = pd.infer_freq(series.index)
    return series.asfreq(inferred or "D").interpolate()


def _future_dates(last_date: pd.Timestamp, freq: str, horizon: int) -> pd.DatetimeIndex:
    return pd.date_range(last_date, periods=horizon + 1, freq=freq)[1:]


def _forecast_ets(series: pd.Series, horizon: int) -> list[ForecastPoint]:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    use_seasonal = len(series) >= 14
    model = ExponentialSmoothing(
        series,
        trend="add",
        seasonal="add" if use_seasonal else None,
        seasonal_periods=7 if use_seasonal else None,
    ).fit()

    point_forecast = model.forecast(horizon)
    residual_std = float(np.std(model.resid))
    future_idx = _future_dates(series.index[-1], series.index.freq or "D", horizon)

    return [
        ForecastPoint(
            date=d.date().isoformat(),
            forecast=float(v),
            lower=float(v - 1.96 * residual_std * ((i + 1) ** 0.5)),
            upper=float(v + 1.96 * residual_std * ((i + 1) ** 0.5)),
        )
        for i, (d, v) in enumerate(zip(future_idx, point_forecast, strict=True))
    ]


def _forecast_arima(series: pd.Series, horizon: int) -> list[ForecastPoint]:
    from statsmodels.tsa.arima.model import ARIMA

    model = ARIMA(series, order=(2, 1, 2)).fit()
    result = model.get_forecast(horizon)
    mean = result.predicted_mean
    ci = result.conf_int(alpha=0.05)

    return [
        ForecastPoint(
            date=idx.date().isoformat(),
            forecast=float(mean.iloc[i]),
            lower=float(ci.iloc[i, 0]),
            upper=float(ci.iloc[i, 1]),
        )
        for i, idx in enumerate(mean.index)
    ]


def _forecast_prophet(series: pd.Series, horizon: int) -> list[ForecastPoint]:
    try:
        from prophet import Prophet
    except ImportError as exc:
        raise RuntimeError(
            "Prophet isn't installed. `pip install prophet` (requires a "
            "working C++ build toolchain on Windows) or use method=ets/arima."
        ) from exc

    df = pd.DataFrame({"ds": series.index, "y": series.values})
    model = Prophet()
    model.fit(df)
    future = model.make_future_dataframe(periods=horizon, freq=series.index.freq or "D")
    forecast = model.predict(future).tail(horizon)

    return [
        ForecastPoint(
            date=row.ds.date().isoformat(),
            forecast=float(row.yhat),
            lower=float(row.yhat_lower),
            upper=float(row.yhat_upper),
        )
        for row in forecast.itertuples()
    ]


_METHODS = {"ets": _forecast_ets, "arima": _forecast_arima, "prophet": _forecast_prophet}


def run_forecast(
    df: pd.DataFrame, date_col: str, value_col: str, horizon: int, method: str
) -> tuple[list[ForecastPoint], int]:
    series = _prepare_series(df, date_col, value_col)
    if method not in _METHODS:
        raise ValueError(f"Unknown method '{method}'. Choose from: {list(_METHODS)}")
    return _METHODS[method](series, horizon), len(series)
