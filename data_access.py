import pandas as pd

def load_transactions(filepath, start_date, end_date, mcc=None, merchant_id=None, chunksize=100_000):
    result = []
    for chunk in pd.read_csv(filepath, chunksize=chunksize, parse_dates=['date']):
        mask = (chunk['date'] >= start_date) & (chunk['date'] <= end_date)
        if mcc is not None:
            mask &= (chunk['mcc'] == int(mcc))
        if merchant_id is not None:
            mask &= (chunk['merchant_id'] == int(merchant_id))
        filtered = chunk[mask]
        if not filtered.empty:
            result.append(filtered)
    if result:
        return pd.concat(result, ignore_index=True)
    return pd.DataFrame()