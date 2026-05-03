# This file run ONCE before the daily pipeline starts, loading 2 years of data into duckdb,

import requests, duckdb, pandas as pd
from datetime import date, timedelta
from pathlib import Path
import time

WAREHOUSE   = Path('data/warehouse/fx.duckdb')
BASE_CURRENCIES = ['EUR', 'USD', 'INR']
TARGET_CURRENCIES = 'USD,GBP,JPY,CHF,CAD,AUD,CNY,BRL,SEK,NOK,DKK,MXN,SGD,HKD'
START_DATE        = date.today() - timedelta(days=730)
END_DATE          = date.today()
API_BASE          = 'https://api.frankfurter.app'
 
def create_warehouse():
    WAREHOUSE.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(WAREHOUSE))
    con.execute('CREATE SCHEMA IF NOT EXISTS raw')
    con.execute('''
        CREATE TABLE IF NOT EXISTS raw.raw_fx_rates (
            rate_date        DATE        NOT NULL,
            base_currency    VARCHAR(3)  NOT NULL,
            target_currency  VARCHAR(3)  NOT NULL,
            exchange_rate    DOUBLE      NOT NULL,
            loaded_at        TIMESTAMP   NOT NULL,
            PRIMARY KEY (rate_date, base_currency, target_currency)
        )
    ''')
    return con
 
def fetch_range(base, start, end):
    url = f'{API_BASE}/{start}..{end}'
    params = {'from': base, 'to': TARGET_CURRENCIES}
    print(f'  Fetching {base} from {start} to {end}...')
    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code == 404:
        print('  No data for this range')
        return []
    resp.raise_for_status()
    data = resp.json()
    rows = []
    loaded_at = pd.Timestamp.utcnow()
    for rate_date_str, rates in data['rates'].items():
        for target, rate in rates.items():
            if target == base: continue
            rows.append({'rate_date': date.fromisoformat(rate_date_str),
                         'base_currency': base, 'target_currency': target,
                         'exchange_rate': float(rate), 'loaded_at': loaded_at})
    return rows
 
def insert_rows(rows, con):
    if not rows: return 0
    df = pd.DataFrame(rows)
    con.register('_batch', df)
    con.execute('''
        INSERT OR IGNORE INTO raw.raw_fx_rates
        SELECT CAST(rate_date AS DATE), base_currency, target_currency,
               exchange_rate, CAST(loaded_at AS TIMESTAMP)
        FROM _batch
    ''')
    return len(rows)
 
def main():
    print('=' * 55)
    print('FX Backfill — Loading 2 Years of Historical Data')
    print('=' * 55)
    con = create_warehouse()
    for base in BASE_CURRENCIES:
        print(f'\nBase currency: {base}')
        rows = fetch_range(base, START_DATE, END_DATE)
        n = insert_rows(rows, con)
        print(f'  -> {n:,} rows inserted')
        time.sleep(0.5)
    total = con.execute('SELECT COUNT(*) FROM raw.raw_fx_rates').fetchone()[0]
    print(f'\nDone! Total rows: {total:,}')
    con.close()
 
if __name__ == '__main__': main()
