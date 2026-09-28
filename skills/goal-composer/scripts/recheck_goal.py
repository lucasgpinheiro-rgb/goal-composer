#!/usr/bin/env python3
"""Independent checks for a /goal run, outside the executor and without any model.

Usage:
  recheck_goal.py <slug>-proofs.json --baseline      before the /goal: prove the proofs are not vacuous
  recheck_goal.py <slug>-proofs.json [--expect-sha H] after the /goal: re-run everything, verdict DONE/NOT-DONE

Why: the /goal evaluator only reads the transcript and never runs anything, so it
cannot tell a fresh output from a stale, partial or cherry-picked one. And a proof
that already passes before the work starts measures nothing.

proofs.json:
{
  "goal": "<slug>",
  "proofs": [
    {"criterion": "1", "kind": "target", "command": "{python} -m pytest tests/test_x.py::test_new -q"},
    {"criterion": "2", "kind": "invariant", "command": "{python} -m pytest -q"},
    {"criterion": "3", "kind": "target", "command": "{python} .claude/goals/x-verify.py",
     "expect_regex": "^PASS", "expect_exit": 0, "timeout": 900}
  ],
  "counters": [
    {"name": "tests", "command": "{python} -m pytest --collect-only -q",
     "regex": "(\\\\d+) tests? collected", "rule": "no_decrease"}
  ],
  "pinned": [{"path": ".claude/goals/x-verify.py", "sha256": "<64 hex>"},
             {"path": "sources/", "sha256": "<64 hex>"}],
  "sample": {"glob": "out/**/*.md", "n": 5, "lines": 20}
}

Fields per proof or counter:
  kind          target (must FAIL at baseline, PASS at the end) | invariant (must PASS both times). Default target.
  shell         bash (default; Git Bash on Windows, same shell Claude Code uses) | system (cmd.exe / sh) | none (argv, no shell)
  command       string for bash/system; "{python}" is replaced by this interpreter
  argv          list for shell "none"; an item equal to "{python}" is replaced by this interpreter
  expect_exit   default 0 when expect_regex is absent
  expect_regex  searched in stdout+stderr (multiline)
  timeout       seconds, default 600
Counters: value = first capture group of "regex", or the first integer in the output.
  rule no_decrease (final >= baseline) | no_increase (final <= baseline). Baseline values are stored in the file.
Pinned: a file or a whole directory (hash of sorted relative paths + file hashes; skips .git,
  __pycache__, node_modules, venvs). Get the hash with validate_goal.py --hash <path>.
Sample: after the verdict, prints n random files matching glob (first `lines` lines each) for human review.

Exit codes: 0 DONE / BASELINE OK, 1 NOT-DONE / BASELINE INVALID, 2 BROKEN (spec or environment problem).
Run from the project root.
"""
import argparse
import datetime
import glob
import hashlib
import json
import os
import random
import re
import shlex
import shutil
import subprocess
import sys

IS_WIN = os.name == "nt"
NOT_FOUND_CODES = {126, 127, 9009}
NOT_FOUND_RE = re.compile(
    r"command not found|is not recognized as an internal or external command|"
    r"is not recognized as the name of a cmdlet|No module named", re.I)
TAIL = 15


class SpecError(Exception):
    pass


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}


def hash_path(path):
    """SHA-256 of a file, or of a directory tree (sorted relative paths + file hashes)."""
    if os.path.isfile(path):
        return sha256(path)
    if not os.path.isdir(path):
        raise FileNotFoundError(path)
    lines = []
    for root, dirs, files in os.walk(path):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            full = os.path.join(root, f)
            rel = os.path.relpath(full, path).replace(os.sep, "/")
            lines.append(f"{rel}\t{sha256(full)}")
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def find_bash():
    if not IS_WIN:
        return shutil.which("bash")
    cands = [os.environ.get("CLAUDE_CODE_GIT_BASH_PATH")]
    for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"),
                 os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs")):
        if base:
            cands.append(os.path.join(base, "Git", "bin", "bash.exe"))
    w = shutil.which("bash")
    # System32\bash.exe and WindowsApps\bash.exe are WSL: different filesystem, wrong shell
    if w and not re.search(r"[\\/](system32|windowsapps)[\\/]", w, re.I):
        cands.append(w)
    for c in cands:
        if c and os.path.isfile(c):
            return c
    return None


def python_token(shell):
    exe = sys.executable
    if shell == "bash":
        return shlex.quote(exe.replace("\\", "/"))
    if shell == "system" and IS_WIN:
        return f'"{exe}"'
    return shlex.quote(exe)


