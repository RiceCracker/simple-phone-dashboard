SELECT
		"dialed"
	AS type,
		(SELECT count(*) FROM dialed WHERE datetime BETWEEN datetime('now', 'start of month', '$PENULTIMATE month') AND datetime('now', 'start of month', '$PREVIOUS month'))
	AS penultimate_month,
		(SELECT count(*) FROM dialed WHERE datetime BETWEEN datetime('now', 'start of month', '$PREVIOUS month') AND datetime('now', 'start of month', '$CURRENT month'))
	AS last_month,
		count(*)
	AS current_month
		FROM dialed WHERE datetime BETWEEN datetime('now', 'start of month', '$CURRENT month') AND datetime('now', 'start of month', '$NEXT month')
UNION
SELECT
		"received"
	AS type,
		(SELECT count(*) FROM received WHERE datetime BETWEEN datetime('now', 'start of month', '$PENULTIMATE month') AND datetime('now', 'start of month', '$PREVIOUS month'))
	AS penultimate_month,
		(SELECT count(*) FROM received WHERE datetime BETWEEN datetime('now', 'start of month', '$PREVIOUS month') AND datetime('now', 'start of month', '$CURRENT month'))
	AS last_month,
		count(*)
	AS current_month
		FROM received WHERE datetime BETWEEN datetime('now', 'start of month', '$CURRENT month') AND datetime('now', 'start of month', '$NEXT month')
UNION
SELECT
		"missed"
	AS type,
		(SELECT SUM(count) AS count
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
		      m.datetime BETWEEN datetime('now', 'start of month', '$PENULTIMATE month') AND datetime('now', 'start of month', '$PREVIOUS month')
		    GROUP BY
		  	  m.localid, m.remotenr
		    UNION
		    SELECT
		    	mp.localid,
		    	mp.room,
		    	mp.remotenr,
		  	  MAX(count)*$PREVIOUS AS count
		    FROM
		  	  missed mp
		    WHERE
		  	  mp.datetime < datetime('now', 'start of month', '$PENULTIMATE month')
		      --AND mp.localid || '_' || mp.remotenr IN (SELECT localid || '_' || remotenr FROM missed WHERE datetime BETWEEN datetime('now', 'start of month') AND datetime('now', 'localtime'))
		    GROUP BY
		  	  mp.localid, mp.remotenr
		  )
		  GROUP BY localid, remotenr
		)

		WHERE count > 0
		ORDER BY count DESC
	)
	AS penultimate_month,
		(SELECT SUM(count) AS count
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
		      m.datetime BETWEEN datetime('now', 'start of month', '$PREVIOUS month') AND datetime('now', 'start of month', '$CURRENT month')
		    GROUP BY
		  	  m.localid, m.remotenr
		    UNION
		    SELECT
		    	mp.localid,
		    	mp.room,
		    	mp.remotenr,
		  	  MAX(count)*$PREVIOUS AS count
		    FROM
		  	  missed mp
		    WHERE
		  	  mp.datetime < datetime('now', 'start of month', '$PREVIOUS month')
		      --AND mp.localid || '_' || mp.remotenr IN (SELECT localid || '_' || remotenr FROM missed WHERE datetime BETWEEN datetime('now', 'start of month') AND datetime('now', 'localtime'))
		    GROUP BY
		  	  mp.localid, mp.remotenr
		  )
		  GROUP BY localid, remotenr
		)

		WHERE count > 0
		ORDER BY count DESC
		)
	AS last_month,
		(SELECT SUM(count) AS count
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
		      m.datetime BETWEEN datetime('now', 'start of month', '$CURRENT month') AND datetime('now', 'start of month', '$NEXT month')
		    GROUP BY
		  	  m.localid, m.remotenr
		    UNION
		    SELECT
		    	mp.localid,
		    	mp.room,
		    	mp.remotenr,
		  	  MAX(count)*$PREVIOUS AS count
		    FROM
		  	  missed mp
		    WHERE
		  	  mp.datetime < datetime('now', 'start of month', '$CURRENT month')
		      --AND mp.localid || '_' || mp.remotenr IN (SELECT localid || '_' || remotenr FROM missed WHERE datetime BETWEEN datetime('now', 'start of month') AND datetime('now', 'localtime'))
		    GROUP BY
		  	  mp.localid, mp.remotenr
		  )
		  GROUP BY localid, remotenr
		)

		WHERE count > 0
		ORDER BY count DESC
		)
	AS current_month

;
