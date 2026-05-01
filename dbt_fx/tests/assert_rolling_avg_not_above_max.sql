-- Rolling average cannot exceed the rolling max.
SELECT rate_key, currency_pair, rolling_30d_avg, rolling_30d_max
FROM {{ ref('fct_exchange_rates') }}
WHERE rolling_30d_avg IS NOT NULL
  AND rolling_30d_max IS NOT NULL
  AND ROUND(rolling_30d_avg, 4) > ROUND(rolling_30d_max, 4)
