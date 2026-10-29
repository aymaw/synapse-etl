# Verification record

Validated on October 28, 2026, on macOS arm64.

- 23 tests passed on each of Python 3.12, 3.13, and 3.14.
- Python 3.11 syntax was checked; its runtime was not installed locally.
- Ruff lint and format checks passed.
- Wheel and source distribution built successfully.
- The wheel was installed and its command ran from outside the checkout.
- A full command-line workflow and the README Python example passed.
- Relative Markdown links and banner SVG XML were checked.
- The generated HTML report was opened and inspected in the browser.

## Hosted verification

[GitHub Actions passed all six matrix jobs](https://github.com/aymaw/synapse-etl/actions/runs/40798027435) on October 28, 2026,
for executable source commit `778856014c6792987f344deba0c22279dbf0c7c5`.

- Ubuntu: Python 3.11, 3.12, 3.13, and 3.14.
- macOS and Windows: Python 3.13.
- Each job checks lint and formatting, builds and installs the package, runs the
  full test suite, compiles modules, and uploads a generated synthetic demo.
- GitHub reports runner migration and action runtime deprecation notices; these
  did not prevent successful verification.

The Windows runs verified fixes that preserve OS TLS environment variables in
the provider isolation test and, for AgentFlow, close test database connections
before removing temporary files. These are test portability fixes.

Provider tests use mocked responses. No live model inference was performed.
These checks do not establish production readiness or hosted security.
