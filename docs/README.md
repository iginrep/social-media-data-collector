# docs

Human-facing documentation for the BNI/BIONS sentiment monitoring project.

Use this directory for strategy, architecture, data contracts, research, approval records, and operational notes.

## Reading order

1. `architecture.md` — system overview.
2. `collector-strategy.md` — cheapest-first source plan.
3. `human-approval-checklist.md` — current approvals and risk gates.
4. `data-contract.md` — canonical normalized item reference and collection schemas.
5. `provider-decision-matrix.md` — source/API/vendor tradeoffs.
6. `labeling-guideline.md` — sentiment labeling rules.

## Runbooks

| Runbook | Use |
| --- | --- |
| `runbook/00-prerequisites.md` | Setup and config |
| `runbook/01-google-play.md` | Google Play collection |
| `runbook/02-app-store.md` | App Store collection |
| `runbook/03-youtube.md` | YouTube collection |
| `runbook/11-docker-mongodb.md` | Local MongoDB |
| `runbook/12-backfill-retention.md` | Historical backfill with checkpoints |

## Research docs

| File | Purpose |
| --- | --- |
| `stockbit-x-collection-research.md` | Stockbit and X/Twitter collection options, risks, approval needs. |
| `tiktok-instagram-threads-cheapest-first.md` | TikTok, Instagram, Threads options and safety posture. |
| `source-limitations.md` | Known source limitations. |

## Documentation style

Use Diátaxis framing:

- tutorials for onboarding walkthroughs.
- how-to guides for task recipes.
- reference for exact schemas, commands, APIs.
- explanation for tradeoffs and architecture.

Keep safety/compliance notes explicit. This project intentionally prioritizes low-risk collection over maximum volume.
