# Agent workflows

Use these workflows when modifying this repository.

## Before changing code

1. Read `AGENTS.md`.
2. Read the relevant `.agents/*` file.
3. Check current git state:

```bash
git status --short
```

4. If changing library/API usage, fetch current docs first.
5. Prefer the smallest safe slice.

## Collector implementation workflow

1. Confirm the platform is approved/enabled.
2. Read `.agents/safety-and-compliance.md`.
3. Read `.agents/collector-contract.md`.
4. Add or update tests first where possible.
5. Implement adapter normalization without live network in tests.
6. Add stop-condition handling.
7. Verify limits/rate config exists before any real fetch path.
8. Run:

```bash
. .venv/bin/activate
pytest -q
node --check db/mongo-init.js
```

9. Summarize changed files, test output, risks.

## Backfill workflow

1. Implement `collect_backfill()` on the adapter following the backfill contract in `.agents/collector-contract.md`.
2. Add unit tests for backfill normalization (no live network).
3. Add rate-limit/quota safety tests if adapter uses paid APIs.
4. Verify the adapter appears in `remaining_platform_adapters()` output.
5. Run backfill dry-run first:

```bash
.venv/bin/python -m pipeline.collector.backfill --dry-run --retention-days 365 --window-days 14
```

6. Run live backfill with safe defaults:

```bash
.venv/bin/python -m pipeline.collector.backfill --retention-days 365 --window-days 14 --limit-per-window 5 --recent-overlap-days 7
```

7. Verify MongoDB state:

```bash
.venv/bin/python -c "
from apps.api.app.db import get_database
db = get_database()
print(db.social_items.count_documents({}))
print(db.collection_checkpoints.count_documents({}))
"
```

8. Update `docs/runbook/12-backfill-retention.md` if platform support changed.

## API workflow

1. Keep route response shapes stable.
2. Add/adjust FastAPI TestClient tests.
3. Avoid leaking raw payloads unless endpoint is explicitly internal/admin.
4. Verify:

```bash
. .venv/bin/activate
pytest -q
```

## Data/schema workflow

1. Prefer Mongo schema/index updates in `db/mongo-init.js`.
2. Keep `docs/data-contract.md` and `.agents/collector-contract.md` aligned.
3. For any new field, document:
   - purpose
   - type
   - whether it can contain PII
   - retention expectation
4. Verify:

```bash
node --check db/mongo-init.js
pytest -q
```

## Sentiment workflow

1. Preserve positive/neutral/negative labels unless user changes taxonomy.
2. Keep Indonesian text in mind.
3. Prefer explainable rule/model hooks over opaque changes.
4. Add examples to tests or labeling docs.
5. Verify:

```bash
pytest -q tests/test_sentiment_rules.py tests/test_normalizer.py
```

## Docs workflow

Agent docs should be:

- command-first.
- specific to this repo.
- clear about boundaries.
- linked to deeper files instead of one huge blob.
- updated when decisions change.

Main docs:

```txt
AGENTS.md
.agents/README.md
.agents/project-context.md
.agents/safety-and-compliance.md
.agents/collector-contract.md
.agents/workflows.md
```

## Commit workflow

Before commit:

```bash
git status --short
. .venv/bin/activate
pytest -q
node --check db/mongo-init.js
git diff --check
git diff --staged --check
git diff --staged | grep -Ei 'password|secret|api[_-]?key|token|cookie|authorization|bearer' || true
```

If grep hits real secrets, stop and remove them. Placeholder/risk docs are ok.

Commit message format:

```txt
<type>: <short imperative summary>
```

Examples:

```txt
docs: add ai agent operating guide
feat: add google play review collector
fix: stop youtube collector on quota errors
test: cover app review normalization
```

## Completion report

When done, report:

```txt
changed:
- file paths

verified:
- exact commands + output summary

risks:
- any remaining blockers or disabled behavior
```
