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
| Instagram | `{IG_MEDIA_ID}/comments` with `replies{...}` | weak in official API | media -> comment -> reply |
| Threads | `{THREADS_MEDIA_ID}/conversation` | weak in official API | flattened conversation; parent via `replied_to`; root via `root_post` |
| TikTok | Research API `video/comment/list` for `video_id` | Research API video discovery later | video -> comment -> reply if `parent_comment_id` exists |
| Google Play | package reviews | n/a | app -> review |
| App Store | app reviews rss | n/a | app -> review |
| Stockbit | target discussion pages | weak/no official API | page/thread scrape, config gated |

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
