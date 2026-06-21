from pathlib import Path
import pandas as pd
from pipeline.export.csv_export import export_csv


def export_excel(path: str = "data/exports/sample_sentiment.xlsx") -> str:
    csv_path = export_csv("data/exports/.tmp_sample.csv")
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.read_csv(csv_path).to_excel(out, index=False)
    return str(out)
