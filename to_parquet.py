import pandas as pd
import os

# Liste deiner CSV-Dateien
csv_files = [
    'cleaned_cards_data.csv',
    'cleaned_transaction_data_500k.csv',
    'cleaned_users_data.csv'
]

# Quell- und Zielverzeichnis
data_folder = './newData'
output_dir = './parquet_data'
os.makedirs(output_dir, exist_ok=True)

# CSV → Parquet konvertieren
for csv_file in csv_files:
    print(f"Verarbeite {csv_file}...")

    # Vollständiger Pfad zur CSV-Datei
    csv_path = os.path.join(data_folder, csv_file)

    # CSV einlesen
    df = pd.read_csv(csv_path)

    # Parquet-Dateiname generieren
    parquet_file = os.path.join(output_dir, csv_file.replace('.csv', '.parquet'))

    # Speichern als Parquet
    df.to_parquet(parquet_file, compression='snappy')

    print(f"→ Gespeichert als {parquet_file}")

print("✅ Alle Dateien wurden erfolgreich konvertiert.")