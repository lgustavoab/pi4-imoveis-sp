from dataclasses import dataclass

from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    mean_absolute_error,
    r2_score,
    root_mean_squared_error,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor

from pi4_imoveis_sp.ml.dataset import (
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    NUMERICAL_FEATURES_WITHOUT_MONTH,
)
from pi4_imoveis_sp.ml.split import build_selection_split


@dataclass(frozen=True)
class XGBoostMetrics:
    mae: float
    rmse: float
    r2: float


def build_preprocessor(
    include_month: bool = True,
) -> ColumnTransformer:
    categorical_transformer = OneHotEncoder(
        handle_unknown="infrequent_if_exist",
        min_frequency=10,
    )

    numerical_features = (
        NUMERICAL_FEATURES if include_month else NUMERICAL_FEATURES_WITHOUT_MONTH
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
                list(numerical_features),
            ),
        ],
        remainder="drop",
    )


def build_xgboost_pipeline(
    include_month: bool = True,
) -> Pipeline:
    model = XGBRegressor(
        objective="reg:squarederror",
        n_estimators=500,
        learning_rate=0.05,
        max_depth=6,
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
                    include_month=include_month,
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
) -> XGBoostMetrics:
    return XGBoostMetrics(
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


def run_xgboost(
    include_month: bool = True,
) -> XGBoostMetrics:
    split = build_selection_split(
        include_month=include_month,
    )

    x_train = split.x_train.to_pandas()
    y_train = split.y_train.to_numpy()

    x_validation = split.x_validation.to_pandas()
    y_validation = split.y_validation.to_numpy()

    pipeline = build_xgboost_pipeline(
        include_month=include_month,
    )

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
