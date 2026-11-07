#!/usr/bin/env python3
"""Find secrets saved in AI agents' project settings, without showing them.

Agents can save an approved command word for word, password included, in a settings
file inside the project. This script finds those files, says what kind of secret each
holds and whether git has ever seen it. It prints paths, kinds and counts. It never
prints a value, part of a value, or a value's length, so the output is safe to keep.

  python3 -I agent_secrets.py scan --path ~/code [--path ...] [--json]

Read-only. Only the Python standard library is used.
"""
import argparse, json, os, re, subprocess, sys

AGENT_DIRS = {".claude", ".codex", ".cursor", ".gemini", ".windsurf"}
SUFFIXES = (".json", ".toml", ".yaml", ".yml")
SKIP_DIRS = {"node_modules", ".git", ".venv", "venv", ".next", "dist", "build", "Library", ".Trash",
             "__pycache__", ".cache", "target", "vendor"}
MAX_BYTES = 5_000_000

# Each pattern's "v" group is the value. Only its shape is ever used, to spot placeholders.
PATTERNS = [
    ("api key", r"(?P<v>\b(?:sk-[A-Za-z0-9_-]{20,}|sk_live_\w{16,}|AIza[\w-]{30,}|AKIA[0-9A-Z]{16}))"),
    ("code host token", r"(?P<v>\b(?:ghp_\w{20,}|gho_\w{20,}|github_pat_\w{20,}|glpat-[\w-]{16,}|npm_\w{20,}))"),
    ("chat or network token", r"(?P<v>\b(?:xox[bap]-[\w-]{16,}|tskey-[\w-]{16,}))"),
    ("connection string", r"\b[a-z][a-z0-9+.-]*://[^:@/\s\"']+:(?P<v>[^@/\s\"']+)@"),
    ("password in a variable",
     r"\b[A-Z0-9_]*(?:PASSWORD|PASSWD|PASS|PWD)=(?P<v>\"[^\"]*\"|'[^']*'|[^\s\"')]+)"),
    ("token in a variable",
     r"\b[A-Z0-9_]*(?:TOKEN|SECRET|API_?KEY|AUTH)=(?P<v>\"[^\"]*\"|'[^']*'|[^\s\"')]+)"),
    ("password argument", r"(?:\bsshpass\s+-p\s*|--password[= ]\s*|\bmysql\b[^\"\n]*?\s-p)(?P<v>[^\s\"')]+)"),
    ("bearer token", r"\bBearer\s+(?P<v>[\w.~+/=-]{16,})"),
]
PATTERNS = [(kind, re.compile(rx)) for kind, rx in PATTERNS]
PLACEHOLDER = re.compile(
    r"^[\"']?(?:\$|<|\{|%|\*)|example|changeme|change_me|your[_-]|placeholder|redacted|test|dummy|fake|xxx",
    re.I)


def find_kinds(text):
    """Return {kind: count}. Likely placeholders are counted apart, never dropped."""
    kinds = {}
    for kind, rx in PATTERNS:
        for m in rx.finditer(text):
            name = f"{kind} (likely placeholder)" if PLACEHOLDER.search(m.group("v")) else kind
            kinds[name] = kinds.get(name, 0) + 1
    return kinds


def git(repo, *args):
    # core.fsmonitor can run a program named in the repo's config, so it is switched off.
    r = subprocess.run(["git", "-c", "core.fsmonitor=false", "-C", repo, *args],
                       capture_output=True, text=True, errors="replace")
    return r.returncode, r.stdout


def repo_of(path):
    code, out = git(os.path.dirname(path), "rev-parse", "--show-toplevel")
    return out.strip() if code == 0 else None


def is_settings(path):
    parts = path.split(os.sep)
    return len(parts) > 1 and parts[-2] in AGENT_DIRS and path.endswith(SUFFIXES)


def walk(root):
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        if os.path.basename(base) in AGENT_DIRS:
            dirs[:] = []
        for f in files:
            path = os.path.join(base, f)
            if is_settings(path):
                yield path


def walk_repos(root):
    for base, dirs, _ in os.walk(root):
        if ".git" in dirs:
            yield base
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]


def git_state(repo, path):
    rel = os.path.relpath(path, repo)
    tracked = git(repo, "ls-files", "--error-unmatch", "--", rel)[0] == 0
    ignored = git(repo, "check-ignore", "-q", "--", rel)[0] == 0
    return {"tracked": tracked, "ignored": ignored}


def history(repo):
    """Agent settings files git has ever held, with the kinds of secret in added lines."""
    specs = [f":(glob)**/{d}/*{s}" for d in sorted(AGENT_DIRS) for s in SUFFIXES]
    code, out = git(repo, "log", "--all", "--format=", "--name-only", "--", *specs)
    names = sorted(set(out.split("\n")) - {""}) if code == 0 else []
    rows = []
    for name in names:
        code, patch = git(repo, "log", "--all", "-p", "--format=", "--", name)
        added = "\n".join(l[1:] for l in patch.splitlines() if l.startswith("+") and not l.startswith("+++"))
        kinds = find_kinds(added) if code == 0 else {}
        if kinds:
            rows.append({"repo": repo, "file": name, "kinds": kinds})
    return rows


def scan(args):
    roots = [os.path.abspath(os.path.expanduser(p)) for p in args.path]
    files, past, seen_files, seen_repos = [], [], set(), set()
    checked = 0
    for root in roots:
        for path in walk(root):
            if path in seen_files:
                continue
            seen_files.add(path)
            try:
                if os.path.getsize(path) > MAX_BYTES:
                    continue
                with open(path, errors="replace") as fh:
                    text = fh.read()
            except OSError:
                continue
            checked += 1
            kinds = find_kinds(text)
            if kinds:
                repo = repo_of(path)
                state = git_state(repo, path) if repo else {"tracked": False, "ignored": False}
                files.append({"file": path, "kinds": kinds, "repo": repo, **state})
        for repo in walk_repos(root):
            if repo not in seen_repos:
                seen_repos.add(repo)
                past.extend(history(repo))
    if args.json:
        print(json.dumps({"files_checked": checked, "repos_checked": len(seen_repos),
                          "files": files, "history": past}, indent=1))
        return
    print(f"Checked {checked} agent settings file(s) and the history of {len(seen_repos)} repo(s).")
    if not files and not past:
        print("Nothing found in what this could check. Passwords in unusual forms can be missed.")
    for row in files:
        where = "TRACKED by git" if row["tracked"] else "ignored by git" if row["ignored"] else (
            "not ignored by git" if row["repo"] else "not in a repo")
        print(f"- {row['file']}: {describe(row['kinds'])}; {where}")
    for row in past:
        print(f"- history of {row['repo']}: {row['file']}: {describe(row['kinds'])}")


def describe(kinds):
    return ", ".join(f"{kind} x{n}" for kind, n in sorted(kinds.items()))


def main():
    p = argparse.ArgumentParser(description="Find secrets saved in AI agents' settings files.")
    p.add_argument("mode", choices=["scan"])
    p.add_argument("--path", action="append", required=True, help="folder to search (repeatable)")
    p.add_argument("--json", action="store_true", help="print JSON instead of text")
    scan(p.parse_args())


if __name__ == "__main__":
    sys.exit(main())
