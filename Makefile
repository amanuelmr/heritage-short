PY = uv run python
.PHONY: setup validate smoke narration radio keyframes shots music assemble film

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
shots: keyframes   ## Wan 2.2 on a Kaggle T4, only for shots whose inputs changed
	$(PY) pipeline/shots.py
music: validate    ## ACE-Step 1.5 score candidates on a Kaggle T4
	$(PY) pipeline/music.py
assemble:          ## both aspect ratios, subtitles, ducking, -14 LUFS, end card
	$(PY) pipeline/assemble.py
film: narration keyframes shots music assemble   ## the whole pipeline, end to end
	@echo "film ready in outputs/final/"
