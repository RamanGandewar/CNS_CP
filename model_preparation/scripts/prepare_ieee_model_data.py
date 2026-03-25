from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PATH = (
    ROOT_DIR / "data_preprocessing" / "outputs" / "ieee_cis" / "processed" / "ieee_cis_dev_sample_processed.csv"
)
OUTPUT_DIR = ROOT_DIR / "model_preparation" / "outputs" / "datasets"
REPORT_DIR = ROOT_DIR / "model_preparation" / "outputs" / "reports"
ARTIFACT_DIR = ROOT_DIR / "model_preparation" / "artifacts"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare IEEE-CIS processed data for model training."
    )
    parser.add_argument(
        "--input-path",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help="Path to a processed IEEE-CIS CSV file.",
    )
    parser.add_argument(
        "--target-column",
        default="isFraud",
        help="Target column name.",
    )
    parser.add_argument(
        "--id-column",
        default="TransactionID",
        help="Identifier column to exclude from model features.",
    )
    parser.add_argument(
        "--validation-size",
        type=float,
        default=0.2,
        help="Validation split ratio.",
    )
    parser.add_argument(
        "--rare-threshold",
        type=float,
        default=0.005,
        help="Minimum frequency ratio required to keep a categorical value as-is.",
    )
    parser.add_argument(
        "--output-prefix",
        default="ieee_model_ready",
        help="Prefix for generated files.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed.",
    )
    return parser.parse_args()


def ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def reduce_rare_categories(
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    categorical_columns: list[str],
    rare_threshold: float,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, list[str]]]:
    train_copy = train_df.copy()
    valid_copy = valid_df.copy()
    rare_value_map: dict[str, list[str]] = {}

    for column in categorical_columns:
        frequencies = train_copy[column].fillna("missing").value_counts(normalize=True)
        rare_values = frequencies[frequencies < rare_threshold].index.tolist()
        rare_value_map[column] = rare_values

        if rare_values:
            train_copy[column] = train_copy[column].replace(rare_values, "rare")
            valid_copy[column] = valid_copy[column].replace(rare_values, "rare")

    return train_copy, valid_copy, rare_value_map


def build_preprocessor(
    numeric_columns: list[str], categorical_columns: list[str]
) -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
            (
                "encoder",
                OrdinalEncoder(
                    handle_unknown="use_encoded_value",
                    unknown_value=-1,
                    encoded_missing_value=-1,
                ),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_columns),
            ("cat", categorical_pipeline, categorical_columns),
        ],
        remainder="drop",
    )


def build_report(
    source_path: Path,
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    numeric_columns: list[str],
    categorical_columns: list[str],
    target_column: str,
    rare_value_map: dict[str, list[str]],
) -> dict:
    return {
        "source_path": str(source_path),
        "train_rows": int(train_df.shape[0]),
        "validation_rows": int(valid_df.shape[0]),
        "feature_count": int(len(numeric_columns) + len(categorical_columns)),
        "numeric_feature_count": int(len(numeric_columns)),
        "categorical_feature_count": int(len(categorical_columns)),
        "target_column": target_column,
        "train_fraud_rate": float(train_df[target_column].mean()),
        "validation_fraud_rate": float(valid_df[target_column].mean()),
        "rare_category_columns": int(sum(1 for values in rare_value_map.values() if values)),
        "top_rare_category_columns": [
            {"column": column, "rare_value_count": len(values)}
            for column, values in sorted(
                rare_value_map.items(), key=lambda item: len(item[1]), reverse=True
            )[:20]
            if values
        ],
    }


def main() -> None:
    args = parse_args()
    ensure_dirs()

    if not args.input_path.exists():
        raise FileNotFoundError(f"Input file not found: {args.input_path}")

    df = pd.read_csv(args.input_path)

    if args.target_column not in df.columns:
        raise ValueError(f"Target column '{args.target_column}' not found in input data.")

    feature_df = df.drop(columns=[args.target_column]).copy()
    if args.id_column in feature_df.columns:
        feature_df = feature_df.drop(columns=[args.id_column])

    target = df[args.target_column].astype("int8")

    x_train, x_valid, y_train, y_valid = train_test_split(
        feature_df,
        target,
        test_size=args.validation_size,
        stratify=target,
        random_state=args.random_state,
    )

    numeric_columns = x_train.select_dtypes(include=[np.number]).columns.tolist()
    categorical_columns = x_train.select_dtypes(exclude=[np.number]).columns.tolist()

    x_train, x_valid, rare_value_map = reduce_rare_categories(
        x_train,
        x_valid,
        categorical_columns=categorical_columns,
        rare_threshold=args.rare_threshold,
    )

    preprocessor = build_preprocessor(
        numeric_columns=numeric_columns,
        categorical_columns=categorical_columns,
    )

    x_train_transformed = preprocessor.fit_transform(x_train)
    x_valid_transformed = preprocessor.transform(x_valid)

    feature_names = numeric_columns + categorical_columns
    train_prepared_df = pd.DataFrame(x_train_transformed, columns=feature_names, index=x_train.index)
    valid_prepared_df = pd.DataFrame(x_valid_transformed, columns=feature_names, index=x_valid.index)

    train_prepared_df[args.target_column] = y_train
    valid_prepared_df[args.target_column] = y_valid

    train_output_path = OUTPUT_DIR / f"{args.output_prefix}_train.csv"
    valid_output_path = OUTPUT_DIR / f"{args.output_prefix}_validation.csv"
    artifact_path = ARTIFACT_DIR / f"{args.output_prefix}_preprocessor.joblib"
    report_path = REPORT_DIR / f"{args.output_prefix}_report.json"

    train_prepared_df.to_csv(train_output_path, index=False)
    valid_prepared_df.to_csv(valid_output_path, index=False)
    joblib.dump(preprocessor, artifact_path)

    report = build_report(
        source_path=args.input_path,
        train_df=train_prepared_df,
        valid_df=valid_prepared_df,
        numeric_columns=numeric_columns,
        categorical_columns=categorical_columns,
        target_column=args.target_column,
        rare_value_map=rare_value_map,
    )
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Training dataset saved to: {train_output_path}")
    print(f"Validation dataset saved to: {valid_output_path}")
    print(f"Preprocessor artifact saved to: {artifact_path}")
    print(f"Preparation report saved to: {report_path}")
    print(
        f"Summary: train_rows={train_prepared_df.shape[0]}, "
        f"validation_rows={valid_prepared_df.shape[0]}, "
        f"features={len(feature_names)}"
    )


if __name__ == "__main__":
    main()
