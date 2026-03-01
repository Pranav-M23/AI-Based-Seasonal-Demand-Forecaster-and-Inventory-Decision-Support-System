import pandas as pd
import numpy as np

def to_dt(x):
    return pd.to_datetime(x, errors="coerce")

def safe_float(x, default=np.nan):
    try:
        if pd.isna(x):
            return default
        s = str(x).strip().replace(" ", "").replace("%", "")
        return float(s)
    except:
        return default

def pick_col(df: pd.DataFrame, candidates: list[str]):
    cols = list(df.columns)
    lower_map = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None

def norm_region(x: str) -> str:
    if pd.isna(x):
        return "Pan-India"
    s = str(x).strip().replace("_", " ").replace("-", " ")
    s = " ".join(s.split())
    mapping = {
        "pan india": "Pan-India",
        "panindia": "Pan-India",
        "north india": "North-India",
        "north": "North-India",
        "west india": "West-India",
        "west": "West-India",
        "east india": "East-India",
        "east": "East-India",
        "tamilnadu": "Tamil Nadu",
        "tamil nadu": "Tamil Nadu",
        "kerala": "Kerala",
    }
    return mapping.get(s.lower(), s)

def week_start_monday(dt_series: pd.Series) -> pd.Series:
    d = pd.to_datetime(dt_series, errors="coerce")
    return (d - pd.to_timedelta(d.dt.weekday, unit="D")).dt.normalize()
