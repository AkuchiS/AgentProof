# AgentProof -- Verifiable Edition
# The whole product in one command. No deps, no network, stdlib Python 3 only.

.PHONY: verify selftests clean

# The hero command. Runs every module's real selftest on YOUR machine and
# prints the real pass counts with a combined PASS/FAIL exit code.
verify:
	@python3 verify.py

# Run each module's selftest directly (raw, unaggregated output).
selftests:
	@for f in modules/*.py; do \
		echo "===== $$f ====="; \
		python3 "$$f"; \
		echo; \
	done

clean:
	@find . -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "cleaned __pycache__"
