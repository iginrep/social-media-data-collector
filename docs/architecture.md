# Architecture

Media sosial -> collector adapters -> normalized raw_social_items -> preprocessing -> sentiment engine -> database -> api -> dashboard/export.

Core design rule: keep platform payload raw, then normalize to one canonical contract.

Collector rule: cheapest useful source first. Official/paid APIs are promotion targets after the source proves value.
