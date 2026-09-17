from dataclasses import dataclass

import numpy as np
import polars as pl
from sklearn.metrics import (
    mean_absolute_error,
    r2_score,
    root_mean_squared_error,
)
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor

from pi4_imoveis_sp.ml.dataset import (
    FEATURE_COLUMNS_WITHOUT_MONTH,
    TARGET_COLUMN,
    build_model_dataset,
)
from pi4_imoveis_sp.ml.split import build_temporal_partitions
from pi4_imoveis_sp.ml.xgboost_model import build_preprocessor

EXPECTED_TRAIN_ROWS = 57_709
EXPECTED_TEST_ROWS = 5_431


@dataclass(frozen=True)
class FinalMetrics:
    mae: float
    rmse: float
    r2: float


@dataclass(frozen=True)
class FinalEvaluation:
    metrics: FinalMetrics
    train_rows: int
    test_rows: int
    y_test: np.ndarray
    predictions: np.ndarray
    test_data: pl.DataFrame
    pipeline: Pipeline


def build_final_pipeline() -> Pipeline:
    model = XGBRegressor(
        objective="reg:squarederror",
        max_depth=8,
        learning_rate=0.05,
        n_estimators=800,
        min_child_weight=1,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=1.0,
        tree_method="hist",
        random_state=42,
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            (
                "preprocessor",
                build_preprocessor(
                    include_month=False,
                ),
            ),
            (
                "model",
                model,
            ),
        ]
    )


def calculate_metrics(
    y_true,
    y_pred,
) -> FinalMetrics:
    return FinalMetrics(
        mae=float(
            mean_absolute_error(
                y_true,
                y_pred,
            )
        ),
        rmse=float(
            root_mean_squared_error(
                y_true,
                y_pred,
            )
        ),
        r2=float(
            r2_score(
                y_true,
                y_pred,
            )
        ),
    )


def run_final_evaluation() -> FinalEvaluation:
    dataframe = build_model_dataset(
        exclude_severe_anomalies=True,
        include_month=False,
    )

    partitions = build_temporal_partitions(dataframe)

    train = pl.concat(
        [
            partitions.train,
            partitions.validation,
        ]
    )

    test = partitions.test

    if train.height != EXPECTED_TRAIN_ROWS:
        raise ValueError(
            f"Quantidade inesperada no treino final: "
            f"{train.height:,}. "
            f"Esperado: {EXPECTED_TRAIN_ROWS:,}."
        )

    if test.height != EXPECTED_TEST_ROWS:
        raise ValueError(
            f"Quantidade inesperada no teste final: "
            f"{test.height:,}. "
            f"Esperado: {EXPECTED_TEST_ROWS:,}."
        )

    x_train = train.select(FEATURE_COLUMNS_WITHOUT_MONTH).to_pandas()

    y_train = train.get_column(TARGET_COLUMN).to_numpy()

    x_test = test.select(FEATURE_COLUMNS_WITHOUT_MONTH).to_pandas()

    y_test = test.get_column(TARGET_COLUMN).to_numpy()

    pipeline = build_final_pipeline()

    pipeline.fit(
        x_train,
        y_train,
    )

    predictions = pipeline.predict(
        x_test,
    )

    metrics = calculate_metrics(
        y_test,
        predictions,
    )

    return FinalEvaluation(
        metrics=metrics,
        train_rows=train.height,
        test_rows=test.height,
        y_test=y_test,
        predictions=predictions,
        test_data=test,
        pipeline=pipeline,
    )
