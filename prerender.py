import pandas as pd
import os

# Verzeichnisse und Dateinamen
parquet_folder = "./parquet_data/"
transaction_file = os.path.join(parquet_folder, "cleaned_transactions_data.parquet")
output_file = os.path.join(parquet_folder, "gesamt_ausgaben_pro_client.parquet")

# Lade nur die benötigten Spalten für die Gesamtausgaben pro Kunde
df = pd.read_parquet(transaction_file, columns=['client_id', 'amount', 'date'])

# Gruppiere und berechne die Gesamtausgaben pro Kunde
gesamt_ausgaben = df.groupby("client_id")["amount"].sum().reset_index()
gesamt_ausgaben.rename(columns={"amount": "gesamt_ausgaben"}, inplace=True)

# Speichere das Ergebnis als Parquet
gesamt_ausgaben.to_parquet(output_file, compression='snappy', index=False)
print(f"✅ Gesamtausgaben pro Kunde gespeichert unter: {output_file}")

# Jahresweise Aufteilung
df['year'] = pd.to_datetime(df['date']).dt.year

for year in df['year'].unique():
    year_file = os.path.join(parquet_folder, f"transactions_{year}.parquet")
    df[df['year'] == year].to_parquet(year_file, compression='snappy', index=False)
    print(f"✅ Transaktionen für {year} gespeichert unter: {year_file}")