import pandas as pd
import os

# Verzeichnisse und Dateinamen
parquet_folder = "./parquet_data/"
transaction_file = os.path.join(parquet_folder, "cleaned_transaction_data.parquet")
output_file = os.path.join(parquet_folder, "gesamt_ausgaben_pro_client.parquet")

# lade alle Spalten aus transactions main datei
df = pd.read_parquet(transaction_file)

# Gruppiere und berechne die Gesamtausgaben pro Kunde
gesamt_ausgaben = df.groupby("client_id")["amount"].sum().reset_index()
gesamt_ausgaben.rename(columns={"amount": "gesamt_ausgaben"}, inplace=True)

# Speichere das Ergebnis als Parquet
gesamt_ausgaben.to_parquet(output_file, compression='snappy', index=False)
print(f"✅ Gesamtausgaben pro Kunde gespeichert unter: {output_file}")

# Jahres- und Monatsweise Aufteilung
df['year'] = pd.to_datetime(df['date']).dt.year
df['month'] = pd.to_datetime(df['date']).dt.month

for year in df['year'].unique():
    for month in df[df['year'] == year]['month'].unique():
        ym_file = os.path.join(parquet_folder, f"transactions_{year}_{str(month).zfill(2)}.parquet")
        df[(df['year'] == year) & (df['month'] == month)].to_parquet(ym_file, compression='snappy', index=False)
        print(f"✅ Transaktionen für {year}-{str(month).zfill(2)} gespeichert unter: {ym_file}")