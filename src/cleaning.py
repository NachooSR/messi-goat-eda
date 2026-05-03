from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "messi_all_goals.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CLEAN_PATH = PROCESSED_DIR / "messi_goals_clean.csv"

BIRTH_DATE = pd.Timestamp("1987-06-24")
EXCLUDED_COMPETITIONS = {"2ª B - Grupo III"}


def _normalize_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    text_columns = df.select_dtypes(include="object").columns
    df[text_columns] = df[text_columns].apply(lambda col: col.str.strip())
    return df


def _minute_period(minute: int) -> str:
    if minute <= 23:
        return "1/4: 0-23"
    if minute <= 45:
        return "2/4: 24-45"
    if minute <= 68:
        return "3/4: 46-68"
    return "4/4: 69-90+"


def load_raw_goals(path: Path = RAW_PATH) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def clean_goals(df: pd.DataFrame) -> pd.DataFrame:
    clean = df.copy()
    clean = _normalize_text_columns(clean)

    clean["date"] = pd.to_datetime(clean["date"], errors="raise")
    clean["year"] = clean["date"].dt.year
    clean["month"] = clean["date"].dt.month
    clean["age"] = ((clean["date"] - BIRTH_DATE).dt.days // 365).astype(int)
    clean["minute_period"] = clean["goal_minute"].apply(_minute_period)

    clean["is_home_goal"] = clean["venue"].eq("Home")

    clean = clean[~clean["competition"].isin(EXCLUDED_COMPETITIONS)].copy()
    clean = clean[(clean["year"] > 2005) & (clean["year"] < 2026)].copy()

    cols_to_drop = ["goal_decade", "goal_minute_bucket"]
    clean = clean.drop(columns=cols_to_drop, errors="ignore")
    clean = clean.sort_values(["date", "goal_minute", "opponent"]).reset_index(drop=True)
    return clean


def save_clean_goals(df: pd.DataFrame, path: Path = CLEAN_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def run_cleaning() -> pd.DataFrame:
    clean = clean_goals(load_raw_goals())
    save_clean_goals(clean)
    return clean


if __name__ == "__main__":
    result = run_cleaning()
    print(f"Dataset limpio guardado en {CLEAN_PATH}")
    print(f"Filas: {len(result)} | Columnas: {len(result.columns)}")
