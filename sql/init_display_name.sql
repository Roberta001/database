update song 
set display_name = modify_name(name)
where type = '翻唱';
update song
set display_name = '视奸(Best Friend Remix)'
where name like '视奸(Best%';
update song
set display_name = 'World.Execute(me);'
where name ilike 'world.execute%';