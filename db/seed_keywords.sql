insert into keywords (id, keyword, target_entity, platform) values
('kw_bions_youtube','bions','bions','youtube'),
('kw_bni_sekuritas_youtube','bni sekuritas','bni_sekuritas','youtube'),
('kw_bions_x','bions','bions','x'),
('kw_bni_sekuritas_x','bni sekuritas','bni_sekuritas','x')
on conflict do nothing;
