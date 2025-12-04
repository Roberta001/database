select
	v.title, song.name, s.item
from video v
join (select bvid, max(view) as item
	from snapshot
	group by bvid) as s using (bvid)
join song on song.id = v.song_id
order by item desc
offset 20
limit 10