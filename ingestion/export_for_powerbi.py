"""
export_for_powerbi.py — Exports mart tables to CSV for Power BI.
Run after dbt build: python ingestion/export_for_powerbi.py
"""
import duckdb
from pathlib import Path
 
WAREHOUSE  = Path('data/warehouse/fx.duckdb')
EXPORT_DIR = Path('data/exports')
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
 
con = duckdb.connect(str(WAREHOUSE))
print('Exporting mart tables for Power BI...')
 
# Try prod schema first, fall back to dev schema
schemas_to_try = ['dev_marts', 'prod_marts', 'dev']
tables = ['fct_exchange_rates', 'dim_currencies', 'kpi_monthly_summary']
 
for table in tables:
    exported = False
    for schema in schemas_to_try:
        try:
            out = EXPORT_DIR / f'{table}.csv'
            con.execute(f"COPY {schema}.{table} TO '{out}' (HEADER, DELIMITER ',')")
            count = con.execute(f'SELECT COUNT(*) FROM {schema}.{table}').fetchone()[0]
            print(f'  {table}: {count:,} rows -> {out}')
            exported = True
            break
        except Exception:
            continue
    if not exported:
        print(f'  WARNING: Could not export {table} — run dbt build first')
 
con.close()
print('Export complete. Open data/exports/ in Power BI.')
