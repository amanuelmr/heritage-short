PY = uv run python
.PHONY: setup validate smoke narration radio keyframes film clean-cache

setup:        ## install dependencies
	uv sync
validate:     ## check storyboard.json against the schema
	$(PY) pipeline/validate.py
smoke:        ## call each provider once, log latency, list real model ids
	$(PY) pipeline/smoke.py
narration: validate
	$(PY) pipeline/narration.py
radio: narration   ## prototype for user test 1: narration + placeholder pad on black
	$(PY) pipeline/radio_cut.py
keyframes: validate
	$(PY) pipeline/keyframes.py --ref
film: radio keyframes   ## whole pipeline (music, shots, assemble added as they land)
	@echo "film: stages so far complete"
