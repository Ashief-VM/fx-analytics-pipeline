import duckdb

con = duckdb.connect('data/warehouse/fx.duckdb')

# Delete old GBP rows
con.execute("DELETE FROM raw.raw_fx_rates WHERE base_currency = 'GBP'")

# Verify
result = con.execute("SELECT DISTINCT base_currency FROM raw.raw_fx_rates").fetchdf()
count = con.execute("SELECT COUNT(*) FROM raw.raw_fx_rates").fetchone()[0]

print("Base currencies remaining:")
print(result)
print(f"Total rows: {count:,}")

con.close()
print("Done!")