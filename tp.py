import pandas as pd

df = pd.read_csv("model_preparation/outputs/datasets/ieee_dev_model_ready_validation.csv")

print(df.drop(columns=["isFraud"]).iloc[0].to_dict())