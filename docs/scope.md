# Scope and evidence

SynapseETL turns heterogeneous synthetic sensor CSVs into canonical events. A policy or model proposes a field mapping; review binds the exact transforms; deterministic ingestion validates rows, quarantines errors, and records lineage.

Source, synthetic fixtures, tests, installed commands, and demo artifacts are the
evidence. JSON and HTML examples record completed runs; they are not a hosted
service. Provider tests use mocked responses and do not establish the quality of
any specific running model.

## Limits

This reference accepts CSV, one synthetic telemetry schema, and a fixed
transform library. It has no distributed processing, connectors, streaming,
schema registry, or automatic repair. Equivalent CSVs with different formatting
create different batches; natural IDs still deduplicate canonical events. Approval
is a local label rather than authenticated authorization. Model commands send
profile samples to your configured endpoint. No live model quality is claimed.

No production scale, vendor connectivity, clinical safety, business outcomes,
or model superiority is claimed. CI configuration and locally passing checks
are separate from a verified remote CI run.
