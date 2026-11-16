from pathlib import Path
from typing import Dict

from diffprivlib.mechanisms import Laplace


def duckdb_summary(path: Path) -> Dict[str, float]:
    import duckdb

    result = duckdb.sql(
        "SELECT COUNT(*) AS rows, "
        "COUNT(DISTINCT city) AS cities, "
        "COALESCE(SUM(CAST(orders AS DOUBLE)), 0) AS total_orders "
        f"FROM read_csv_auto('{path.as_posix()}')"
    ).fetchall()[0]
    return {"rows": result[0], "cities": result[1], "total_orders": result[2]}


def private_total(value: float, epsilon: float = 1.0, sensitivity: float = 1.0) -> float:
    return max(0.0, float(Laplace(epsilon=epsilon, sensitivity=sensitivity).randomise(value)))
