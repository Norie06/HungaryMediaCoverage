import pandas as pd

def load_json_to_dataframe(json_path: str) -> pd.DataFrame:
    """Load a JSON file into a pandas DataFrame."""
    try:
        df = pd.read_json(json_path, encoding="utf-8")
        print(f"Loaded {len(df)} records from {json_path}")
        return df
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return pd.DataFrame()

load_json_to_dataframe("./articles/telex.json")
load_json_to_dataframe("./articles/444.json")
load_json_to_dataframe("./articles/24hu.json")
load_json_to_dataframe("./articles/magyarnemzet.json")
load_json_to_dataframe("./articles/origo.json")
load_json_to_dataframe("./articles/mandiner.json")