def label(item):
    if item.get("shell") == "none":
        return " ".join(map(str, item.get("argv", [])))
    return item.get("command", "<no command>")


def execute(item, bash):
    """Return dict(rc, out, broken, timeout)."""
    shell = item.get("shell", "bash")
    timeout = item.get("timeout", 600)
    if shell == "none":
        argv = item.get("argv")
        if not isinstance(argv, list) or not argv:
            raise SpecError("shell 'none' requires a non-empty 'argv' list")
        cmd, use_shell = [sys.executable if a == "{python}" else str(a) for a in argv], False
    elif shell in ("bash", "system"):
        c = item.get("command")
        if not c:
            raise SpecError("missing 'command'")
        c = c.replace("{python}", python_token(shell))
        if shell == "bash":
            if not bash:
                return {"rc": None, "out": "", "timeout": False,
                        "broken": "bash not found (Windows: install Git for Windows or set CLAUDE_CODE_GIT_BASH_PATH)"}
            cmd, use_shell = [bash, "-c", c], False
        else:
            cmd, use_shell = c, True
    else:
        raise SpecError(f"unknown shell '{shell}'")
    try:
        r = subprocess.run(cmd, shell=use_shell, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
    except FileNotFoundError as e:
        return {"rc": None, "out": "", "timeout": False, "broken": f"executable not found: {e.filename}"}
    except subprocess.TimeoutExpired:
        return {"rc": None, "out": "", "timeout": True, "broken": None}
    out = (r.stdout or "") + (r.stderr or "")
    broken = None
    if r.returncode in NOT_FOUND_CODES or (r.returncode != 0 and NOT_FOUND_RE.search(out)):
        broken = f"command or module not found (exit {r.returncode})"
    return {"rc": r.returncode, "out": out, "timeout": False, "broken": broken}


def passes(item, res):
    exp_exit, exp_re = item.get("expect_exit"), item.get("expect_regex")
    if exp_exit is None and exp_re is None:
        exp_exit = 0
    problems = []
    if res["timeout"]:
        return False, ["timeout"]
    if exp_exit is not None and res["rc"] != exp_exit:
        problems.append(f"exit {res['rc']}, expected {exp_exit}")
    if exp_re is not None and not re.search(exp_re, res["out"], re.MULTILINE):
        problems.append(f"output does not match /{exp_re}/")
    return not problems, problems


def show_tail(out):
    for line in out.strip().splitlines()[-TAIL:]:
        print(f"        | {line}")


def counter_value(item, res):
    if res["broken"] or res["timeout"]:
        return None
    rx = item.get("regex")
    m = re.search(rx, res["out"], re.MULTILINE) if rx else re.search(r"-?\d+", res["out"])
    if not m:
        return None
    try:
        return int(m.group(1) if (rx and m.groups()) else m.group(0))
    except ValueError:
        return None


def print_sample(spec, rng_seed):
    s = spec.get("sample")
    if not s:
        return
    files = sorted(f for f in glob.glob(s["glob"], recursive=True) if os.path.isfile(f))
    n, lines = s.get("n", 5), s.get("lines", 20)
    print(f"\nSAMPLE for human review: {min(n, len(files))} of {len(files)} files matching {s['glob']} (seed {rng_seed})")
    if not files:
        print("        no files matched")
        return
    for f in random.Random(rng_seed).sample(files, min(n, len(files))):
        print(f"\n--- {f}")
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                for i, line in enumerate(fh):
                    if i >= lines:
                        print("        [...]")
                        break
                    print("    " + line.rstrip("\n"))
        except OSError as e:
            print(f"        unreadable: {e}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--baseline", action="store_true", help="run before the /goal and record counters")
    ap.add_argument("--expect-sha", help="SHA-256 of the proofs file as delivered")
    ap.add_argument("--seed", type=int, help="seed for the sample (default: random)")
    a = ap.parse_args()

    if a.expect_sha:
        actual = sha256(a.spec)
        if actual.lower() != a.expect_sha.lower():
            print(f"SPEC    BROKEN  {a.spec} changed since delivery\n        expected {a.expect_sha}\n        actual   {actual}")
            print("\nVERDICT: BROKEN (the proofs file itself was modified; nothing below it can be trusted)")
            return 2
        print(f"SPEC    OK      {a.spec} matches the delivered hash")

    try:
        spec = json.load(open(a.spec, encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"SPEC    BROKEN  cannot read {a.spec}: {e}\n\nVERDICT: BROKEN")
        return 2
    if not spec.get("proofs"):
        print("SPEC    BROKEN  no proofs listed\n\nVERDICT: BROKEN")
        return 2

    bash = find_bash()
    mode = "BASELINE" if a.baseline else "RECHECK"
    print(f"{mode} | bash: {bash or 'not found'} | python: {sys.executable}\n")
    fails, broken, total = 0, 0, 0

    for pin in spec.get("pinned", []):
        total += 1
        try:
            actual = hash_path(pin["path"])
        except (FileNotFoundError, KeyError):
            print(f"PINNED  FAIL    {pin.get('path')}: missing")
            fails += 1
            continue
        if actual.lower() == str(pin.get("sha256", "")).lower():
            print(f"PINNED  OK      {pin['path']}")
        else:
            print(f"PINNED  FAIL    {pin['path']}\n        expected {pin.get('sha256')}\n        actual   {actual}")
            fails += 1

    for p in spec["proofs"]:
        total += 1
        kind = p.get("kind", "target")
        tag = f"[{p.get('criterion', '?')}|{kind}] {label(p)}"
        try:
            if kind not in ("target", "invariant"):
                raise SpecError(f"unknown kind '{kind}'")
            res = execute(p, bash)
        except SpecError as e:
            print(f"PROOF   BROKEN  {tag}: {e}")
            broken += 1
            continue
        if res["broken"]:
            print(f"PROOF   BROKEN  {tag}: {res['broken']}")
            show_tail(res["out"])
            broken += 1
            continue
        ok, problems = passes(p, res)
        if a.baseline and kind == "target":
            if ok:
                print(f"PROOF   VACUOUS {tag}: already passes before any work, so it measures nothing")
                show_tail(res["out"])
                fails += 1
            else:
                print(f"PROOF   OK      {tag}: fails now, as a target must ({'; '.join(problems)})")
        elif a.baseline and kind == "invariant" and not ok:
            print(f"PROOF   INVALID {tag}: an invariant must hold now ({'; '.join(problems)})")
            show_tail(res["out"])
            fails += 1
        elif ok:
            print(f"PROOF   OK      {tag}")
        else:
            print(f"PROOF   FAIL    {tag}: {'; '.join(problems)}")
            show_tail(res["out"])
            fails += 1

    measured = {}
    base = (spec.get("baseline") or {}).get("counters", {})
    for c in spec.get("counters", []):
        total += 1
        name, rule = c.get("name", "?"), c.get("rule", "no_decrease")
        try:
            if rule not in ("no_decrease", "no_increase"):
                raise SpecError(f"unknown rule '{rule}'")
            res = execute(c, bash)
        except SpecError as e:
            print(f"COUNTER BROKEN  {name}: {e}")
            broken += 1
            continue
        val = counter_value(c, res)
        if val is None:
            print(f"COUNTER BROKEN  {name}: {res['broken'] or 'no integer found in the output'}")
            show_tail(res["out"])
            broken += 1
            continue
        if a.baseline:
            measured[name] = val
            print(f"COUNTER OK      {name} = {val} (recorded, rule {rule})")
            continue
        if name not in base:
            print(f"COUNTER BROKEN  {name}: no baseline recorded (run --baseline before the /goal)")
            broken += 1
            continue
        ok = val >= base[name] if rule == "no_decrease" else val <= base[name]
        print(f"COUNTER {'OK    ' if ok else 'FAIL  '}  {name} = {val} (baseline {base[name]}, {rule})")
        fails += 0 if ok else 1

    passed = total - fails - broken
    if broken:
        print(f"\nVERDICT: BROKEN ({broken} check(s) could not run; fix the spec or environment, not the work)")
        return 2
    if a.baseline:
        if fails:
            print(f"\nVERDICT: BASELINE INVALID ({fails} problem(s)); fix the proofs before starting the /goal")
            return 1
        spec["baseline"] = {"taken_at": datetime.datetime.now().isoformat(timespec="seconds"),
                            "counters": measured}
        with open(a.spec, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"\nVERDICT: BASELINE OK ({passed}/{total})")
        print(f"Proofs file SHA-256 (use with --expect-sha after the /goal): {sha256(a.spec)}")
        return 0
    verdict = "DONE" if fails == 0 else "NOT-DONE"
    print(f"\nVERDICT: {verdict} ({passed}/{total} checks passed)")
    print_sample(spec, a.seed if a.seed is not None else random.randrange(10**6))
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
