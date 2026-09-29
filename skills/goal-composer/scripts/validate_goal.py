#!/usr/bin/env python3
"""Validate a /goal mandate (length, required sections, weak-condition signals).

Usage:
  validate_goal.py <mandate-file>
  validate_goal.py --hash <path>     print SHA-256 of a file or directory (for pinning)

Accepts Portuguese or English section labels.
"""
import hashlib
import re
import sys
import unicodedata

MAX_CHARS = 4000
TARGET = 3800

REQUIRED = {
    "OBJECTIVE": ["OBJECTIVE:", "OBJETIVO:"],
    "DONE WHEN": ["DONE WHEN", "CONCLUIDO QUANDO"],
    "SCOPE": ["SCOPE:", "ESCOPO:"],
    "CONSTRAINTS": ["CONSTRAINTS:", "RESTRICOES:"],
    "STOP": ["STOP:", "PARADA:"],
}
RECOMMENDED = {
    "PER-TURN PROTOCOL": ["PER-TURN PROTOCOL", "PROTOCOLO POR TURNO"],
    "EXTERNAL EFFECTS": ["EXTERNAL EFFECTS", "EFEITOS EXTERNOS"],
}
VAGUE = [
    "robust", "clean code", "production-ready", "production ready", "well structured",
    "high quality", "optimized", "elegant", "robusto", "limpo", "pronto para producao",
    "bem estruturado", "funcionando bem", "otimizado", "elegante", "de qualidade",
]
UNBOUNDED = [
    "everything", "completely", "entire codebase", "whole project", "whole codebase",
    "tudo", "completamente", "totalmente", "todo o projeto", "todo o codigo", "projeto inteiro", "codigo inteiro",
]
UNDETECTABLE_STOP = [
    "if unclear", "if in doubt", "if confused", "if stuck", "when unsure",
    "se nao estiver claro", "em caso de duvida", "se estiver confuso", "se tiver duvida", "se travar",
]


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).upper()


def any_in(t: str, keys) -> bool:
    return any(k in t for k in keys)


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
SKIP_FILES = {"recheck-log.jsonl"}  # same as recheck_goal.py: the run log is not part of any pin


