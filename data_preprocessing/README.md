# Data Preprocessing Module

This module now follows the multi-dataset strategy for the fraud detection system instead of treating preprocessing as a single generic step.

## Dataset Strategy

- `IEEE-CIS Fraud Detection`: main knowledge base for feature engineering and training the core fraud models such as Random Forest and XGBoost
- `IEEE-CIS 10k sample`: lightweight development dataset for quickly testing the full pipeline from ingestion to scoring
- `PaySim`: graph-oriented dataset for building sender-receiver relationships for the GNN or network analysis layer

## Folder Layout

- `scripts/`: preprocessing and dataset preparation scripts
- `outputs/ieee_cis/processed/`: prepared IEEE datasets
- `outputs/ieee_cis/profiles/`: IEEE data profiles
- `outputs/paysim/processed/`: prepared PaySim transaction records
- `outputs/paysim/graph/`: graph-ready node and edge files for NetworkX or PyTorch Geometric
- `outputs/paysim/profiles/`: PaySim data profiles
- `logs/`: reserved for future logs

## Main Script

Use the staged dataset preparation script:

```powershell
.\setup_venv.ps1
.\.venv\Scripts\Activate.ps1
python data_preprocessing/scripts/prepare_datasets.py --dataset ieee_sample
```

## Workflow Commands

Prepare the main IEEE-CIS training dataset:

```powershell
python data_preprocessing/scripts/prepare_datasets.py --dataset ieee_full
```

Prepare the IEEE-CIS development sample:

```powershell
python data_preprocessing/scripts/prepare_datasets.py --dataset ieee_sample --sample-size 10000
```

Prepare the PaySim graph dataset:

```powershell
python data_preprocessing/scripts/prepare_datasets.py --dataset paysim_graph --sample-size 50000
```

## What Each Workflow Produces

### IEEE-CIS Full

- merged transaction and identity data
- starter feature engineering
- missing-value treatment
- cleaned training-ready dataset
- raw and cleaned data profiles

### IEEE-CIS Sample

- smaller processed version of the IEEE data
- intended for API, Kafka, model, and scoring pipeline debugging
- faster iteration with the same schema style as the main dataset

### PaySim Graph

- cleaned transaction-level PaySim data
- graph edge list built from `nameOrig -> nameDest`
- node summary table for account-level graph construction
- profile report including node and edge counts

## Notes

- The default raw dataset directory is `Database/`
- Project dependencies are defined in the root [requirements.txt](C:/Users/HP/Desktop/SEM%206/CNS/CP/requirements.txt)
- Run [setup_venv.ps1](C:/Users/HP/Desktop/SEM%206/CNS/CP/setup_venv.ps1) once to create the project `.venv` and install dependencies
- Optional advanced GNN packages are listed in [requirements-gnn.txt](C:/Users/HP/Desktop/SEM%206/CNS/CP/requirements-gnn.txt)
- The earlier `preprocess_ieee_cis.py` file is kept as the initial prototype
- The new `prepare_datasets.py` script is the main entry point for the project data layer
- Next, we can build train-validation splits, encoding pipelines, feature stores, and graph feature generation on top of this structure
