import json
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import joblib

from pi4_imoveis_sp.data.cleaning import PROJECT_ROOT
from pi4_imoveis_sp.ml.dataset import (
    FEATURE_COLUMNS_WITHOUT_MONTH,
    TARGET_COLUMN,
    build_model_dataset,
)
from pi4_imoveis_sp.ml.final_model import build_final_pipeline

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

MODEL_FILE = ARTIFACTS_DIR / "apartment_price_model.joblib"

METADATA_FILE = ARTIFACTS_DIR / "model_metadata.json"

EXPECTED_PRODUCTION_ROWS = 63_140

FINAL_METRICS = {
    "mae": 228_857.12,
    "rmse": 1_044_652.29,
    "r2": 0.5890,
}

FINAL_HYPERPARAMETERS = {
    "max_depth": 8,
    "learning_rate": 0.05,
    "n_estimators": 800,
    "min_child_weight": 1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_lambda": 1.0,
    "tree_method": "hist",
    "random_state": 42,
}


def build_production_dataset():
    dataframe = build_model_dataset(
        exclude_severe_anomalies=True,
        include_month=False,
    )

    if dataframe.height != EXPECTED_PRODUCTION_ROWS:
        raise ValueError(
            "Quantidade inesperada de registros para produção: "
            f"{dataframe.height:,}. "
            f"Esperado: {EXPECTED_PRODUCTION_ROWS:,}."
        )

    x = dataframe.select(FEATURE_COLUMNS_WITHOUT_MONTH).to_pandas()

    y = dataframe.get_column(TARGET_COLUMN).to_numpy()

    return x, y


def build_metadata(
    training_rows: int,
) -> dict:
    return {
        "model_name": "XGBoost Apartment Price Estimator",
        "model_version": "1.0.0",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "training_period": {
            "start": "2025-01",
            "end": "2025-12",
        },
        "training_rows": training_rows,
        "target": TARGET_COLUMN,
        "features": list(FEATURE_COLUMNS_WITHOUT_MONTH),
        "quality_filters": {
            "purchase_and_sale_only": True,
            "apartment_use_code": 20,
            "full_transfer_only": True,
            "exclude_value_m2_below_100": True,
            "exclude_transaction_below_10_percent_vvr": True,
        },
        "model": {
            "algorithm": "XGBRegressor",
            "hyperparameters": FINAL_HYPERPARAMETERS,
        },
        "official_evaluation": {
            "train_period": "2025-01 to 2025-11",
            "test_period": "2025-12",
            "test_rows": 5_966,
            "metrics": FINAL_METRICS,
        },
        "environment": {
            "python": version("pi4-imoveis-sp"),
            "scikit_learn": version("scikit-learn"),
            "xgboost": version("xgboost"),
            "pandas": version("pandas"),
            "polars": version("polars"),
            "joblib": version("joblib"),
        },
    }


def save_metadata(
    metadata: dict,
    path: Path = METADATA_FILE,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            metadata,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def train_and_save_production_model():
    x, y = build_production_dataset()

    pipeline = build_final_pipeline()

    pipeline.fit(
        x,
        y,
    )

    ARTIFACTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        pipeline,
        MODEL_FILE,
        compress=3,
    )

    metadata = build_metadata(
        training_rows=len(x),
    )

    save_metadata(metadata)

    return pipeline, metadata