def hash_path(path: str) -> str:
    """Same algorithm as recheck_goal.py: file hash, or directory tree hash."""
    import os
    if os.path.isfile(path):
        return sha256(path)
    lines = []
    for root, dirs, files in os.walk(path):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(x for x in files if x not in SKIP_FILES):
            full = os.path.join(root, f)
            rel = os.path.relpath(full, path).replace(os.sep, "/")
            lines.append(f"{rel}\t{sha256(full)}")
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def validate(path: str) -> int:
    text = open(path, encoding="utf-8").read().strip()
    errors, warnings = [], []

    # Claude Code runs on JS: counting UTF-16 code units is the conservative measure
    n_cp = len(text)
    n_u16 = len(text.encode("utf-16-le")) // 2
    if text.lower().startswith("/goal"):
        errors.append("remove the '/goal' prefix from the file; it is typed separately")
    if n_u16 > MAX_CHARS:
        errors.append(f"{n_u16} characters: exceeds the {MAX_CHARS} limit")
    elif n_u16 > TARGET:
        warnings.append(f"{n_u16} characters: above the {TARGET} safety margin")

    t = norm(text)
    for name, keys in REQUIRED.items():
        if not any_in(t, keys):
            errors.append(f"missing required section: {name}")
    for name, keys in RECOMMENDED.items():
        if not any_in(t, keys):
            warnings.append(f"missing recommended section: {name}")

    n_proofs = len(re.findall(r"\b(PROOF|PROVA):", t))
    if n_proofs == 0:
        errors.append("no criterion has 'proof:'; the evaluator will have nothing to read")
    if not any_in(t, ["BLOCKED", "BLOQUEADO"]):
        errors.append("missing 'BLOCKED' exit in the stop clause")

    # The exit must be a branch that SATISFIES the condition, not a policy about it:
    # an evaluator counted three BLOQUEADO lines, quoted the policy, and still answered
    # not-met four times (2026-09-25). See "Why each piece exists" in SKILL.md.
    done = re.search(r"(DONE WHEN|CONCLUIDO QUANDO)(.*?)(\n\s*(SCOPE|ESCOPO):|\Z)", t, re.S)
    if done:
        body = done.group(2)
        if not (re.search(r"\(B\)", body) and any_in(body, ["BLOCKED", "BLOQUEADO"])
                and any_in(body, ["LIMIT REACHED", "LIMITE ATINGIDO"])):
            errors.append("DONE WHEN has no branch (B) that ends the goal on three BLOCKED lines "
                          "or LIMIT REACHED; a blocked run would be relaunched without end")
    stop = re.search(r"(?:^|\n)\s*(STOP|PARADA):(.*)", t, re.S)
    if stop:
        body = stop.group(2)
        if not re.search(r"/\s*3\b", body):
            errors.append("STOP has no three-strike line (e.g. 'BLOCKED (<k>/3): waiting for the user')")
        if not any_in(body, ["SCOPE", "ESCOPO"]):
            warnings.append("STOP has no generic situation 'a needed change falls outside SCOPE "
                            "or against a CONSTRAINT'")
    if not re.search(r"\d+\s*(TURNS|TURNOS)", t):
        errors.append("missing numeric turn limit (e.g. '30 turns')")
    if not any_in(t, ["FORBIDDEN", "PROIBIDO"]):
        warnings.append("no list of forbidden shortcuts")
    if not any_in(t, ["TASKS", "CHECKLIST"]):
        warnings.append("no checklist file (e.g. .claude/goals/<slug>-tasks.md)")
    if re.search(r"VERIFIER|VERIFICADOR|-VERIFY\.", t) and not re.search(r"\b[0-9A-F]{64}\b", t):
        warnings.append("mentions a verifier but no SHA-256 hash is pinned in the mandate")

    import os
    design = re.sub(r"\.md$", "", path) + "-design.md"
    design_name = os.path.basename(design)
    if os.path.exists(design) and design_name.upper() not in t:
        warnings.append(f"{design_name} exists but the mandate does not cite it "
                        "(FIRST ACTION reads it; CONSTRAINTS bind its approach)")
    proofs = re.sub(r"\.md$", "", path) + "-proofs.json"
    if not os.path.exists(proofs):
        warnings.append(f"no proofs file for the independent recheck: {proofs}")
    else:
        import json
        try:
            ps = json.load(open(proofs, encoding="utf-8"))
            if not any(p.get("kind", "target") == "target" for p in ps.get("proofs", [])):
                warnings.append("proofs file has no 'target' proof: nothing must change for it to pass")
            pins = [p.get("path", "") for p in ps.get("pinned", [])]
            if os.path.exists(design) and not any(p.endswith(design_name) for p in pins):
                warnings.append(f"{design_name} is not in 'pinned': the executor could rewrite "
                                "the approach it is bound to")
            if "baseline" not in ps:
                warnings.append("proofs file has no baseline: run recheck_goal.py --baseline before the /goal")
            for c in (ps.get("baseline") or {}).get("counters", {}).values():
                if not re.search(rf"(>=|<=|≥|≤)\s*{c}\b", text):
                    warnings.append(f"baseline counter value {c} does not appear in the mandate constraints")
        except (OSError, ValueError) as e:
            errors.append(f"proofs file unreadable: {e}")
    if not any_in(t, [".CLAUDE/GOALS/"]) or not re.search(r"(FORBIDDEN|PROIBIDO)[^\n]*\.CLAUDE/GOALS", t):
        warnings.append("constraints do not forbid modifying .claude/goals/ files")

    tl = norm(text).lower()
    for v in VAGUE:
        if re.search(rf"\b{re.escape(norm(v).lower())}\b", tl):
            warnings.append(f"unverifiable term: '{v}' (tie it to a proof or remove it)")
    for v in UNBOUNDED:
        if re.search(rf"\b{re.escape(norm(v).lower())}\b", tl):
            warnings.append(f"unbounded quantity: '{v}' (give a number or name the source that enumerates it)")
    for v in UNDETECTABLE_STOP:
        if re.search(rf"\b{re.escape(norm(v).lower())}\b", tl):
            warnings.append(f"stop condition not mechanically detectable: '{v}' (name the concrete situation)")

    if done:
        n_crit = len(re.findall(r"^\s*\d+[.)]\s", done.group(2), re.M))
        if n_crit and n_crit < 3:
            warnings.append(f"{n_crit} criteria: fewer than 3 catches little (fine for small tasks)")
        elif n_crit > 8:
            warnings.append(f"{n_crit} criteria: above 8 the executor tends to drop one; consider splitting the goal")
    turns = [int(x) for x in re.findall(r"(\d+)\s*(?:TURNS|TURNOS)", t)]
    if turns and max(turns) > 40:
        warnings.append(f"turn limit {max(turns)} above 40: consider splitting into two goals")
    if not any_in(t, ["DISCARDED ATTEMPTS", "TENTATIVAS DESCARTADAS"]):
        warnings.append("checklist has no discarded-attempts section")

    odd = sorted({c for c in text if ord(c) > 0xFFFF or unicodedata.category(c) == "So"})
    if odd:
        warnings.append(f"symbols/emoji present: {''.join(odd)}")

    print(f"characters: {n_u16} (UTF-16) / {n_cp} (code points) | limit {MAX_CHARS}")
    print(f"criteria with proof: {n_proofs}")
    for e in errors:
        print(f"ERROR: {e}")
    for w in warnings:
        print(f"WARNING: {w}")
    print("RESULT: " + ("FAIL" if errors else "OK"))
    return 1 if errors else 0


def main() -> int:
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "--hash":
        print(hash_path(args[1]))
        return 0
    if len(args) != 1:
        print(__doc__)
        return 2
    return validate(args[0])


if __name__ == "__main__":
    sys.exit(main())
