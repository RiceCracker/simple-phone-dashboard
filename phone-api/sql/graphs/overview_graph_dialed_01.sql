SELECT
	strftime('%Y', datetime) as year,
	strftime('%m', datetime) as month,
	count(*)                 as count
FROM dialed
GROUP BY year, month
