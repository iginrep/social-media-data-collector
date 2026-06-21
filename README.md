# social-media-data-collector

Monorepo sederhana untuk monitoring sentimen BNI Sekuritas dan aplikasi BIONS.

Pipeline:

1. keyword + schedule
2. social collector adapters
3. canonical raw social item normalization
4. dedupe + preprocessing
5. sentiment classification: positive / neutral / negative
6. api + dashboard
7. csv/xlsx export

## Quick start

```bash
cd /home/hp/dev/work/bni-bions-sentiment-analysis
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
make test
make collect
make analyze
make export
make api
```

## Source caveats

- YouTube: official Data API is straightforward.
- X/Twitter: needs API tier.
- Instagram: Graph API limited to business/creator/owned media access.
- TikTok: official comment access limited; scraping has ToS risk.
- Threads: public search/replies limited.
- Stockbit: no stable public comment API found; unofficial adapter should be marked fragile.
