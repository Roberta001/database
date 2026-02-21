WITH anon_1 AS
(SELECT snapshot.bvid AS bvid, max(snapshot.date) AS latest
FROM snapshot
WHERE snapshot.view >= 10000 AND snapshot.view < 100000 GROUP BY snapshot.bvid)
 SELECT song.id, song.name, song.type, video.bvid, video.title, video.pubdate, video.uploader_id, video.song_id, video.copyright, video.thumbnail, video.duration, video.page, snapshot.bvid AS bvid_1, snapshot.date, snapshot.view, snapshot.favorite, snapshot.coin, snapshot."like", snapshot.danmaku, snapshot.reply, snapshot.share
FROM anon_1 JOIN video ON video.bvid = snapshot.bvid JOIN song ON song.id = video.song_id JOIN snapshot ON anon_1.bvid = snapshot.bvid AND anon_1.latest = snapshot.date ORDER BY snapshot.view DESC
 LIMIT 10 OFFSET 20