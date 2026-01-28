# Stress Test Automation

This adds a simple automated runner that executes a fixed set of prompts against `cpp ask`,
collects the generated run folders, and summarizes diagram outcomes using `run.json`.

## Files

- `stress/prompts.json` — the prompt set (edit to add/remove prompts)
- `scripts/run_stress.py` — runs the stress suite and writes reports
- Output reports are written under: `runs_stress/_reports_<timestamp>/`

## Usage

From repo root:

```bash
python scripts/run_stress.py
```

Optional overrides:

```bash
python scripts/run_stress.py --prompts stress/prompts.json --log-dir runs_stress
```

Disable diagrams entirely (still useful for baseline):

```bash
python scripts/run_stress.py --no-diagrams
```

## What it produces

- `runs_stress/<run_folder>/...` — one run per prompt (normal CPP run logging)
- `runs_stress/_reports_<timestamp>/stress_summary.md`
- `runs_stress/_reports_<timestamp>/stress_summary.csv`
- `runs_stress/_reports_<timestamp>/*_stdout.txt` and `*_stderr.txt`

## Notes

- The runner finds the latest run folder created under `--log-dir` after each `cpp ask`.
- It summarizes using `run.json.items[]`:
  - `diagram_generated` (visualizer returned something other than `(none)` before hiding)
  - `diagram_hidden` (hidden by validator or flags)
  - shown = generated - hidden
