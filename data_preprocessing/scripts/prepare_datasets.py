from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = ROOT_DIR / "Database"
OUTPUT_DIR = ROOT_DIR / "data_preprocessing" / "outputs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare project datasets for model training, fast pipeline testing, and graph analysis."
    )
    parser.add_argument(
        "--dataset",
        choices=["ieee_full", "ieee_sample", "paysim_graph"],
        required=True,
        help="Dataset workflow to run.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Directory containing the raw datasets.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Optional row sample size. Use 0 or omit to process full data for the selected flow.",
    )
    parser.add_argument(
        "--missing-threshold",
        type=float,
        default=0.85,
        help="Drop columns above this missing-value ratio for IEEE workflows.",
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

    for column in optimized.select_dtypes(include=["float64"]).columns:
        optimized[column] = pd.to_numeric(optimized[column], downcast="float")

    for column in optimized.select_dtypes(include=["int64"]).columns:
        optimized[column] = pd.to_numeric(optimized[column], downcast="integer")

    return optimized


def build_profile(
    df: pd.DataFrame,
    label_column: str | None,
    dataset_name: str,
    dataset_role: str,
) -> dict:
    missing_ratio = df.isna().mean().sort_values(ascending=False)
    label_rate = None
    if label_column and label_column in df.columns:
        label_rate = float(df[label_column].mean())

    return {
        "dataset_name": dataset_name,
        "dataset_role": dataset_role,
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "label_column": label_column,
        "label_rate": label_rate,
        "numeric_columns": int(len(df.select_dtypes(include=[np.number]).columns)),
        "categorical_columns": int(len(df.select_dtypes(exclude=[np.number]).columns)),
        "top_missing_columns": [
            {"column": column, "missing_ratio": round(float(ratio), 4)}
            for column, ratio in missing_ratio.head(20).items()
        ],
    }


def ensure_output_dirs(dataset_name: str) -> dict[str, Path]:
    dataset_dir = OUTPUT_DIR / dataset_name
    processed_dir = dataset_dir / "processed"
    profiles_dir = dataset_dir / "profiles"
    graph_dir = dataset_dir / "graph"

    for directory in (processed_dir, profiles_dir, graph_dir):
        directory.mkdir(parents=True, exist_ok=True)

    return {
        "root": dataset_dir,
        "processed": processed_dir,
        "profiles": profiles_dir,
        "graph": graph_dir,
    }


def sample_dataframe(
    df: pd.DataFrame, sample_size: int | None, random_state: int, sort_column: str | None = None
) -> pd.DataFrame:
    if sample_size is None or sample_size == 0 or sample_size >= len(df):
        sampled = df.copy()
    else:
        sampled = df.sample(n=sample_size, random_state=random_state)

    if sort_column and sort_column in sampled.columns:
        sampled = sampled.sort_values(sort_column)

    return sampled.reset_index(drop=True)


def add_ieee_features(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()

    if {"TransactionDT", "TransactionAmt"}.issubset(enriched.columns):
        seconds_per_hour = 60 * 60
        seconds_per_day = 24 * seconds_per_hour
        enriched["transaction_hour"] = (enriched["TransactionDT"] // seconds_per_hour % 24).astype(
            "int16"
        )
        enriched["transaction_day"] = (enriched["TransactionDT"] // seconds_per_day).astype("int32")
        enriched["log_transaction_amt"] = np.log1p(enriched["TransactionAmt"]).astype("float32")

    if {"TransactionAmt", "card1"}.issubset(enriched.columns):
        card_mean = enriched.groupby("card1")["TransactionAmt"].transform("mean")
        card_std = enriched.groupby("card1")["TransactionAmt"].transform("std")
        enriched["card1_amount_mean_diff"] = (enriched["TransactionAmt"] - card_mean).astype(
            "float32"
        )
        enriched["card1_amount_zscore"] = (
            (enriched["TransactionAmt"] - card_mean) / card_std.replace(0, np.nan)
        ).astype("float32")

    if {"TransactionAmt", "ProductCD"}.issubset(enriched.columns):
        product_mean = enriched.groupby("ProductCD")["TransactionAmt"].transform("mean")
        enriched["product_amount_ratio"] = (
            enriched["TransactionAmt"] / product_mean.replace(0, np.nan)
        ).astype("float32")

    if {"P_emaildomain", "R_emaildomain"}.issubset(enriched.columns):
        enriched["email_domain_match"] = (
            enriched["P_emaildomain"].fillna("missing")
            == enriched["R_emaildomain"].fillna("missing")
        ).astype("int8")

    if {"addr1", "addr2"}.issubset(enriched.columns):
        enriched["has_full_address"] = (
            enriched["addr1"].notna() & enriched["addr2"].notna()
        ).astype("int8")

    if {"DeviceType", "DeviceInfo"}.issubset(enriched.columns):
        enriched["device_info_missing"] = enriched["DeviceInfo"].isna().astype("int8")
        enriched["is_mobile_device"] = (
            enriched["DeviceType"].fillna("").str.lower().eq("mobile")
        ).astype("int8")

    return enriched


def clean_ieee_dataframe(df: pd.DataFrame, missing_threshold: float) -> tuple[pd.DataFrame, list[str]]:
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

    working_df = optimize_dtypes(working_df)
    return working_df, dropped_columns


def run_ieee_workflow(
    data_dir: Path,
    output_dirs: dict[str, Path],
    workflow_name: str,
    dataset_role: str,
    sample_size: int | None,
    missing_threshold: float,
    random_state: int,
) -> None:
    transaction_path = data_dir / "train_transaction.csv"
    identity_path = data_dir / "train_identity.csv"

    if not transaction_path.exists() or not identity_path.exists():
        raise FileNotFoundError(
            "IEEE-CIS workflow expects train_transaction.csv and train_identity.csv."
        )

    transaction_df = pd.read_csv(transaction_path)
    identity_df = pd.read_csv(identity_path)

    transaction_df = sample_dataframe(
        transaction_df,
        sample_size=sample_size,
        random_state=random_state,
        sort_column="TransactionID",
    )
    merged_df = transaction_df.merge(identity_df, on="TransactionID", how="left")
    merged_df = optimize_dtypes(merged_df)

    raw_profile = build_profile(
        merged_df,
        label_column="isFraud",
        dataset_name=workflow_name,
        dataset_role=dataset_role,
    )
    raw_profile["sample_size"] = int(sample_size) if sample_size else 0

    enriched_df = add_ieee_features(merged_df)
    cleaned_df, dropped_columns = clean_ieee_dataframe(enriched_df, missing_threshold)

    cleaned_profile = build_profile(
        cleaned_df,
        label_column="isFraud",
        dataset_name=workflow_name,
        dataset_role=dataset_role,
    )
    cleaned_profile["sample_size"] = int(sample_size) if sample_size else 0
    cleaned_profile["missing_threshold"] = missing_threshold
    cleaned_profile["dropped_column_count"] = len(dropped_columns)
    cleaned_profile["dropped_columns"] = dropped_columns

    processed_path = output_dirs["processed"] / f"{workflow_name}_processed.csv"
    raw_profile_path = output_dirs["profiles"] / f"{workflow_name}_raw_profile.json"
    cleaned_profile_path = output_dirs["profiles"] / f"{workflow_name}_cleaned_profile.json"

    cleaned_df.to_csv(processed_path, index=False)
    raw_profile_path.write_text(json.dumps(raw_profile, indent=2), encoding="utf-8")
    cleaned_profile_path.write_text(json.dumps(cleaned_profile, indent=2), encoding="utf-8")

    print(f"Processed dataset saved to: {processed_path}")
    print(f"Raw profile saved to: {raw_profile_path}")
    print(f"Cleaned profile saved to: {cleaned_profile_path}")
    print(
        f"Summary: rows={cleaned_df.shape[0]}, columns={cleaned_df.shape[1]}, "
        f"fraud_rate={cleaned_profile['label_rate']:.4f}"
    )


def prepare_paysim_graph_features(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()
    prepared["type"] = prepared["type"].fillna("UNKNOWN")
    prepared["log_amount"] = np.log1p(prepared["amount"]).astype("float32")
    prepared["origin_balance_delta"] = (
        prepared["oldbalanceOrg"] - prepared["newbalanceOrig"]
    ).astype("float32")
    prepared["destination_balance_delta"] = (
        prepared["newbalanceDest"] - prepared["oldbalanceDest"]
    ).astype("float32")
    prepared["is_cashout"] = prepared["type"].eq("CASH_OUT").astype("int8")
    prepared["is_transfer"] = prepared["type"].eq("TRANSFER").astype("int8")
    prepared["account_pair"] = prepared["nameOrig"] + "->" + prepared["nameDest"]
    return optimize_dtypes(prepared)


def build_paysim_graph_artifacts(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    edge_df = (
        df.groupby(["nameOrig", "nameDest"], as_index=False)
        .agg(
            transaction_count=("step", "count"),
            total_amount=("amount", "sum"),
            fraud_count=("isFraud", "sum"),
            flagged_count=("isFlaggedFraud", "sum"),
            first_step=("step", "min"),
            last_step=("step", "max"),
        )
        .rename(columns={"nameOrig": "source", "nameDest": "target"})
    )

    source_nodes = df[["nameOrig", "oldbalanceOrg", "newbalanceOrig"]].rename(
        columns={
            "nameOrig": "node_id",
            "oldbalanceOrg": "balance_before",
            "newbalanceOrig": "balance_after",
        }
    )
    destination_nodes = df[["nameDest", "oldbalanceDest", "newbalanceDest"]].rename(
        columns={
            "nameDest": "node_id",
            "oldbalanceDest": "balance_before",
            "newbalanceDest": "balance_after",
        }
    )
    node_df = pd.concat([source_nodes, destination_nodes], ignore_index=True)
    node_df = (
        node_df.groupby("node_id", as_index=False)
        .agg(
            observations=("node_id", "count"),
            avg_balance_before=("balance_before", "mean"),
            avg_balance_after=("balance_after", "mean"),
        )
        .sort_values("node_id")
        .reset_index(drop=True)
    )

    return optimize_dtypes(edge_df), optimize_dtypes(node_df)


def run_paysim_workflow(
    data_dir: Path,
    output_dirs: dict[str, Path],
    sample_size: int | None,
    random_state: int,
) -> None:
    paysim_path = data_dir / "paysim dataset.csv"
    if not paysim_path.exists():
        raise FileNotFoundError("PaySim workflow expects paysim dataset.csv.")

    paysim_df = pd.read_csv(paysim_path)
    paysim_df = sample_dataframe(
        paysim_df,
        sample_size=sample_size,
        random_state=random_state,
        sort_column="step",
    )
    prepared_df = prepare_paysim_graph_features(paysim_df)
    edge_df, node_df = build_paysim_graph_artifacts(prepared_df)

    prepared_profile = build_profile(
        prepared_df,
        label_column="isFraud",
        dataset_name="paysim_graph",
        dataset_role="graph-based fraud detection and relationship analysis",
    )
    prepared_profile["sample_size"] = int(sample_size) if sample_size else 0
    prepared_profile["node_count"] = int(node_df.shape[0])
    prepared_profile["edge_count"] = int(edge_df.shape[0])

    processed_path = output_dirs["processed"] / "paysim_graph_transactions_processed.csv"
    edge_path = output_dirs["graph"] / "paysim_graph_edges.csv"
    node_path = output_dirs["graph"] / "paysim_graph_nodes.csv"
    profile_path = output_dirs["profiles"] / "paysim_graph_profile.json"

    prepared_df.to_csv(processed_path, index=False)
    edge_df.to_csv(edge_path, index=False)
    node_df.to_csv(node_path, index=False)
    profile_path.write_text(json.dumps(prepared_profile, indent=2), encoding="utf-8")

    print(f"Processed transactions saved to: {processed_path}")
    print(f"Graph edge list saved to: {edge_path}")
    print(f"Graph node summary saved to: {node_path}")
    print(f"Profile saved to: {profile_path}")
    print(
        f"Summary: rows={prepared_df.shape[0]}, nodes={node_df.shape[0]}, "
        f"edges={edge_df.shape[0]}, fraud_rate={prepared_profile['label_rate']:.4f}"
    )


def main() -> None:
    args = parse_args()

    if args.dataset == "ieee_full":
        output_dirs = ensure_output_dirs("ieee_cis")
        run_ieee_workflow(
            data_dir=args.data_dir,
            output_dirs=output_dirs,
            workflow_name="ieee_cis_full_train",
            dataset_role="core knowledge base for model training and feature engineering",
            sample_size=0,
            missing_threshold=args.missing_threshold,
            random_state=args.random_state,
        )
        return

    if args.dataset == "ieee_sample":
        output_dirs = ensure_output_dirs("ieee_cis")
        run_ieee_workflow(
            data_dir=args.data_dir,
            output_dirs=output_dirs,
            workflow_name="ieee_cis_dev_sample",
            dataset_role="fast end-to-end pipeline development and debugging",
            sample_size=args.sample_size or 10000,
            missing_threshold=args.missing_threshold,
            random_state=args.random_state,
        )
        return

    output_dirs = ensure_output_dirs("paysim")
    run_paysim_workflow(
        data_dir=args.data_dir,
        output_dirs=output_dirs,
        sample_size=args.sample_size or 50000,
        random_state=args.random_state,
    )


if __name__ == "__main__":
    main()
