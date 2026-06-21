# Canonical Social Item

```python
RawSocialItem(
  platform,
  source_type,
  source_id,
  parent_source_id,
  conversation_id,
  keyword,
  target_entity,
  author_id,
  author_username,
  author_display_name,
  text,
  language,
  source_url,
  posted_at,
  collected_at,
  metrics,
  raw_payload,
  content_hash,
)
```

Use `raw_social_items`, not `raw_comments`, because X has tweets, Threads has replies, Stockbit may have posts/comments.
