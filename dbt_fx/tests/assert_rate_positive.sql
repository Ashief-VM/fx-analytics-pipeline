-- Returns rows that FAIL. dbt expects 0 rows. Any row = test fails.
SELECT rate_key, rate_date, currency_pair, exchange_rate
FROM {{ ref('fct_exchange_rates') }}
WHERE exchange_rate <= 0
