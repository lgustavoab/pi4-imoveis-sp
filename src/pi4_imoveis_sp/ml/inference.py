import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline

from pi4_imoveis_sp.ml.production import (
    METADATA_FILE,
    MODEL_FILE,
)


def validate_artifact_file(
    path: Path,
    artifact_name: str,
) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{artifact_name} não encontrado: {path}")


def load_production_model(
    path: Path = MODEL_FILE,
) -> Pipeline:
    validate_artifact_file(
        path,
        "Modelo de produção",
    )

    model = joblib.load(path)

    if not isinstance(model, Pipeline):
        raise TypeError("O artefato carregado não é um Pipeline do Scikit-learn.")

    return model


def load_model_metadata(
    path: Path = METADATA_FILE,
) -> dict:
    validate_artifact_file(
        path,
        "Arquivo de metadados",
    )

    return json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )


def predict_apartment_price(
    area: float,
    cep4: str,
    iptu_pattern: int,
    property_age: int,
    ideal_fraction: float,
    model: Pipeline | None = None,
) -> float:
    if model is None:
        model = load_production_model()

    input_data = pd.DataFrame(
        [
            {
                "Área Construída (m2)": area,
                "cep4": cep4,
                "Padrão (IPTU)": iptu_pattern,
                "idade_imovel": property_age,
                "Fração Ideal": ideal_fraction,
            }
        ]
    )

    prediction = model.predict(input_data)

    return float(prediction[0])
