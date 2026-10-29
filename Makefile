PYTHON ?= python3
.PHONY: test demo check
test:
	$(PYTHON) -m unittest discover -s tests -v
demo:
	$(PYTHON) -m synapse_etl demo
check: test demo
	$(PYTHON) -m compileall -q synapse_etl
