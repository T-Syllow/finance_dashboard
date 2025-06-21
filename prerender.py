import pandas as pd
import os

parquet_folder = "./parquet_data/"
transaction_file = os.path.join(parquet_folder, "cleaned_transactions_data.parquet")

df = pd.read_parquet(transaction_file)

df['year'] = pd.to_datetime(df['date']).dt.year
df['month'] = pd.to_datetime(df['date']).dt.month

for year in df['year'].unique():
    for month in df[df['year'] == year]['month'].unique():
        ym_file = os.path.join(parquet_folder, f"transactions_{year}_{str(month).zfill(2)}.parquet")
        df[(df['year'] == year) & (df['month'] == month)].to_parquet(ym_file, compression='snappy', index=False)
        print(f"✅ Transaktionen für {year}-{str(month).zfill(2)} gespeichert unter: {ym_file}")