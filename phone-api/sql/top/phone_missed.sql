SELECT localid, room, SUM(count) AS count
FROM (
  SELECT localid, room, SUM(count) AS count
  FROM (
    SELECT
    	m.localid,
    	m.room,
    	m.remotenr,
    	MAX(count) AS count
    FROM
      missed m
    WHERE
      m.datetime BETWEEN datetime('now', 'start of month') AND datetime('now', 'localtime')
    GROUP BY
  	  m.localid, m.remotenr
    UNION
    SELECT
    	mp.localid,
    	mp.room,
    	mp.remotenr,
  	  MAX(count)*-1 AS count
    FROM
  	  missed mp
    WHERE
  	  mp.datetime < datetime('now', 'start of month')
      --AND mp.localid || '_' || mp.remotenr IN (SELECT localid || '_' || remotenr FROM missed WHERE datetime BETWEEN datetime('now', 'start of month') AND datetime('now', 'localtime'))
    GROUP BY
  	  mp.localid, mp.remotenr
  )
  GROUP BY localid, remotenr
)

WHERE count > 0
GROUP BY localid
ORDER BY count DESC
LIMIT 10;
