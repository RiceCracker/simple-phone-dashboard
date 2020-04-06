SELECT localid, room, count(*) AS count FROM received GROUP BY localid ORDER BY count(*) DESC LIMIT 10;
