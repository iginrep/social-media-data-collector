PY=python3

.PHONY: test collect analyze export api

test:
	$(PY) -m pytest -q

collect:
	$(PY) -m pipeline.collector.run

analyze:
	$(PY) -m pipeline.sentiment.run

export:
	$(PY) -m pipeline.export.csv_export

api:
	$(PY) -m uvicorn apps.api.app.main:app --reload
