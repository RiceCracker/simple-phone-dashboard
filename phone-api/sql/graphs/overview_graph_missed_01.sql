SELECT
	strftime('%Y', datetime) AS year,
	strftime('%m', datetime) AS month,
	count(*)                 AS count
FROM missed
GROUP BY year, month
