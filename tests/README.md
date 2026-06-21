# test layout

```txt
tests/
  unit/          fast isolated tests, no network, no database
  integration/   tests across app/module boundaries, no live third-party calls by default
```

## run

```bash
pytest -q
pytest tests/unit -q
pytest tests/integration -q
pytest -m unit -q
pytest -m integration -q
```

## rules

- use pytest only
- no live third-party calls in default suite
- live collectors must be opt-in with `@pytest.mark.live`
- prefer fixtures in `tests/conftest.py`
- test behavior and safety stops, not private implementation details
