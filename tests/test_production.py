from importlib.metadata import version
from platform import python_version

from pi4_imoveis_sp.ml.dataset import (
    CATEGORICAL_FEATURES,
    FEATURE_COLUMNS_WITHOUT_MONTH,
    NUMERICAL_FEATURES_WITHOUT_MONTH,
)
from pi4_imoveis_sp.ml.production import (
    EXPECTED_PRODUCTION_ROWS,
    FINAL_HYPERPARAMETERS,
    FINAL_METRICS,
    build_metadata,
)


def test_metadata_separates_project_and_python_versions() -> None:
    metadata = build_metadata(EXPECTED_PRODUCTION_ROWS)

    assert metadata["project"]["version"] == version("pi4-imoveis-sp")
    assert metadata["environment"]["python"] == python_version()


def test_metadata_contains_complete_frozen_configuration() -> None:
    metadata = build_metadata(EXPECTED_PRODUCTION_ROWS)

    assert metadata["model"]["hyperparameters"] == FINAL_HYPERPARAMETERS
    assert FINAL_HYPERPARAMETERS["objective"] == "reg:squarederror"
    assert FINAL_HYPERPARAMETERS["n_jobs"] == -1


def test_metadata_contains_production_training_context() -> None:
    metadata = build_metadata(EXPECTED_PRODUCTION_ROWS)

    assert metadata["production_training_rows"] == 63_140
    assert metadata["production_training"]["transaction_year"] == 2025
    assert metadata["production_training"]["internal_holdout"] is False


def test_metadata_preserves_official_evaluation() -> None:
    metadata = build_metadata(EXPECTED_PRODUCTION_ROWS)
    evaluation = metadata["official_evaluation"]

    assert evaluation["train_rows"] == 57_709
    assert evaluation["test_rows"] == 5_431
    assert evaluation["metrics"] == FINAL_METRICS


def test_metadata_preserves_feature_contract() -> None:
    metadata = build_metadata(EXPECTED_PRODUCTION_ROWS)

    assert tuple(metadata["features"]) == FEATURE_COLUMNS_WITHOUT_MONTH
    assert tuple(metadata["categorical_features"]) == CATEGORICAL_FEATURES
    assert tuple(metadata["numerical_features"]) == NUMERICAL_FEATURES_WITHOUT_MONTH
