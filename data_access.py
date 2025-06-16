import pandas as pd

def load_transactions(filepath, start_date, end_date, mcc=None, merchant_id=None):
    df = pd.read_parquet(filepath)
    df['date'] = pd.to_datetime(df['date'])
    mask = (df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))
    if mcc is not None:
        mask &= (df['mcc'] == int(mcc))
    if merchant_id is not None:
        mask &= (df['merchant_id'] == int(merchant_id))
    filtered = df[mask]
    return filtered.reset_index(drop=True)