from pi4_imoveis_sp.ml.dataset import FEATURE_COLUMNS
from pi4_imoveis_sp.ml.split import build_temporal_split


EXPECTED_TRAIN_ROWS = 52_911
EXPECTED_VALIDATION_ROWS = 4_930
EXPECTED_TEST_ROWS = 5_966
EXPECTED_TOTAL_ROWS = 63_807


def main() -> None:
    print("=" * 80)
    print("VALIDAÇÃO DO SPLIT TEMPORAL")
    print("=" * 80)

    split = build_temporal_split()

    train_rows = split.x_train.height
    validation_rows = split.x_validation.height
    test_rows = split.x_test.height

    print("\n1. TAMANHOS")
    print("-" * 80)

    print(f"Treino:     {train_rows:,}")
    print(f"Validação:  {validation_rows:,}")
    print(f"Teste:      {test_rows:,}")
    print(f"Total:      {train_rows + validation_rows + test_rows:,}")

    if train_rows != EXPECTED_TRAIN_ROWS:
        raise ValueError(f"Treino inesperado: {train_rows:,}")

    if validation_rows != EXPECTED_VALIDATION_ROWS:
        raise ValueError(f"Validação inesperada: {validation_rows:,}")

    if test_rows != EXPECTED_TEST_ROWS:
        raise ValueError(f"Teste inesperado: {test_rows:,}")

    total = train_rows + validation_rows + test_rows

    if total != EXPECTED_TOTAL_ROWS:
        raise ValueError(f"Total inesperado: {total:,}")

    print("\n2. FEATURES")
    print("-" * 80)

    print(split.x_train.columns)

    if tuple(split.x_train.columns) != FEATURE_COLUMNS:
        raise ValueError("As features do treino diferem do contrato definido.")

    if tuple(split.x_validation.columns) != FEATURE_COLUMNS:
        raise ValueError("As features da validação diferem do contrato definido.")

    if tuple(split.x_test.columns) != FEATURE_COLUMNS:
        raise ValueError("As features do teste diferem do contrato definido.")

    print("Contrato de features preservado.")

    print("\n3. TARGET")
    print("-" * 80)

    print(f"y_train:      {len(split.y_train):,}")
    print(f"y_validation: {len(split.y_validation):,}")
    print(f"y_test:       {len(split.y_test):,}")

    print("\n" + "=" * 80)
    print("SPLIT TEMPORAL VALIDADO COM SUCESSO")
    print("=" * 80)


if __name__ == "__main__":
    main()
