from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = ROOT_DIR / "Database"
OUTPUT_DIR = ROOT_DIR / "data_preprocessing" / "outputs"
PROFILE_DIR = OUTPUT_DIR / "profiles"
PROCESSED_DIR = OUTPUT_DIR / "processed"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preprocess the IEEE-CIS fraud detection training dataset."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Directory containing train_transaction.csv and train_identity.csv",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=50000,
        help="Number of rows to sample from train_transaction.csv before merge. Use 0 for full data.",
    )
    parser.add_argument(
        "--missing-threshold",
        type=float,
        default=0.85,
        help="Drop columns with missing ratio above this threshold.",
    )
    parser.add_argument(
        "--output-prefix",
        default="ieee_cis_train",
        help="Prefix used for generated output files.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducible sampling.",
    )
    return parser.parse_args()


def optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    optimized = df.copy()

    float_columns = optimized.select_dtypes(include=["float64"]).columns
    int_columns = optimized.select_dtypes(include=["int64"]).columns

    for column in float_columns:
        optimized[column] = pd.to_numeric(optimized[column], downcast="float")

    for column in int_columns:
        optimized[column] = pd.to_numeric(optimized[column], downcast="integer")

    return optimized


def build_profile(df: pd.DataFrame, label_column: str) -> dict:
    missing_ratio = df.isna().mean().sort_values(ascending=False)
    fraud_rate = None
    if label_column in df.columns:
        fraud_rate = float(df[label_column].mean())

    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "fraud_rate": fraud_rate,
        "numeric_columns": int(len(df.select_dtypes(include=[np.number]).columns)),
        "categorical_columns": int(len(df.select_dtypes(exclude=[np.number]).columns)),
        "top_missing_columns": [
            {"column": column, "missing_ratio": round(float(ratio), 4)}
            for column, ratio in missing_ratio.head(20).items()
        ],
    }


def add_starter_features(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()

    if {"TransactionAmt", "card1"}.issubset(enriched.columns):
        card_amount_mean = enriched.groupby("card1")["TransactionAmt"].transform("mean")
        card_amount_std = enriched.groupby("card1")["TransactionAmt"].transform("std")
        enriched["card1_txn_amt_mean_diff"] = (
            enriched["TransactionAmt"] - card_amount_mean
        ).astype("float32")
        enriched["card1_txn_amt_zscore"] = (
            (enriched["TransactionAmt"] - card_amount_mean) / card_amount_std.replace(0, np.nan)
        ).astype("float32")

    if {"TransactionAmt", "ProductCD"}.issubset(enriched.columns):
        product_amount_mean = enriched.groupby("ProductCD")["TransactionAmt"].transform("mean")
        enriched["product_txn_amt_ratio"] = (
            enriched["TransactionAmt"] / product_amount_mean.replace(0, np.nan)
        ).astype("float32")

    if {"addr1", "addr2"}.issubset(enriched.columns):
        enriched["has_full_address"] = (
            enriched["addr1"].notna() & enriched["addr2"].notna()
        ).astype("int8")

    if {"DeviceType", "DeviceInfo"}.issubset(enriched.columns):
        enriched["device_info_missing"] = enriched["DeviceInfo"].isna().astype("int8")
        enriched["is_mobile_device"] = (
            enriched["DeviceType"].fillna("").str.lower().eq("mobile")
        ).astype("int8")

    if {"P_emaildomain", "R_emaildomain"}.issubset(enriched.columns):
        enriched["email_domain_match"] = (
            enriched["P_emaildomain"].fillna("missing")
            == enriched["R_emaildomain"].fillna("missing")
        ).astype("int8")

    if "TransactionDT" in enriched.columns:
        seconds_per_day = 24 * 60 * 60
        enriched["transaction_day"] = (
            enriched["TransactionDT"] // seconds_per_day
        ).astype("int32")

    return enriched


def clean_dataframe(df: pd.DataFrame, missing_threshold: float) -> tuple[pd.DataFrame, list[str]]:
    working_df = df.copy()
    missing_ratio = working_df.isna().mean()
    dropped_columns = missing_ratio[missing_ratio > missing_threshold].index.tolist()
    working_df = working_df.drop(columns=dropped_columns)

    numeric_columns = working_df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_columns = working_df.select_dtypes(exclude=[np.number]).columns.tolist()

    if numeric_columns:
        working_df[numeric_columns] = working_df[numeric_columns].fillna(
            working_df[numeric_columns].median()
        )

    for column in categorical_columns:
        working_df[column] = working_df[column].fillna("missing")

    return working_df, dropped_columns


def main() -> None:
    args = parse_args()
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    transaction_path = args.data_dir / "train_transaction.csv"
    identity_path = args.data_dir / "train_identity.csv"

    if not transaction_path.exists() or not identity_path.exists():
        raise FileNotFoundError(
            "Expected train_transaction.csv and train_identity.csv in the provided data directory."
        )

    transaction_df = pd.read_csv(transaction_path)
    identity_df = pd.read_csv(identity_path)

    if args.sample_size and args.sample_size > 0 and args.sample_size < len(transaction_df):
        transaction_df = transaction_df.sample(
            n=args.sample_size,
            random_state=args.random_state,
        ).sort_values("TransactionID")

    merged_df = transaction_df.merge(identity_df, on="TransactionID", how="left")
    merged_df = optimize_dtypes(merged_df)

    raw_profile = build_profile(merged_df, label_column="isFraud")
    raw_profile["sample_size"] = int(args.sample_size)

    enriched_df = add_starter_features(merged_df)
    cleaned_df, dropped_columns = clean_dataframe(
        enriched_df, missing_threshold=args.missing_threshold
    )
    cleaned_df = optimize_dtypes(cleaned_df)

    cleaned_profile = build_profile(cleaned_df, label_column="isFraud")
    cleaned_profile["dropped_columns"] = dropped_columns
    cleaned_profile["dropped_column_count"] = len(dropped_columns)
    cleaned_profile["missing_threshold"] = args.missing_threshold

    processed_csv = PROCESSED_DIR / f"{args.output_prefix}_processed.csv"
    raw_profile_json = PROFILE_DIR / f"{args.output_prefix}_raw_profile.json"
    cleaned_profile_json = PROFILE_DIR / f"{args.output_prefix}_cleaned_profile.json"

    cleaned_df.to_csv(processed_csv, index=False)
    raw_profile_json.write_text(json.dumps(raw_profile, indent=2), encoding="utf-8")
    cleaned_profile_json.write_text(json.dumps(cleaned_profile, indent=2), encoding="utf-8")

    print(f"Processed dataset saved to: {processed_csv}")
    print(f"Raw profile saved to: {raw_profile_json}")
    print(f"Cleaned profile saved to: {cleaned_profile_json}")
    fraud_rate_text = (
        f"{cleaned_profile['fraud_rate']:.4f}"
        if cleaned_profile["fraud_rate"] is not None
        else "n/a"
    )
    print(
        "Summary: "
        f"rows={cleaned_df.shape[0]}, "
        f"columns={cleaned_df.shape[1]}, "
        f"fraud_rate={fraud_rate_text}"
    )


if __name__ == "__main__":
    main()
