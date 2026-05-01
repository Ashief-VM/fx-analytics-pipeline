# extract_daily.py — Called by Airflow every weekday at 08:00 UTC.
#Fetches previous day's exchange rates and appends to DuckDB.
#Idempotent: safe to run multiple times for the same date.
#Test manually: python ingestion/extract_daily.py 2025-01-15

import requests, duckdb, pandas as pd, sys, logging
from datetime import date, timedelta
from pathlib import Path
 
logging.basicConfig(level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)
 
WAREHOUSE = Path('/opt/airflow/data/warehouse/fx.duckdb')
if not WAREHOUSE.parent.exists():
    WAREHOUSE = Path('data/warehouse/fx.duckdb')
 
BASE_CURRENCIES   = ['EUR', 'USD', 'INR']
TARGET_CURRENCIES = 'GBP,JPY,CHF,CAD,AUD,CNY,BRL,SEK,NOK,DKK,MXN,SGD,HKD'
API_BASE          = 'https://api.frankfurter.app'
 
def fetch_rates(target_date):
    rows = []
    loaded_at = pd.Timestamp.utcnow()
    for base in BASE_CURRENCIES:
        url = f'{API_BASE}/{target_date}'
        params = {'from': base, 'to': TARGET_CURRENCIES}
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 404:
                log.info(f'No data for {target_date} — weekend or holiday')
                return []
            resp.raise_for_status()
            data = resp.json()
            for target, rate in data['rates'].items():
                if target == base: continue
                rows.append({'rate_date': date.fromisoformat(data['date']),
                             'base_currency': base, 'target_currency': target,
                             'exchange_rate': float(rate), 'loaded_at': loaded_at})
        except requests.RequestException as e:
            log.error(f'API failed for {base}: {e}')
            raise
    return rows
 
def load(rows, target_date):
    if not rows:
        log.info('No rows to load')
        return 0
    con = duckdb.connect(str(WAREHOUSE))
    # Idempotent: delete then re-insert
    con.execute('DELETE FROM raw.raw_fx_rates WHERE rate_date = ?', [target_date])
    df = pd.DataFrame(rows)
    con.register('_batch', df)
    con.execute('''
        INSERT INTO raw.raw_fx_rates
        SELECT CAST(rate_date AS DATE), base_currency, target_currency,
               exchange_rate, CAST(loaded_at AS TIMESTAMP) FROM _batch
    ''')
    count = con.execute('SELECT COUNT(*) FROM raw.raw_fx_rates WHERE rate_date = ?',
                        [target_date]).fetchone()[0]
    con.close()
    return count
 
def main(target_date=None):
    if target_date is None:
        target_date = date.today() - timedelta(days=1)
    log.info(f'Extracting FX rates for {target_date}')
    rows = fetch_rates(target_date)
    count = load(rows, target_date)
    log.info(f'Done. {count} rows loaded for {target_date}')
    return count
 
if __name__ == '__main__':
    d = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today() - timedelta(days=1)
    main(d)
