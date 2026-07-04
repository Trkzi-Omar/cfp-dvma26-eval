# multi-agent-prod-reference
#
# The repo's public interface. Every target works offline in mock mode with no
# API key. `make setup && make run-demo` should take well under 10 minutes.

PYTHON ?= python3

.PHONY: help setup run-demo run-fail eval baseline traces test clean

help:
	@echo "Targets:"
	@echo "  make setup      Install deps (pytest only) and create .env"
	@echo "  make run-demo   Run one ticket end to end (mock mode, no key)"
	@echo "  make run-fail   Run the misrouting scenario to see a silent failure"
	@echo "  make eval       Run the eval harness, print a summary, write a report"
	@echo "  make baseline   Run evals and save the result as the regression baseline"
	@echo "  make traces     Regenerate and print the committed example traces"
	@echo "  make test       Run the test suite"

setup:
	@[ -f .env ] || cp .env.example .env
	@$(PYTHON) -m pip install -r requirements.txt
	@echo "Setup complete. Try: make run-demo"

run-demo:
	@$(PYTHON) -m app.main examples/easy_ticket.json

run-fail:
	@$(PYTHON) -m app.main examples/ambiguous_ticket.json

eval:
	@$(PYTHON) -m evals.run_evals

baseline:
	@$(PYTHON) -m evals.run_evals --baseline

traces:
	@$(PYTHON) -m traces.refresh_examples

test:
	@$(PYTHON) -m pytest -q

clean:
	@find . -type d -name __pycache__ -prune -exec rm -rf {} +
	@rm -f traces/*_trace.json evals/reports/latest.json evals/reports/latest.md
	@echo "Cleaned generated files."
