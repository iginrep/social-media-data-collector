# Source Limitations

Adapters expose collector metadata:

- `access_mode`: `official_api`, `unofficial_api`, `automation`, `rss`, `vendor`, `disabled`
- `cost_level`: `free`, `cheap`, `paid`, `expensive`
- `risk_level`: `low`, `medium`, `high`
- `enabled_by_default`: risky collectors stay disabled until approved

No collector should hide ToS/API limitations. Store raw payload for audit and reprocessing.

Default strategy: cheapest useful source first. Upgrade to official paid API only after a source proves value and needs reliability.
