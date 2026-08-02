"""Feature Engineering skill: lag features, rolling statistics, and
calendar features — the standard inputs to a classical forecasting model,
exposed directly so they can be inspected/reused independent of forecasting."""

import pandas as pd


def engineer_features(df: pd.DataFrame, date_col: str, value_col: str) -> pd.DataFrame:
    ts = df[[date_col, value_col]].copy()
    ts[date_col] = pd.to_datetime(ts[date_col])
    ts = ts.sort_values(date_col).reset_index(drop=True)

    ts["lag_1"] = ts[value_col].shift(1)
    ts["lag_7"] = ts[value_col].shift(7)
    ts["rolling_mean_7"] = ts[value_col].rolling(window=7, min_periods=1).mean()
    ts["day_of_week"] = ts[date_col].dt.dayofweek
    ts["month"] = ts[date_col].dt.month

    return ts
