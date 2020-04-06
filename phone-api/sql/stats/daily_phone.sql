SELECT
		"dialed"
	AS type,
		(SELECT count(*) FROM dialed WHERE datetime BETWEEN datetime(date('now', '$PENULTIMATE days')) AND datetime(date('now', '$PREVIOUS days')) AND localid=$LOCALID)
	AS penultimate_day,
		(SELECT count(*) FROM dialed WHERE datetime BETWEEN datetime(date('now', '$PREVIOUS days')) AND datetime(date('now', '$CURRENT days')) AND localid=$LOCALID)
	AS previous_day,
		count(*)
	AS current_day
		FROM dialed WHERE datetime BETWEEN datetime(date('now', '$CURRENT days')) AND datetime(date('now', '$NEXT days')) AND localid=$LOCALID
UNION
SELECT
		"received"
	AS type,
		(SELECT count(*) FROM received WHERE datetime BETWEEN datetime(date('now', '$PENULTIMATE days')) AND datetime(date('now', '$PREVIOUS days')) AND localid=$LOCALID)
	AS penultimate_day,
		(SELECT count(*) FROM received WHERE datetime BETWEEN datetime(date('now', '$PREVIOUS days')) AND datetime(date('now', '$CURRENT days')) AND localid=$LOCALID)
	AS previous_day,
		count(*)
	AS current_day
		FROM received WHERE datetime BETWEEN datetime(date('now', '$CURRENT days')) AND datetime(date('now', '$NEXT days')) AND localid=$LOCALID
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
		      m.datetime BETWEEN datetime(date('now', '$PENULTIMATE days')) AND datetime(date('now', '$PREVIOUS days')) AND m.localid=$LOCALID
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
		  	  mp.datetime < datetime(date('now', '$PENULTIMATE days')) AND mp.localid=$LOCALID
		      --AND mp.localid || '_' || mp.remotenr IN (SELECT localid || '_' || remotenr FROM missed WHERE datetime BETWEEN datetime('now', 'start of month') AND datetime('now', 'localtime'))
		    GROUP BY
		  	  mp.localid, mp.remotenr
		  )
		  GROUP BY localid, remotenr
		)

		WHERE count > 0
		ORDER BY count DESC
	)
	AS penultimate_day,
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
		      m.datetime BETWEEN datetime(date('now', '$PREVIOUS days')) AND datetime(date('now', '$CURRENT days')) AND m.localid=$LOCALID
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
		  	  mp.datetime < datetime(date('now', '$PREVIOUS days')) AND mp.localid=$LOCALID
		      --AND mp.localid || '_' || mp.remotenr IN (SELECT localid || '_' || remotenr FROM missed WHERE datetime BETWEEN datetime('now', 'start of month') AND datetime('now', 'localtime'))
		    GROUP BY
		  	  mp.localid, mp.remotenr
		  )
		  GROUP BY localid, remotenr
		)

		WHERE count > 0
		ORDER BY count DESC
		)
	AS previous_day,
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
		      m.datetime BETWEEN datetime(date('now', '$CURRENT days')) AND datetime(date('now', '$NEXT days')) AND m.localid=$LOCALID
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
		  	  mp.datetime < datetime(date('now', '$CURRENT days')) AND mp.localid=$LOCALID
		      --AND mp.localid || '_' || mp.remotenr IN (SELECT localid || '_' || remotenr FROM missed WHERE datetime BETWEEN datetime('now', 'start of month') AND datetime('now', 'localtime'))
		    GROUP BY
		  	  mp.localid, mp.remotenr
		  )
		  GROUP BY localid, remotenr
		)

		WHERE count > 0
		ORDER BY count DESC
		)
	AS current_day

;
