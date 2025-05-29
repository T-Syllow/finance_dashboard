import pandas as pd

data_folder = "newData/"
transaction_data = pd.read_csv(data_folder + "cleaned_transaction_data.csv", sep=",",  encoding="utf8", parse_dates=['date'])
print(transaction_data.columns)

 # Alle Händler 
merchant_id = transaction_data['merchant_id'].unique()


# Umsatz Gesamt
revenue_per_merchant = transaction_data.groupby('merchant_id')['amount'].sum().rename('gesamtumsatz')

# Durchschnittliche Transaktionshöhe
avg_transaction = transaction_data.groupby('merchant_id')['amount'].mean().rename('avg_transaction')

# Anzahl der Niederlassungen
niederlassungen_per_merchant = (
    transaction_data.groupby('merchant_id')
    .apply(lambda g: g[['merchant_city', 'merchant_state']].drop_duplicates().shape[0], include_groups=False)
    .rename('niederlassungen')
)


# Jahr extrahieren
transaction_data['year'] = transaction_data['date'].dt.year

# Umsatz pro Jahr und merchant
revenue_yearly = (
    transaction_data.groupby(['merchant_id', 'year'])['amount']
    .sum()
    .unstack(fill_value=0)
)


# zusammenführen
merchant_stats = (
    revenue_per_merchant
    .to_frame()
    .join(avg_transaction)
    .join(niederlassungen_per_merchant)
    
    .reset_index()
)

# Umbenennen und Runden für Darstellung
merchant_stats.columns = [
    "merchant_id", "revenue", "avg_transaction", "niederlassungen"
]
merchant_stats = merchant_stats.round(1)


output_path = "C:/Users/skugl/Documents/HFT/WIP2/finance_dashboard/merchant_stats.csv"

merchant_stats.to_csv(output_path, index=False, encoding="utf8")
print(f"Berechnete CSV gespeichert unter: {output_path}")