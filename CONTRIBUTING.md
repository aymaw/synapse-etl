# Contributing

Use Python 3.11 or later. No runtime dependencies are required.

```sh
python3 -m unittest discover -s tests -v
python3 -m synapse_etl demo
```

Keep examples synthetic. Add regression coverage for behavior changes. Include
the failure scenario, expected behavior, and validation results in pull requests.
Model outputs are untrusted proposals; deterministic checks own state changes.
