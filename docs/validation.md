# Local verification

Validated on October 28, 2026, on macOS arm64.

- 23 tests passed on each of Python 3.12, 3.13, and 3.14.
- Python 3.11 syntax was checked; its runtime was not installed locally.
- Ruff lint and format checks passed.
- Wheel and source distribution built successfully.
- The wheel was installed and its command ran from outside the checkout.
- A full command-line workflow and the README Python example passed.
- Relative Markdown links and banner SVG XML were checked.
- The generated HTML report was opened and inspected in the browser.

Provider tests use mocked responses. No live model inference was performed.
Remote CI was not run because personal GitHub authentication was unavailable.
The CI matrix is configuration, not evidence of a remote run. Local checks do
not establish production readiness or hosted security.
