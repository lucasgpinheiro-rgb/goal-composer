#!/usr/bin/env python3
"""Independent checks for a /goal run, outside the executor and without any model.

Usage:
  recheck_goal.py <slug>-proofs.json --baseline      before the /goal: prove the proofs are not vacuous
  recheck_goal.py <slug>-proofs.json [--expect-sha H] after the /goal: re-run everything, verdict DONE/NOT-DONE
  recheck_goal.py <slug>-proofs.json --attacks DIR    after the baseline: run each red-team attack script
                                                      in a throwaway git worktree, verdict CAUGHT/HOLE per attack

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
  catches       (targets) the wrong implementation or shortcut the proof fails on; recorded, not run
  external      true when the command has an external or paid effect (API, production host); --attacks
                never runs it, so N attacks never multiply those calls
Top level, for --attacks only:
  attack_copy   list of paths or globs, relative to the project root, of gitignored inputs the proofs
                need (.env, a test database). A git worktree starts without them; they are copied in.
Counters: value = first capture group of "regex", or the first integer in the output.
  rule no_decrease (final >= baseline) | no_increase (final <= baseline). Baseline values are stored in the file.
Pinned: a file or a whole directory (hash of sorted relative paths + file hashes; skips .git,
  __pycache__, node_modules, venvs). Get the hash with validate_goal.py --hash <path>.
Sample: after the verdict, prints n random files matching glob (first `lines` lines each) for human review.

Classification: a proof is BROKEN, not failed, when its command is not found (exit 126/127/9009 or a
"command not found" message) or when it fails on a missing module that is not part of the project, such as
pytest or requests not being installed. A missing module whose top-level package is a folder or .py file in
the project root or in src/ (tests.test_retry, billing.retry) is an ordinary failure: that is how a target
looks before the work is done. A unittest run that reports "Ran 0 tests" never passes, since Python before
3.12 exits 0 there while pytest and later versions exit 5.

Attacks (--attacks DIR): each *.sh in DIR is one cheap way to fake the work (a stub returning a
constant, a deleted test, a swallowed error), written by the red-team before the /goal. Header lines:
  # attacks: <criterion>[, <criterion>]     the target proof(s) the attack tries to make pass
  # break: <what the attack does>
The project is never touched. A temporary git worktree at HEAD (outside the project) gets a copy of the
spec's folder and of attack_copy. Control first: in that clean worktree every proof must exit with the
code the baseline recorded and every counter must equal its baseline value; otherwise the worktree does
not reproduce the project and every attack would look caught, so the run is BROKEN. Then, per attack:
reset the worktree, run the script with bash from the project root inside it, and judge
  NO-APPLY  the script failed, or changed no file (a no-op attack proves nothing)
  UNREACHED an attacked target fails with exactly its pre-attack output: the attack never reached
            what the proof checks, or the proof cannot pass at all (a verifier that fails to import)
  CAUGHT    an attacked target still fails, or it passes but a pin, counter or invariant fails
  HOLE      the attacked target passes and no guard fails: the proof can be fooled
  SKIPPED   an attacked target is external
Verdict ATTACKS OK (every attack CAUGHT or SKIPPED), ATTACKS HOLE (any HOLE), ATTACKS UNPROVEN
(any NO-APPLY or UNREACHED), BROKEN.
Needs a git repository whose tracked files are unchanged outside the spec's folder, and a --baseline
taken with this version (it records each proof's exit code). Attack scripts are code: read them first.

Exit codes: 0 DONE / BASELINE OK / ATTACKS OK, 1 NOT-DONE / BASELINE INVALID / ATTACKS HOLE or UNPROVEN,
2 BROKEN (spec or environment problem). Run from the project root.

Run log: every run appends one JSON line to recheck-log.jsonl next to the spec (goal, mode,
verdict, passed/total, counter values, proofs file SHA-256, expect_sha_ok, exit code, UTC time),
so a recheck run in a plain terminal still leaves a record. --no-log skips it. A failure to
write the log prints a warning and never changes the verdict or the exit code. Directory pins
ignore recheck-log.jsonl.
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
import tempfile

IS_WIN = os.name == "nt"
NOT_FOUND_CODES = {126, 127, 9009}
NOT_FOUND_RE = re.compile(
    r"command not found|is not recognized as an internal or external command|"
    r"is not recognized as the name of a cmdlet", re.I)
NO_MODULE_RE = re.compile(r"No module named ['\"]?([A-Za-z_][\w.]*)")
ZERO_TESTS_RE = re.compile(r"^Ran 0 tests? in ", re.M)
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
SKIP_FILES = {"recheck-log.jsonl"}  # the run log grows on every run; a pinned directory must not see it


def hash_path(path):
    """SHA-256 of a file, or of a directory tree (sorted relative paths + file hashes)."""
    if os.path.isfile(path):
        return sha256(path)
    if not os.path.isdir(path):
        raise FileNotFoundError(path)
    lines = []
    for root, dirs, files in os.walk(path):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(x for x in files if x not in SKIP_FILES):
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


def is_project_module(name):
    """True when the top-level package of a missing module is part of the project (run from its root)."""
    top = name.split(".")[0]
    return any(os.path.isdir(os.path.join(base, top)) or os.path.isfile(os.path.join(base, top + ".py"))
               for base in (".", "src"))


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
    rc = r.returncode
    broken = None
    if rc in NOT_FOUND_CODES or (rc != 0 and NOT_FOUND_RE.search(out)):
        broken = f"command not found (exit {rc})"
    elif rc != 0:
        # A missing tool or package (pytest, requests) is an environment problem. A missing project
        # module (tests.test_retry, billing.retry) is what a target looks like before the work.
        external = [m for m in NO_MODULE_RE.findall(out) if not is_project_module(m)]
        if external:
            broken = f"module not installed: {external[0]} (exit {rc})"
    return {"rc": rc, "out": out, "timeout": False, "broken": broken}


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
    if ZERO_TESTS_RE.search(res["out"]):
        problems.append("ran 0 tests")
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


LOG_NAME = "recheck-log.jsonl"


def write_log(a, rec):
    """Append one line per run to <spec dir>/recheck-log.jsonl, so every baseline and recheck
    leaves a record even when it runs outside Claude Code. Never changes the verdict or exit code."""
    if a.no_log:
        return
    rec["ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    try:
        rec["proofs_sha256"] = sha256(a.spec)
    except OSError:
        rec["proofs_sha256"] = None
    path = os.path.join(os.path.dirname(os.path.abspath(a.spec)), LOG_NAME)
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
    except OSError as e:
        print(f"LOG     WARN    could not append to {path}: {e}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--baseline", action="store_true", help="run before the /goal and record counters")
    ap.add_argument("--expect-sha", help="SHA-256 of the proofs file as delivered")
    ap.add_argument("--seed", type=int, help="seed for the sample (default: random)")
    ap.add_argument("--no-log", action="store_true", help=f"do not append this run to {LOG_NAME} next to the spec")
    ap.add_argument("--attacks", metavar="DIR", help="run the red-team attack scripts in DIR (after --baseline)")
    a = ap.parse_args()
    if a.attacks and a.baseline:
        ap.error("--attacks runs after the baseline, not together with it")
    rec = {"goal": re.sub(r"-proofs\.json$", "", os.path.basename(a.spec)), "spec": a.spec,
           "mode": "attacks" if a.attacks else "baseline" if a.baseline else "recheck", "expect_sha_ok": None,
           "verdict": None, "passed": None, "total": None, "counters": {}, "exit": None}
    code = run(a, rec)
    rec["exit"] = code
    write_log(a, rec)
    return code


def run(a, rec):
    if a.expect_sha:
        actual = sha256(a.spec)
        rec["expect_sha_ok"] = actual.lower() == a.expect_sha.lower()
        if actual.lower() != a.expect_sha.lower():
            print(f"SPEC    BROKEN  {a.spec} changed since delivery\n        expected {a.expect_sha}\n        actual   {actual}")
            print("\nVERDICT: BROKEN (the proofs file itself was modified; nothing below it can be trusted)")
            rec["verdict"] = "BROKEN"
            return 2
        print(f"SPEC    OK      {a.spec} matches the delivered hash")

    try:
        spec = json.load(open(a.spec, encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"SPEC    BROKEN  cannot read {a.spec}: {e}\n\nVERDICT: BROKEN")
        rec["verdict"] = "BROKEN"
        return 2
    rec["goal"] = spec.get("goal") or rec["goal"]
    if not spec.get("proofs"):
        print("SPEC    BROKEN  no proofs listed\n\nVERDICT: BROKEN")
        rec["verdict"] = "BROKEN"
        return 2

    bash = find_bash()
    if a.attacks:
        return run_attacks(a, rec, spec, bash)
    mode = "BASELINE" if a.baseline else "RECHECK"
    print(f"{mode} | bash: {bash or 'not found'} | python: {sys.executable}\n")
    fails, broken, total = 0, 0, 0
    rcs = []  # exit code per proof, recorded at baseline for the --attacks control

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
        rcs.append(None if res["timeout"] else res["rc"])
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
        rec["counters"][name] = val
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
    rec["passed"], rec["total"] = passed, total
    if broken:
        print(f"\nVERDICT: BROKEN ({broken} check(s) could not run; fix the spec or environment, not the work)")
        rec["verdict"] = "BROKEN"
        return 2
    if a.baseline:
        if fails:
            print(f"\nVERDICT: BASELINE INVALID ({fails} problem(s)); fix the proofs before starting the /goal")
            rec["verdict"] = "BASELINE INVALID"
            return 1
        spec["baseline"] = {"taken_at": datetime.datetime.now().isoformat(timespec="seconds"),
                            "counters": measured, "proof_rc": rcs}
        with open(a.spec, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"\nVERDICT: BASELINE OK ({passed}/{total})")
        print(f"Proofs file SHA-256 (use with --expect-sha after the /goal): {sha256(a.spec)}")
        rec["verdict"] = "BASELINE OK"
        return 0
    verdict = "DONE" if fails == 0 else "NOT-DONE"
    rec["verdict"] = verdict
    print(f"\nVERDICT: {verdict} ({passed}/{total} checks passed)")
    print_sample(spec, a.seed if a.seed is not None else random.randrange(10**6))
    return 0 if fails == 0 else 1


# ---------------------------------------------------------------- attacks

GLOB_CHARS = re.compile(r"([*?\[\]\\!#])")


def git(args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def fingerprint(root):
    """(size, mtime_ns) of every file under root except .git: enough to tell whether anything changed."""
    fp = {}
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            if f == ".git":
                continue
            full = os.path.join(r, f)
            try:
                st = os.stat(full)
            except OSError:
                continue
            fp[os.path.relpath(full, root)] = (st.st_size, st.st_mtime_ns)
    return fp


def stat_fp(path):
    if os.path.isdir(path):
        return fingerprint(path)
    try:
        st = os.stat(path)
        return (st.st_size, st.st_mtime_ns)
    except OSError:
        return None


def attack_header(path):
    targets, brk = None, ""
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = re.match(r"\s*#\s*attacks:\s*(.+)", line, re.I)
            if m:
                targets = [t.strip() for t in m.group(1).split(",") if t.strip()]
            m = re.match(r"\s*#\s*break:\s*(.+)", line, re.I)
            if m:
                brk = m.group(1).strip()
    return targets, brk


def proof_state(p, bash):
    """'pass' | 'fail' | 'broken' | 'timeout', with a short reason."""
    res = execute(p, bash)
    if res["broken"]:
        return "broken", res["broken"], res
    if res["timeout"]:
        return "timeout", "timeout", res
    ok, problems = passes(p, res)
    return ("pass", "", res) if ok else ("fail", "; ".join(problems), res)


def broken_attacks(rec, msg):
    print(f"ATTACKS BROKEN  {msg}\n\nVERDICT: BROKEN")
    rec["verdict"] = "BROKEN"
    return 2


def run_attacks(a, rec, spec, bash):
    proj = os.getcwd()
    spec_abs = os.path.abspath(a.spec)
    attacks_dir = os.path.abspath(a.attacks)
    print(f"ATTACKS | bash: {bash or 'not found'} | python: {sys.executable}\n")
    if not bash:
        return broken_attacks(rec, "bash not found (Windows: install Git for Windows or set CLAUDE_CODE_GIT_BASH_PATH)")
    if not shutil.which("git"):
        return broken_attacks(rec, "git not found")
    scripts = sorted(glob.glob(os.path.join(attacks_dir, "*.sh")))
    if not scripts:
        return broken_attacks(rec, f"no *.sh attack scripts in {a.attacks}")

    r = git(["rev-parse", "--show-toplevel"], proj)
    if r.returncode != 0:
        return broken_attacks(rec, "attacks need a git repository (fall back to the prose red-team and say so)")
    top = os.path.normpath(r.stdout.strip())
    prefix = git(["rev-parse", "--show-prefix"], proj).stdout.strip()  # project root inside the repo, "" or "sub/"
    goals_rel = os.path.relpath(os.path.dirname(spec_abs), proj).replace(os.sep, "/")
    if goals_rel.startswith(".."):
        return broken_attacks(rec, "the proofs file must be inside the project")

    st = git(["status", "--porcelain", "--untracked-files=no"], proj)
    dirty = [ln[3:] for ln in st.stdout.splitlines()
             if ln[3:] and not ln[3:].strip('"').startswith(f"{prefix}{goals_rel}/")]
    if dirty:
        return broken_attacks(rec, "tracked files changed since HEAD, so a worktree at HEAD is not the starting "
                                   f"state the baseline measured; commit or stash first: {', '.join(dirty[:5])}")

    proofs = spec["proofs"]
    base = spec.get("baseline") or {}
    base_rc, base_counters = base.get("proof_rc"), base.get("counters", {})
    if not isinstance(base_rc, list) or len(base_rc) != len(proofs):
        return broken_attacks(rec, "no per-proof exit codes in the baseline; rerun --baseline with this version")
    known = {str(p.get("criterion")) for p in proofs if p.get("kind", "target") == "target"}

    copies = []
    for pat in spec.get("attack_copy", []):
        hits = [os.path.relpath(h, proj).replace(os.sep, "/") for h in glob.glob(os.path.join(proj, pat), recursive=True)]
        if not hits:
            return broken_attacks(rec, f"attack_copy entry '{pat}' matches nothing in the project")
        copies += hits

    tmp = os.path.realpath(tempfile.mkdtemp(prefix="goal-attacks-"))
    wt = os.path.join(tmp, "wt")
    wproj = os.path.normpath(os.path.join(wt, prefix))
    verdicts, results = {}, []
    try:
        r = git(["worktree", "add", "--detach", "-q", wt, "HEAD"], top)
        if r.returncode != 0:
            return broken_attacks(rec, f"git worktree add failed: {r.stderr.strip()[:300]}")
        excludes = [f"/{prefix}{p}" for p in [goals_rel, *copies]]
        copy_fp = {}

        def install_inputs(force):
            dst = os.path.join(wproj, goals_rel)
            shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(os.path.dirname(spec_abs), dst)
            for c in copies:
                src, d = os.path.join(proj, c), os.path.join(wproj, c)
                if not force and stat_fp(d) == copy_fp.get(c):
                    continue  # unchanged since copied: skip re-copying a large input
                if os.path.isdir(src):
                    shutil.rmtree(d, ignore_errors=True)
                    shutil.copytree(src, d)
                else:
                    os.makedirs(os.path.dirname(d), exist_ok=True)
                    shutil.copy2(src, d)
                copy_fp[c] = stat_fp(d)

        def reset():
            # only ever inside the throwaway worktree
            assert os.path.realpath(wt).startswith(tmp) and os.path.normcase(os.path.realpath(wt)) != os.path.normcase(os.path.realpath(top))
            os.chdir(tmp)
            git(["reset", "--hard", "-q", "HEAD"], wt)
            git(["clean", "-fdxq", *[x for e in excludes for x in ("-e", GLOB_CHARS.sub(r"\\\1", e))]], wt)
            install_inputs(force=False)
            os.chdir(wproj)

        install_inputs(force=True)
        os.chdir(wproj)

        # Control: the clean worktree must reproduce the baseline, or every attack would look caught.
        mismatch, ctl_out = [], {}
        for i, p in enumerate(proofs):
            if p.get("external"):
                continue
            state, why, res = proof_state(p, bash)
            ctl_out[i] = res["out"]
            got = None if state in ("broken", "timeout") else res["rc"]
            if got != base_rc[i]:
                mismatch.append(f"[{p.get('criterion', '?')}] {label(p)}: exit {got if got is not None else why}, baseline {base_rc[i]}")
        for c in spec.get("counters", []):
            if c.get("external"):
                continue
            val = counter_value(c, execute(c, bash))
            if val != base_counters.get(c.get("name")):
                mismatch.append(f"counter {c.get('name')} = {val}, baseline {base_counters.get(c.get('name'))}")
        for pin in spec.get("pinned", []):
            try:
                ok = hash_path(pin["path"]).lower() == str(pin.get("sha256", "")).lower()
            except (FileNotFoundError, KeyError):
                ok = False
            if not ok:
                mismatch.append(f"pin {pin.get('path')} differs or is missing in the worktree")
        if mismatch:
            for m in mismatch:
                print(f"CONTROL FAIL    {m}")
            return broken_attacks(rec, "the clean worktree does not reproduce the baseline (a gitignored input "
                                       "missing from attack_copy?), so attacks cannot be judged")
        print("CONTROL OK      the clean worktree reproduces the baseline\n")

        for s in scripts:
            name = os.path.basename(s)
            reset()
            targets, brk = attack_header(s)
            if not targets or not set(targets) <= known:
                v, why = "BROKEN", f"header must name target criteria with '# attacks: <criterion>' (targets: {', '.join(sorted(known))})"
            else:
                attacked = [p for p in proofs if p.get("kind", "target") == "target" and str(p.get("criterion")) in targets]
                before = fingerprint(wt)
                try:
                    ar = subprocess.run([bash, s.replace("\\", "/")], cwd=wproj, capture_output=True, text=True,
                                        encoding="utf-8", errors="replace", timeout=300)
                except subprocess.TimeoutExpired:
                    ar = subprocess.CompletedProcess([], 124, "", "timed out after 300 s")
                if ar.returncode != 0:
                    tail = " | ".join((ar.stdout + ar.stderr).strip().splitlines()[-3:])
                    v, why = "NO-APPLY", f"the script exited {ar.returncode}" + (f": {tail}" if tail else "")
                elif fingerprint(wt) == before:
                    v, why = "NO-APPLY", "the script changed no file, so it proves nothing"
                elif any(p.get("external") for p in attacked):
                    v, why = "SKIPPED", "an attacked target is external"
                else:
                    v, why = None, ""
                    for p in attacked:
                        state, reason, res = proof_state(p, bash)
                        if state != "pass":
                            if res["out"] == ctl_out.get(proofs.index(p)):
                                # Same output as before the attack: the proof never saw the change, or it
                                # cannot pass at all (e.g. a verifier that fails to import). Not a catch.
                                v, why = "UNREACHED", (f"[{p.get('criterion')}] fails with exactly the output it had "
                                                       "before the attack: the attack never reached what the proof "
                                                       "checks, the proof cannot pass at all, or it prints "
                                                       "nothing that changes (make it print what it checks)")
                            else:
                                v, why = "CAUGHT", f"[{p.get('criterion')}] still fails ({reason or state})"
                            break
                    if v is None:
                        why = f"[{', '.join(targets)}] passes, "
                        for pin in spec.get("pinned", []):
                            try:
                                ok = hash_path(pin["path"]).lower() == str(pin.get("sha256", "")).lower()
                            except (FileNotFoundError, KeyError):
                                ok = False
                            if not ok:
                                v, why = "CAUGHT", why + f"but pin {pin.get('path')} changed"
                                break
                    if v is None:
                        for c in spec.get("counters", []):
                            if c.get("external"):
                                continue
                            val, b = counter_value(c, execute(c, bash)), base_counters.get(c.get("name"))
                            rule = c.get("rule", "no_decrease")
                            if val is None or not (val >= b if rule == "no_decrease" else val <= b):
                                v, why = "CAUGHT", why + f"but counter {c.get('name')} = {val} (baseline {b}, {rule})"
                                break
                    if v is None:
                        for p in proofs:
                            if p.get("kind") == "invariant" and not p.get("external"):
                                state, reason, _ = proof_state(p, bash)
                                if state != "pass":
                                    v, why = "CAUGHT", why + f"but invariant [{p.get('criterion')}] fails ({reason or state})"
                                    break
                    if v is None:
                        skipped = [f"[{p.get('criterion')}]" for p in proofs
                                   if p.get("external") and p.get("kind") == "invariant"]
                        skipped += [f"counter {c.get('name')}" for c in spec.get("counters", []) if c.get("external")]
                        v, why = "HOLE", why + "and no pin, counter or invariant fails" + (
                            f" (external guards not run: {', '.join(skipped)})" if skipped else "")
            verdicts[name] = v
            results.append((name, v, why, brk))
            print(f"ATTACK  {v:<8} {name}: {why}" + (f"\n        break: {brk}" if brk else ""))
    except SpecError as e:
        return broken_attacks(rec, f"a proof or counter is malformed: {e}")
    finally:
        os.chdir(proj)
        git(["worktree", "remove", "--force", wt], top)
        shutil.rmtree(tmp, ignore_errors=True)
        git(["worktree", "prune"], top)

    rec["attacks"] = verdicts
    n = len(results)
    caught = sum(1 for _, v, _, _ in results if v == "CAUGHT")
    skipped = sum(1 for _, v, _, _ in results if v == "SKIPPED")
    rec["passed"], rec["total"] = caught, n
    if any(v == "BROKEN" for v in verdicts.values()):
        print("\nVERDICT: BROKEN (an attack script is malformed; fix it, not the proofs)")
        rec["verdict"] = "BROKEN"
        return 2
    holes = [k for k, v in verdicts.items() if v == "HOLE"]
    if holes:
        print(f"\nVERDICT: ATTACKS HOLE ({caught}/{n} caught; holes: {', '.join(holes)})")
        rec["verdict"] = "ATTACKS HOLE"
        return 1
    if any(v in ("NO-APPLY", "UNREACHED") for v in verdicts.values()):
        print(f"\nVERDICT: ATTACKS UNPROVEN ({caught}/{n} caught; rewrite each NO-APPLY attack until it changes "
              "the code, and check each UNREACHED proof can pass at all)")
        rec["verdict"] = "ATTACKS UNPROVEN"
        return 1
    print(f"\nVERDICT: ATTACKS OK ({caught}/{n} caught" + (f", {skipped} skipped as external" if skipped else "") + ")")
    rec["verdict"] = "ATTACKS OK"
    return 0


if __name__ == "__main__":
    sys.exit(main())
