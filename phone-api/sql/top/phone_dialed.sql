SELECT localid, room, count(*) AS count FROM dialed GROUP BY localid ORDER BY count(*) DESC LIMIT 10;
