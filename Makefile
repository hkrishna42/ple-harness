# Build-time commands for ple-harness. See CLAUDE.md.
KIT_SHA := 8320f0402fdca9f42476607f72bcfd5271cd50c9
# The kit sits next to the main checkout; worktrees find it through the git common dir.
KIT ?= $(abspath $(shell git rev-parse --path-format=absolute --git-common-dir)/../../ple)
UV := uv run --frozen

.PHONY: check kit kit-check handover

check: kit
	$(UV) ruff check .
	$(UV) ruff format --check .
	$(UV) mypy --strict harness cost .claude/hooks/guard.py
	PLE_KIT_DIR=$(KIT) $(UV) pytest -q
	cd $(KIT) && uv run --quiet python -m kit validate $(CURDIR)
	@mkdir -p .claude/state && touch .claude/state/tests-ran
	@echo "make check: all green"

kit:
	@test -d $(KIT) || git clone --quiet https://github.com/google-research/ple $(KIT)
	@test "$$(git -C $(KIT) rev-parse HEAD)" = "$(KIT_SHA)" || \
		(git -C $(KIT) fetch --quiet origin && git -C $(KIT) checkout --quiet $(KIT_SHA))

kit-check: kit
	cd $(KIT) && uv run python -m kit check $(CURDIR) $(ARGS)

# ADR-0002: ws/<name> writes docs/handover/<name>.md; main writes LATEST.md
HANDOVER = docs/handover/$(or $(patsubst ws/%,%,$(filter ws/%,$(shell git branch --show-current))),LATEST).md

handover:
	cp docs/handover/TEMPLATE.md $(HANDOVER)
	@echo "Now fill in $(HANDOVER) (skill ple-handover)."
