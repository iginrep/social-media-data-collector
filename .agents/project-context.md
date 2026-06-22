# Project context for AI agents

## Mission

Build a safe cheapest-first sentiment monitoring system for BNI Sekuritas and the BIONS app.

The system should collect public feedback, normalize it, classify sentiment, and support dashboards/exports for analysis.

## Business questions

The project should help answer:

- what users complain about in BIONS app reviews.
- whether BIONS/BNI Sekuritas sentiment is improving or worsening.
- which topics drive negative sentiment: login, OTP, trading, order execution, deposit/withdrawal, app crash, customer service, fees, performance.
- which platforms contain actionable signal.
- when a source is valuable enough to justify official API/vendor spend.

## Chosen strategy

Cheapest-first validation:

1. start with public/free low-risk sources.
2. keep risky automation disabled.
3. prove the pipeline and analysis value.
4. upgrade to official/paid APIs only when reliability/compliance/volume requires it.

## Approved MVP sources

```yaml
google_play:
  platform: google_play
  source_type: app_review
  app_id: id.bions.bnis.android
  url: https://play.google.com/store/apps/details?id=id.bions.bnis.android&hl=id
  country: id
  language: id
  status: approved

apple_app_store:
  platform: app_store
  source_type: app_review
  app_id: "6736508566"
  url: https://apps.apple.com/id/app/bions/id6736508566
  country: id
  status: approved

youtube:
  platform: youtube
  source_type: comment
  channels:
    - handle: BNI1946
      url: https://www.youtube.com/@BNI1946
    - handle: bnisekuritas46
      url: https://www.youtube.com/@bnisekuritas46
  auth: YOUTUBE_API_KEY in .env
  status: approved
```

User approved saving raw public usernames/display names.

## Disabled until explicit approval

```yaml
stockbit: false
x: false
tiktok: false
instagram: false
threads: false
```

Reasons:

- login/session requirements.
- anti-bot/CAPTCHA risk.
- ToS/compliance risk.
- account/IP block risk.
- unstable unofficial APIs.

## Current repo shape

```txt
apps/api/app/                 FastAPI application
pipeline/collector/           adapters, normalization, dedupe, backfill runner
pipeline/storage/             social_items persistence, checkpoint store
pipeline/sentiment/           preprocessing, rules, classifier hooks
pipeline/scheduler/           APScheduler jobs
pipeline/export/              CSV/XLSX export
db/                           Mongo init, indexes, seed data
docs/                         human docs and research
.agents/                      AI-agent context
```

## Database
MongoDB database: `bni_bions_sentiment`.
Connection: `mongodb://localhost:27017`.

Mongo init file: `db/mongo-init.js`.

Primary collections:

```txt
social_items               canonical normalized items (app reviews + comments)
collection_checkpoints     backfill window status (complete/partial)
collection_runs            scheduled run history
keywords                   monitored keywords
sentiment_results          sentiment classification outputs
```

See `docs/data-contract.md` for full schema.

## Source docs

Useful docs already in repo:

```txt
docs/collector-strategy.md
docs/provider-decision-matrix.md
docs/human-approval-checklist.md
docs/stockbit-x-collection-research.md
docs/tiktok-instagram-threads-cheapest-first.md
docs/source-limitations.md
docs/data-contract.md
docs/labeling-guideline.md
docs/architecture.md
```
