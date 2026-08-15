from __future__ import annotations

from pathlib import Path
from typing import Optional
import pandas as pd


def build_summary_table(
    stage_root: str | Path,
    *,
    registry_name: str = "_registry.parquet",
    out_parquet: str = "_summary.parquet",
) -> Path:
    """
    Creates a summary table by reading the stage registry and joining per-run qa_summary.parquet if present.
    Output is written to stage_root/_summary.parquet.

    Requirements:
      - registry has a 'product_dir' column
      - each product_dir may have qa_summary.parquet (one row)
    """
    stage_root = Path(stage_root)
    reg_path = stage_root / registry_name
    if not reg_path.exists():
        raise FileNotFoundError(f"Missing registry: {reg_path}")

    reg = pd.read_parquet(reg_path)
    if reg.empty:
        out_path = stage_root / out_parquet
        reg.to_parquet(out_path, index=False)
        return out_path

    # Optional: sort newest first
    if "created_at" in reg.columns:
        reg = reg.sort_values("created_at", ascending=False).reset_index(drop=True)

    # Load qa_summary rows (0 or 1 row per run)
    metrics_rows = []
    for prod in reg["product_dir"].astype(str):
        prod_dir = Path(prod)
        # If product_dir is relative, resolve under stage_root
        abs_dir = (stage_root / prod_dir) if not prod_dir.is_absolute() else prod_dir
        qas = abs_dir / "qa_summary.parquet"
        if qas.exists():
            qdf = pd.read_parquet(qas)
            if len(qdf) >= 1:
                row = qdf.iloc[0].to_dict()
            else:
                row = {}
        else:
            row = {}
        row["_product_dir_key"] = str(prod)
        metrics_rows.append(row)

    metrics = pd.DataFrame(metrics_rows)

    # Join back
    reg2 = reg.copy()
    reg2["_product_dir_key"] = reg2["product_dir"].astype(str)

    summary = reg2.merge(metrics, on="_product_dir_key", how="left").drop(columns=["_product_dir_key"])
    out_path = stage_root / out_parquet
    summary.to_parquet(out_path, index=False)
    return out_path