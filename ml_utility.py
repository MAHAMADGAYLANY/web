import csv
from pathlib import Path
from typing import Dict, List


def ml_utility_report(input_path: Path, protected_path: Path) -> Dict[str, float]:
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import OneHotEncoder

    def load(path: Path) -> List[Dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as source:
            return list(csv.DictReader(source))

    def evaluate(rows: List[Dict[str, str]]) -> float:
        x = [[row["city"]] for row in rows]
        y = [float(row["orders"]) for row in rows]
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=42)
        encoder = ColumnTransformer([("city", OneHotEncoder(handle_unknown="ignore", sparse_output=False), [0])])
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(encoder.fit_transform(x_train), y_train)
        return mean_absolute_error(y_test, model.predict(encoder.transform(x_test)))

    baseline_error = evaluate(load(input_path))
    protected_error = evaluate(load(protected_path))
    return {
        "baseline_mae": round(baseline_error, 4),
        "protected_mae": round(protected_error, 4),
        "mae_change": round(protected_error - baseline_error, 4),
    }
