from dataclasses import dataclass

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_absolute_error,
    r2_score,
    root_mean_squared_error,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from pi4_imoveis_sp.ml.dataset import (
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
)
from pi4_imoveis_sp.ml.split import build_selection_split


@dataclass(frozen=True)
class RegressionMetrics:
    mae: float
    rmse: float
    r2: float


@dataclass(frozen=True)
class BaselineResults:
    dummy: RegressionMetrics
    linear: RegressionMetrics


def build_preprocessor() -> ColumnTransformer:
    categorical_transformer = OneHotEncoder(
        handle_unknown="infrequent_if_exist",
        min_frequency=10,
    )

    numerical_transformer = StandardScaler()

    return ColumnTransformer(
        transformers=[
            (
                "categorical",
                categorical_transformer,
                list(CATEGORICAL_FEATURES),
            ),
            (
                "numerical",
                numerical_transformer,
                list(NUMERICAL_FEATURES),
            ),
        ],
        remainder="drop",
    )


def calculate_metrics(
    y_true,
    y_pred,
) -> RegressionMetrics:
    return RegressionMetrics(
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


def build_linear_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "preprocessor",
                build_preprocessor(),
            ),
            (
                "model",
                LinearRegression(),
            ),
        ]
    )


def run_baselines() -> BaselineResults:
    split = build_selection_split()

    x_train = split.x_train.to_pandas()
    y_train = split.y_train.to_numpy()

    x_validation = split.x_validation.to_pandas()
    y_validation = split.y_validation.to_numpy()

    dummy_model = DummyRegressor(
        strategy="median",
    )

    dummy_model.fit(
        x_train,
        y_train,
    )

    dummy_predictions = dummy_model.predict(
        x_validation,
    )

    linear_model = build_linear_pipeline()

    linear_model.fit(
        x_train,
        y_train,
    )

    linear_predictions = linear_model.predict(
        x_validation,
    )

    return BaselineResults(
        dummy=calculate_metrics(
            y_validation,
            dummy_predictions,
        ),
        linear=calculate_metrics(
            y_validation,
            linear_predictions,
        ),
    )
