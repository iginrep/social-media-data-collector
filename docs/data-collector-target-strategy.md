# Data collector target strategy

Use target-first lanes, then normalize every response to the flat thread model.

## Universal output

Every collector emits `RawSocialItem` rows:

```txt
source_id
root_source_id
parent_source_id
conversation_id
source_type
depth
relation_type
```

Rebuild trees with `source_id -> parent_source_id`.

## Lanes

### 1. Brand-owned content comments

Collect official-account posts/videos/media first, then collect comments/replies under those objects.

Use this for customer reactions under official communications.

### 2. Public search mentions

Collect public posts containing brand/app keywords.

Use this for unprompted market/user sentiment.

## Platform shape

| platform | owned-content lane | public-search lane | native shape |
| --- | --- | --- | --- |
| X | official user tweets, then `conversation_id:<tweet_id> -from:<username>` | `/2/tweets/search/recent` keyword queries | tweet graph; replies are tweets with `referenced_tweets.type=replied_to`; thread root is `conversation_id` |
| YouTube | channel videos, then `commentThreads.list` | not primary | video -> comment -> reply |
| Instagram | `{IG_MEDIA_ID}/comments` with `replies{...}` | hashtag search via `/{IG_USER_ID}/ig_hashtag_search` -> `/{HASHTAG_ID}/recent_media` -> media comments | media -> comment -> reply |
| Threads | `{THREADS_MEDIA_ID}/conversation` | `/keyword_search` with `q`, `search_type`, optional media/time filters | flattened conversation; parent via `replied_to`; root via `root_post` |
| TikTok | Research API `video/comment/list` for `video_id` | Research API video discovery later | video -> comment -> reply if `parent_comment_id` exists |
| Google Play | package reviews | n/a | app -> review |
| App Store | app reviews rss | n/a | app -> review |
| Stockbit | target discussion pages | weak/no official API | page/thread scrape, config gated |

## Instagram current implementation

`InstagramAdapter` now supports two lanes:

```txt
collect_media_comments(media_id)
collect_hashtag_mentions(query)
```

Env config:

```env
INSTAGRAM_GRAPH_ACCESS_TOKEN=...
INSTAGRAM_MEDIA_IDS=1789012345678901234,1789012345678905678
INSTAGRAM_IG_USER_ID=17841405309211844
INSTAGRAM_HASHTAG_QUERIES=BIONS,BNISEKURITAS
```

Behavior:

1. Owned lane fetches each configured media ID with `/{media_id}/comments`.
2. Hashtag lane resolves each query with `/{ig_user_id}/ig_hashtag_search`.
3. It fetches recent public media via `/{hashtag_id}/recent_media`.
4. It fetches comments/replies under each discovered media ID.

## Threads current implementation

`ThreadsAdapter` now supports two lanes:

```txt
collect_conversations(media_id)
collect_keyword_search(query)
```

Env config:

```env
THREADS_ACCESS_TOKEN=...
THREADS_MEDIA_IDS=1789012345678901234,1789012345678905678
THREADS_SEARCH_QUERIES=BIONS,BNI Sekuritas,BIONS error
```

Behavior:

1. Owned lane fetches each configured media ID with `/{media_id}/conversation`.
2. Keyword lane searches each query with `/keyword_search` using `search_type=RECENT`.
3. Both lanes normalize rows into flat thread fields.

## X current implementation

`TwitterAdapter` now supports two lanes:

```txt
collect_recent_mentions(query)
collect_conversation_replies(tweet_id, username)
```

Env config:

```env
X_BEARER_TOKEN=...
X_SEARCH_QUERIES="BIONS" lang:id -is:retweet,"BNI Sekuritas" lang:id -is:retweet
X_OFFICIAL_USERNAMES=BNI1946,bnisekuritas46
```

Behavior:

1. Public mentions lane runs each `X_SEARCH_QUERIES` query with `/2/tweets/search/recent`.
2. Official comments lane resolves each username via `/2/users/by/username/{username}`.
3. It fetches recent official posts via `/2/users/{id}/tweets` excluding retweets/replies.
4. For each official tweet, it searches replies with:

```txt
conversation_id:<tweet_id> -from:<username>
```

## Stop rules

Collectors stop closed on:

```txt
401/403 auth or permission
429 rate limit
captcha/login wall for public scrapers
3 consecutive 5xx if implemented by collector
```

No manual import. No fake rows. Missing config raises `CollectorNotConfigured`.

## Backfill support

| Platform | `collect_backfill()` | Status |
| --- | --- | --- |
| Google Play | yes | checkpoint-based resume, 365d |
| App Store | yes | checkpoint-based resume, 365d |
| YouTube | yes | checkpoint-based resume, request budget/delay |
| X | no | unsupported (needs historical adapter) |
| Instagram | no | unsupported (needs historical adapter) |
| Threads | no | unsupported (needs historical adapter) |
| TikTok | no | unsupported (needs historical adapter) |
| Stockbit | no | unsupported (needs historical adapter) |

Run backfill:

```bash
python -m pipeline.collector.backfill --retention-days 365 --window-days 14 --limit-per-window 5 --recent-overlap-days 7
```

Override quotas with env:

```bash
YOUTUBE_BACKFILL_MAX_REQUESTS=20
YOUTUBE_BACKFILL_REQUEST_DELAY_SECONDS=2
```
