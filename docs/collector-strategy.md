# Collector Strategy: Cheapest First

Goal: get stable BNI Sekuritas/BIONS sentiment data with the lowest operating cost first. Move to paid/official APIs only after the pipeline, schema, sentiment labels, dashboard, and reporting are validated.

## Principle

1. Prefer public/low-cost sources that directly mention BIONS.
2. Keep every source behind an adapter so we can swap unofficial/automation to official API later.
3. Raw payload is always stored for audit and reprocessing.
4. Risky collectors are disabled by default in production until approved.
5. Dashboard/API must not care whether data came from API, browser automation, RSS, or vendor.

## Access modes

```txt
official_api      documented official API
unofficial_api    public/private endpoint or unofficial library
automation        Playwright/Selenium/browser collection
rss               RSS/feed/simple public endpoint
vendor            paid data/social listening provider
disabled          known but not active
```

## Risk levels

```txt
low       official/public stable source, low block risk
medium    unofficial but common/stable, throttle required
high      login automation, private API, ToS/block/legal risk
```

## Platform plan

| Priority | Source | First approach | Later stable approach | Cost | Risk | Why |
|---:|---|---|---|---|---|---|
| 1 | Google Play BIONS reviews | unofficial library / public reviews | same or approved vendor | free | low-medium | direct app sentiment, ratings, version info |
| 2 | Apple App Store BIONS reviews | public iTunes RSS/Search API | same | free | low | direct app sentiment, structured ratings |
| 3 | YouTube comments | YouTube Data API free quota | same, higher quota if needed | free/cheap | low | official, easy comments/replies |
| 4 | Stockbit | Playwright automation low-rate | partnership/vendor/API if available | free | high | strong Indonesian finance community signal |
| 5 | X/Twitter | cheap third-party/vendor trial or browser prototype | official X API v2 paid | cheap→paid | medium-high | high complaint/mention signal but API cost |
| 6 | Instagram | owned-media Graph API if access exists; otherwise disabled | Graph API/vendor | free→paid | low official/high scraping | public keyword comments restricted |
| 7 | Threads | owned replies API if access exists; otherwise disabled | Threads API/vendor | free→paid | medium | public keyword search limited |
| 8 | TikTok | vendor/manual/browser prototype only | approved TikTok API/vendor | cheap→paid | high | comments/search difficult, anti-bot risk |

## Adapter defaults

```txt
google_play: access_mode=unofficial_api, cost=free, risk=medium, enabled=true
app_store:   access_mode=rss,            cost=free, risk=low,    enabled=true
youtube:     access_mode=official_api,   cost=free, risk=low,    enabled=true
stockbit:    access_mode=automation,     cost=free, risk=high,   enabled=false
x:           access_mode=automation,     cost=free, risk=high,   enabled=false, upgrade_to=official_api
instagram:   access_mode=official_api,   cost=free, risk=low,    enabled=false unless owned account access
threads:     access_mode=official_api,   cost=free, risk=medium, enabled=false unless owned account access
tiktok:      access_mode=automation,     cost=free, risk=high,   enabled=false
```

## Promotion rule to official API

Move a platform from cheap collector to official API when at least 3 are true:

- data volume is useful for dashboard/reporting
- source contributes unique signal not covered elsewhere
- collector breaks more than twice per month
- legal/ToS risk is unacceptable for production
- stakeholder needs SLA/reliable daily report
- budget approved

## Browser automation rules

Use only for prototype/low volume:

- public pages first, logged-in only if approved
- no CAPTCHA bypass
- no credential sharing in repo
- throttle heavily
- random jitter
- persist checkpoints
- store `collectionMethod=automation`, `accessRisk=high`
- keep disabled by default in `.env.example`

## MongoDB fields required

Every `social_items` document should include:

```json
{
  "collectionMethod": "official_api | unofficial_api | automation | rss | vendor",
  "accessRisk": "low | medium | high",
  "collectorVersion": "string",
  "rawPayload": {}
}
```

## Immediate MVP

1. Google Play reviews collector.
2. Apple App Store reviews collector.
3. YouTube official free-quota collector.
4. Stockbit Playwright spike, disabled by default.
5. X official API later after product proves value.
