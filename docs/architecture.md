# Architecture

Media sosial -> collector adapters -> normalized raw_social_items -> preprocessing -> sentiment engine -> database -> api -> dashboard/export.

Core design rule: keep platform payload raw, then normalize to one canonical contract.
