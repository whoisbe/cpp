#!/usr/bin/env python3
"""
Stress test automation runner for CPP.

This script:
- reads stress prompts from stress/prompts.json
- invokes `cpp ask ...` for each prompt in a non-interactive way
- captures the created run folder path
- summarizes diagram outcomes from run.json for each run
- writes a summary CSV + markdown report

Assumptions:
- `cpp` is available on PATH (installed editable or via poetry/pipx/etc.)
- `cpp ask` supports: --log-dir, --debug, --no-diagrams (per current implementation)
- Each run writes run.json under the created run folder
"""
from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

RUN_DIR_RE = re.compile(r"(?:Run saved to:|run directory:|Created run:)\s*(.+)$", re.IGNORECASE)

@dataclass
class RunSummary:
    prompt_id: str
    prompt: str
    run_path: str
    ideas_count: int
    diagrams_generated: int
    diagrams_hidden: int
    diagrams_shown: int
    hidden_rate: float
    nlp_attempted: int = 0
    nlp_diagrams_present: int = 0

def _load_prompts(prompts_path: Path) -> List[Dict[str, str]]:
    data = json.loads(prompts_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("prompts.json must be a list")
    for item in data:
        if "id" not in item or "prompt" not in item:
            raise ValueError("Each prompt entry must have id and prompt")
    return data

def _find_latest_run(log_dir: Path) -> Optional[Path]:
    if not log_dir.exists():
        return None
    runs = [p for p in log_dir.iterdir() if p.is_dir()]
    if not runs:
        return None
    runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return runs[0]

def _invoke_cpp(prompt: str, log_dir: Path, extra_args: List[str]) -> Tuple[int, str, str]:
    # Try 'cpp' command first, fall back to 'python -m cpp.cli' if not available
    # Test if 'cpp ask --help' works (to distinguish from C++ compiler)
    cmd = ["cpp", "ask", prompt, "--log-dir", str(log_dir), "--debug"] + extra_args
    try:
        test_proc = subprocess.run(
            ["cpp", "ask", "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=2,
        )
        if test_proc.returncode != 0:
            # 'cpp' exists but doesn't support 'ask', try module invocation
            cmd = [sys.executable, "-m", "cpp.cli", "ask", prompt, "--log-dir", str(log_dir), "--debug"] + extra_args
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # 'cpp' command not found, use module invocation
        cmd = [sys.executable, "-m", "cpp.cli", "ask", prompt, "--log-dir", str(log_dir), "--debug"] + extra_args
    
    # Provide input to advance through all ideas and quit
    # Send enough "next" commands (empty string = Enter = next, 100 should be more than enough) followed by "q" to quit
    # Each line is a separate input() call
    input_lines = [""] * 100 + ["q"]
    input_text = "\n".join(input_lines)
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        input=input_text,
        timeout=300,  # 5 minute timeout per run
    )
    return proc.returncode, proc.stdout, proc.stderr

def _load_run_json(run_path: Path) -> Dict:
    run_json = run_path / "run.json"
    if not run_json.exists():
        raise FileNotFoundError(f"Missing run.json in {run_path}")
    return json.loads(run_json.read_text(encoding="utf-8"))

def _summarize(run: Dict) -> Tuple[int,int,int,int,int]:
    """
    Returns (generated, hidden, shown, nlp_attempted, nlp_diagrams_present)

    generated: count of items where diagram_generated == true
    hidden: count where diagram_hidden == true
    shown: generated - hidden (diagrams that were generated and not hidden)
    nlp_attempted: count of items where nlp.attempted == true
    nlp_diagrams_present: count where nlp.diagram is not None
    Note: '(none)' from visualizer should set diagram_generated=false, so it won't count.
    """
    items = run.get("items", [])
    generated = sum(1 for it in items if it.get("diagram_generated") is True)
    hidden = sum(1 for it in items if it.get("diagram_hidden") is True)
    shown = max(0, generated - hidden)
    
    # NLP metrics (version 2+)
    nlp_attempted = 0
    nlp_diagrams_present = 0
    for it in items:
        nlp = it.get("nlp", {})
        if nlp.get("attempted") is True:
            nlp_attempted += 1
            if nlp.get("diagram") is not None:
                nlp_diagrams_present += 1
    
    return generated, hidden, shown, nlp_attempted, nlp_diagrams_present

def main() -> int:
    root = Path(__file__).resolve().parents[1]  # repo root when scripts/ is under repo
    prompts_path = root / "stress" / "prompts.json"
    log_dir = root / "runs_stress"

    # CLI overrides
    args = sys.argv[1:]
    if "--prompts" in args:
        i = args.index("--prompts")
        prompts_path = Path(args[i+1]).expanduser().resolve()
    if "--log-dir" in args:
        i = args.index("--log-dir")
        log_dir = Path(args[i+1]).expanduser().resolve()

    extra_args: List[str] = []
    if "--no-diagrams" in args:
        extra_args.append("--no-diagrams")

    prompts = _load_prompts(prompts_path)
    log_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = log_dir / f"_reports_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    summaries: List[RunSummary] = []

    for entry in prompts:
        pid = entry["id"]
        ptext = entry["prompt"]

        before_latest = _find_latest_run(log_dir)
        rc, out, err = _invoke_cpp(ptext, log_dir=log_dir, extra_args=extra_args)
        if rc != 0:
            print(f"[FAIL] {pid}: cpp exited {rc}\nSTDOUT:\n{out}\nSTDERR:\n{err}", file=sys.stderr)
            continue

        # Determine run folder: prefer newest folder after invocation
        after_latest = _find_latest_run(log_dir)
        run_path = after_latest if after_latest and after_latest != before_latest else after_latest or before_latest
        if run_path is None:
            print(f"[FAIL] {pid}: could not locate run folder in {log_dir}", file=sys.stderr)
            continue

        run = _load_run_json(run_path)
        ideas_count = int(run.get("ideas_count", len(run.get("items", []))) or 0)
        generated, hidden, shown, nlp_attempted, nlp_diagrams_present = _summarize(run)

        hidden_rate = (hidden / generated) if generated else 0.0
        summaries.append(RunSummary(
            prompt_id=pid,
            prompt=ptext,
            run_path=str(run_path),
            ideas_count=ideas_count,
            diagrams_generated=generated,
            diagrams_hidden=hidden,
            diagrams_shown=shown,
            hidden_rate=hidden_rate,
            nlp_attempted=nlp_attempted,
            nlp_diagrams_present=nlp_diagrams_present,
        ))

        # Save per-run stdout/stderr for debugging
        (out_dir / f"{pid}_stdout.txt").write_text(out, encoding="utf-8")
        (out_dir / f"{pid}_stderr.txt").write_text(err, encoding="utf-8")

    # Write CSV summary
    csv_path = out_dir / "stress_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["prompt_id","ideas_count","diagrams_generated","diagrams_shown","diagrams_hidden","hidden_rate","nlp_attempted","nlp_diagrams_present","run_path","prompt"])
        for s in summaries:
            w.writerow([s.prompt_id, s.ideas_count, s.diagrams_generated, s.diagrams_shown, s.diagrams_hidden, f"{s.hidden_rate:.3f}", s.nlp_attempted, s.nlp_diagrams_present, s.run_path, s.prompt])

    # Write markdown summary
    md_path = out_dir / "stress_summary.md"
    lines = []
    lines.append("# Stress Test Summary\n")
    lines.append(f"- Created: {stamp}\n")
    lines.append(f"- Log dir: `{log_dir}`\n")
    lines.append(f"- Prompts: `{prompts_path}`\n\n")
    lines.append("| Prompt ID | # Ideas | # Diagrams Generated | # Shown | # Hidden | Hidden Rate | NLP Attempted | NLP Diagrams | Run Path |\n")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---|\n")
    for s in summaries:
        lines.append(f"| {s.prompt_id} | {s.ideas_count} | {s.diagrams_generated} | {s.diagrams_shown} | {s.diagrams_hidden} | {s.hidden_rate:.3f} | {s.nlp_attempted} | {s.nlp_diagrams_present} | `{s.run_path}` |\n")
    md_path.write_text("".join(lines), encoding="utf-8")

    print(f"✅ Wrote reports to: {out_dir}")
    print(f"- {md_path}")
    print(f"- {csv_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
