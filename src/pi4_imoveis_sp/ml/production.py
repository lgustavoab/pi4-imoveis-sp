import json
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from platform import python_version

import joblib

from pi4_imoveis_sp.data.cleaning import PROJECT_ROOT
from pi4_imoveis_sp.ml.dataset import (
    CATEGORICAL_FEATURES,
    FEATURE_COLUMNS_WITHOUT_MONTH,
    NUMERICAL_FEATURES_WITHOUT_MONTH,
    TARGET_COLUMN,
    build_model_dataset,
)
from pi4_imoveis_sp.ml.final_model import build_final_pipeline

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

MODEL_FILE = ARTIFACTS_DIR / "apartment_price_model.joblib"

METADATA_FILE = ARTIFACTS_DIR / "model_metadata.json"

EXPECTED_PRODUCTION_ROWS = 63_140

FINAL_METRICS = {
    "mae": 231_947.92292769515,
    "rmse": 1_091_963.084853122,
    "r2": 0.5729976346033591,
}

FINAL_HYPERPARAMETERS = {
    "objective": "reg:squarederror",
    "max_depth": 8,
    "learning_rate": 0.05,
    "n_estimators": 800,
    "min_child_weight": 1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_lambda": 1.0,
    "tree_method": "hist",
    "random_state": 42,
    "n_jobs": -1,
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
        "project": {
            "name": "pi4-imoveis-sp",
            "version": version("pi4-imoveis-sp"),
        },
        "production_training_rows": training_rows,
        "production_training": {
            "period": {
                "start": "2025-01-01",
                "end": "2025-12-31",
            },
            "transaction_year": 2025,
            "economically_valid_records_only": True,
            "internal_holdout": False,
            "description": (
                "Modelo de produção treinado em todos os registros "
                "economicamente válidos com Data de Transação em 2025."
            ),
        },
        "target": TARGET_COLUMN,
        "features": list(FEATURE_COLUMNS_WITHOUT_MONTH),
        "categorical_features": list(CATEGORICAL_FEATURES),
        "numerical_features": list(NUMERICAL_FEATURES_WITHOUT_MONTH),
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
            "description": (
                "Avaliação temporal oficial congelada antes do treinamento "
                "do artefato de produção. Estas métricas não avaliam o modelo "
                "retreinado em todos os registros de 2025."
            ),
            "train_period": {
                "start": "2025-01-01",
                "end": "2025-11-30",
            },
            "test_period": {
                "start": "2025-12-01",
                "end": "2025-12-31",
            },
            "train_rows": 57_709,
            "test_rows": 5_431,
            "metrics": FINAL_METRICS,
        },
        "environment": {
            "python": python_version(),
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
