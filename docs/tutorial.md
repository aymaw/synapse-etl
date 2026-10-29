# SynapseETL walkthrough

Start with `python3 -m synapse_etl demo --html .runs/demo.html`. This creates a
fresh synthetic scenario, executes it, and prints the actual result. Open the
HTML artifact to inspect evidence and export JSON.

## Work with the CLI

```sh
python3 -m synapse_etl profile examples/telemetry.csv
python3 -m synapse_etl propose examples/telemetry.csv > proposal.json
python3 -m synapse_etl approve proposal.json local-reviewer > mapping.json
python3 -m synapse_etl ingest examples/telemetry.csv mapping.json
python3 -m synapse_etl ingest examples/telemetry.csv mapping.json
```

The second ingestion returns the batch with `replayed: true`. The reviewed
synthetic fixture exists only to reproduce the demo. Header drift fails before
writes. Row problems enter quarantine while valid rows are accepted. Structural
CSV corruption rejects the input. Storage failure rolls back the entire batch.

## Reproduce and inspect

```sh
python3 -m synapse_etl demo > demo.json
python3 -m unittest discover -s tests -v
```

`examples/demo.json` was captured from this implementation. Identifiers and
labels are synthetic. AgentBench timings vary with hardware and scheduling;
suite identity and policy outcomes remain reproducible.

## Expected failures

Invalid domain operations print a JSON error to stderr and exit 2. AgentBench's
regression gate exits 1 when a scenario regresses. Tests exercise invalid actions
and verify rejected or rolled-back state changes. No test needs external
credentials or a live model.
