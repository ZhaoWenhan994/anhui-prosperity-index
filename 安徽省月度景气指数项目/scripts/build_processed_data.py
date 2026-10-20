from __future__ import annotations

from pathlib import Path

import pandas as pd

from anhui_index.importer import import_manifest
from anhui_index.preprocess import build_monthly_table, write_processed_table


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "metadata" / "raw_file_manifest.csv"
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "data" / "processed" / "anhui_monthly_indicators.csv"


def main() -> None:
    records = import_manifest(MANIFEST, RAW)
    table = build_monthly_table(records)
    output = write_processed_table(table, OUTPUT)
    complete = int(table["quality_flag"].eq("ok").sum())
    print(
        f"output={output} months={len(table)} records={len(records)} "
        f"complete_months={complete} missing_months={len(table) - complete}"
    )


if __name__ == "__main__":
    main()
