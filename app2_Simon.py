import pandas as pd

data_folder = "newData/"
df = pd.read_csv(data_folder + "cleaned_transaction_data.csv", sep=",",  encoding="utf8", parse_dates=['date'])
print(df.columns)

merchant_id = df['merchant_id'].unique()

#Umsatz Gesamt 
revenue_per_merchant = df.groupby('merchant_id')['amount'].sum().rename('gesamtumsatz')

# Durchschnittliche Transaktionshöhe
avg_transaction = df.groupby('merchant_id')['amount'].mean().rename('avg_transaction')

#  Anzahl der Niederlassungen 
branches_per_merchant = (
    df.groupby('merchant_id')
    .apply(lambda g: g[['merchant_city', 'merchant_state']].drop_duplicates().shape[0])
    .rename('niederlassungen')
)

#  Umsatzwachstum berechnen

# Jahr extrahieren
df['year'] = df['date'].dt.year

# Umsatz pro Jahr und merchant
revenue_yearly = (
    df.groupby(['merchant_id', 'year'])['amount']
    .sum()
    .unstack(fill_value=0)
)

# Umsatzwachstum über verschiedene Zeiträume berechnen
revenue_growth = pd.DataFrame(index=revenue_yearly.index)

years = revenue_yearly.columns.tolist()

# Hilfsfunktion zum Wachstum berechnen
def growth(last_period, earlier_period):
    if earlier_period == 0:
        return 0
    return ((last_period - earlier_period) / earlier_period) * 100

# All Time Wachstum (zwischen letztem und erstem Jahr)
if len(years) >= 2:
    revenue_growth['growth_all_time'] = [
        growth(revenue_yearly.loc[i, years[-1]], revenue_yearly.loc[i, years[0]])
        for i in revenue_yearly.index
    ]
else:
        revenue_growth['growth_all_time'] = 0
# Wachstum 1 Jahr
if len(years) >= 2:
    revenue_growth['growth_1y'] = [
        growth(revenue_yearly.loc[i, years[-1]], revenue_yearly.loc[i, years[-2]])
        for i in revenue_yearly.index
    ]
else:
    revenue_growth['growth_1y'] = 0

# Wachstum 3 Jahre
if len(years) >= 4:
    revenue_growth['growth_3y'] = [
        growth(revenue_yearly.loc[i, years[-1]], revenue_yearly.loc[i, years[-4]])
        for i in revenue_yearly.index
    ]
else:
    revenue_growth['growth_3y'] = 0

# Wachstum 5 Jahre
if len(years) >= 6:
    revenue_growth['growth_5y'] = [
        growth(revenue_yearly.loc[i, years[-1]], revenue_yearly.loc[i, years[-6]])
        for i in revenue_yearly.index
    ]
else:
    revenue_growth['growth_5y'] = 0

# zusammenführen
merchant_stats = (
    revenue_per_merchant
    .to_frame()
    .join(avg_transaction)
    .join(branches_per_merchant)
    .join(revenue_growth)
    .reset_index()
)

print(merchant_stats.columns)
print(len(merchant_stats.columns))



# Optional: Umbenennen für Klarheit
merchant_stats.columns = [
    "merchant_id", "revenue", "avg_transaction", "branches",
    "growth_all_time", "growth_1y", "growth_3y", "growth_5y"
]



output_path = "C:/Users/skugl/Documents/HFT/WIP2/finance_dashboard/testdata.csv"

merchant_stats.to_csv(output_path, index=False, encoding="utf8")
print(f"Bereinigte CSV gespeichert unter: {output_path}")