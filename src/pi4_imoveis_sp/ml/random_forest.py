from dataclasses import dataclass

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    r2_score,
    root_mean_squared_error,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from pi4_imoveis_sp.ml.dataset import (
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
)
from pi4_imoveis_sp.ml.split import build_selection_split


@dataclass(frozen=True)
class RandomForestMetrics:
    mae: float
    rmse: float
    r2: float


def build_preprocessor() -> ColumnTransformer:
    categorical_transformer = OneHotEncoder(
        handle_unknown="infrequent_if_exist",
        min_frequency=10,
    )

    return ColumnTransformer(
        transformers=[
            (
                "categorical",
                categorical_transformer,
                list(CATEGORICAL_FEATURES),
            ),
            (
                "numerical",
                "passthrough",
                list(NUMERICAL_FEATURES),
            ),
        ],
        remainder="drop",
    )


def build_random_forest_pipeline() -> Pipeline:
    model = RandomForestRegressor(
        n_estimators=200,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            (
                "preprocessor",
                build_preprocessor(),
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
) -> RandomForestMetrics:
    return RandomForestMetrics(
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


def run_random_forest() -> RandomForestMetrics:
    split = build_selection_split()

    x_train = split.x_train.to_pandas()
    y_train = split.y_train.to_numpy()

    x_validation = split.x_validation.to_pandas()
    y_validation = split.y_validation.to_numpy()

    pipeline = build_random_forest_pipeline()

    pipeline.fit(
        x_train,
        y_train,
    )

    predictions = pipeline.predict(
        x_validation,
    )

    return calculate_metrics(
        y_validation,
        predictions,
    )
