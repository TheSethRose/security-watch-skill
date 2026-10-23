#!/usr/bin/env python3
"""Find and guard against AI agents sending the user's personal details to other sites.

Two modes share one detector:

  scan   Read agent transcripts (Claude Code, Codex, or any JSONL with tool calls) and list
         every outbound request that carried one of the user's identifiers to a host that
         isn't theirs: in a header, the URL, the body, or a search query.
  guard  Claude Code PreToolUse hook. Reads one tool call on stdin. If it would send an
         identifier to a host that isn't the user's, it answers "ask" (or "deny" when the
         config says so). Everything else passes silently.

Config is a JSON file the user fills in (see references/agent-privacy.md):

  {"identifiers": {"email": ["me@example.com"], "name": ["Jo Doe"], "phone": ["+1 555 010 0199"],
                   "other": ["12 Elm St"]},
   "own_hosts": ["example.com"], "mode": "ask"}

Only the Python standard library is used. Run with `python3 -I`.
"""
import argparse, glob, json, os, re, sys
from urllib.parse import unquote_plus, urlsplit

CLIENT = re.compile(
    r"\b(curl|wget|xh|httpie|http|https)\s|\bgh\s+api\b|requests\.(get|post|put|patch|delete|request|Session)"
    r"|httpx\.|urllib\.request|urlopen\(|\bfetch\(|axios|Invoke-(WebRequest|RestMethod)|aiohttp|got\(|ky\(",
    re.I)
FETCH_TOOL = re.compile(r"(^|_)(webfetch|websearch|fetch|search|navigate|browse|http|scrape|crawl)", re.I)
# Tools that search or read only local data, even though their names match FETCH_TOOL.
LOCAL_TOOL = re.compile(r"ToolSearch|session|transcript|memory|grep|glob|notebook|file", re.I)
URL = re.compile(r"https?://[^\s\"'<>)\]}\\]+", re.I)
# Flags are read only inside a curl/wget/httpie command, so grep -A or sed -e don't count.
CLI_SEGMENT = re.compile(r"\b(curl|wget|xh|http|https)\s")
CLI_HEADER = re.compile(r"""(?<!\S)(?:-H|--header|-A|--user-agent|-e|--referer|-b|--cookie|--header=)\s*("[^"]*"|'[^']*'|\S+)""")
CLI_BODY = re.compile(r"""(?<!\S)(?:-d|--data(?:-raw|-binary|-urlencode)?|--json|-F|--form)\s*(?:=\s*)?("[^"]*"|'[^']*'|\S+)""")
# Headers and bodies set in code (Python, JavaScript), anywhere in the call.
CODE_HEADER = re.compile(r"""["'](?:user-agent|from|referer|cookie|x-[\w-]+)["']\s*:\s*("[^"]*"|'[^']*'|[^,}\n]+)""", re.I)
CODE_BODY = re.compile(r"""\b(?:data|json|body|params)\s*[=:]\s*("[^"]*"|'[^']*'|\{[^}]*\})""", re.I)
ASSIGN = re.compile(r"""\b([A-Za-z_][A-Za-z0-9_]*)=("[^"]*"|'[^']*')""")
LOCAL = re.compile(r"^(localhost|127\.\d+\.\d+\.\d+|0\.0\.0\.0|\[?::1\]?|.*\.(localhost|local|test|internal))$", re.I)
SECRET = re.compile(r"(bearer\s+|token[=:]\s*|api[_-]?key[=:]\s*|authorization:\s*\S+\s+|password[=:]\s*)(\S+)", re.I)
ORDER = {"header": 0, "url": 1, "query": 2, "body": 3, "same command": 4}


def load_config(path):
    with open(os.path.expanduser(path)) as fh:
        cfg = json.load(fh)
    ids = []
    for kind, values in (cfg.get("identifiers") or {}).items():
        for v in values or []:
            v = str(v).strip()
            if not v:
                continue
            if kind == "phone":
                digits = re.sub(r"\D", "", v)[-10:]
                if len(digits) >= 7:
                    pat = r"(?<!\d)" + r"[\s().+-]*".join(digits) + r"(?!\d)"
                    ids.append((kind, v, re.compile(pat)))
            else:
                words = [re.escape(w) for w in v.split()]
                pat = r"(?<![\w.])" + r"[\s+_.-]+".join(words) + r"(?![\w])"
                ids.append((kind, v, re.compile(pat, re.I)))
    own = [h.lower().lstrip(".") for h in cfg.get("own_hosts") or []]
    return ids, own, cfg.get("mode", "ask")


def url_host(u):
    try:
        return (urlsplit(u).hostname or "").lower()
    except ValueError:
        return ""


def host_kind(host, own):
    h = host.lower().split(":")[0].strip("[]")
    if LOCAL.match(h):
        return "local"
    if any(h == o or h.endswith("." + o) for o in own):
        return "own"
    return "third-party"


def find_ids(text, ids):
    """Return {identifier label} found in text, checking the raw and URL-decoded forms."""
    found = set()
    for candidate in (text, unquote_plus(text)):
        for kind, value, pat in ids:
            if kind == "email" and pat.search(candidate):
                found.add(f"{kind}: {value}")
                candidate = pat.sub("<email>", candidate)  # so "Jo Doe" doesn't match inside jo.doe@...
        for kind, value, pat in ids:
            if kind != "email" and pat.search(candidate):
                found.add(f"{kind}: {value}")
    return found


def split_commands(text):
    """Split a shell command on ;, |, &&, || and newlines that sit outside quotes."""
    parts, buf, quote, i = [], [], None, 0
    while i < len(text):
        c = text[i]
        if quote:
            if c == quote:
                quote = None
            elif c == "\\" and quote == '"':
                buf.append(c); i += 1; c = text[i] if i < len(text) else ""
        elif c in "\"'":
            quote = c
        elif c in ";|\n" or text.startswith("&&", i):
            parts.append("".join(buf)); buf = []
            i += 2 if text.startswith(("&&", "||"), i) else 1
            continue
        buf.append(c); i += 1
    parts.append("".join(buf))
    return parts


def hosts_in(text):
    return sorted({url_host(u) for u in URL.findall(text)} - {""})


def shell_leaks(text, ids):
    """Yield (identifier, where, host) for a shell or code call that makes a request."""
    values = dict(ASSIGN.findall(text))
    def expand(chunk):
        # Resolve $VAR / ${VAR} set earlier in the same call, e.g. UA="... me@x.com"; curl -A "$UA".
        return re.sub(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?", lambda m: values.get(m.group(1), m.group(0)), chunk)
    all_hosts = hosts_in(expand(text)) or ["(URL built at runtime)"]
    for seg in split_commands(text):
        if not CLI_SEGMENT.search(seg):
            continue
        seg_hosts = hosts_in(expand(seg)) or all_hosts  # e.g. for u in "https://..."; do curl "$u"
        for pattern, place in ((CLI_HEADER, "header"), (CLI_BODY, "body")):
            for m in pattern.finditer(seg):
                for label in find_ids(expand(m.group(1)), ids):
                    for h in seg_hosts:
                        yield label, place, h
    for pattern, place in ((CODE_HEADER, "header"), (CODE_BODY, "body")):
        for m in pattern.finditer(text):
            for label in find_ids(expand(m.group(1)), ids):
                for h in all_hosts:
                    yield label, place, h
    for u in URL.findall(expand(text)):
        for label in find_ids(u, ids):
            yield label, "url", url_host(u) or "(unparsable URL)"
    for label in find_ids(text, ids):
        for h in all_hosts:
            yield label, "same command", h


def tool_leaks(tool, payload, ids):
    """Yield (identifier, where, host) for a fetch, search or browse tool call."""
    fields = payload if isinstance(payload, dict) else {"input": payload}
    provider = f"(the {tool} tool's provider)"
    for key, value in fields.items():
        raw = json.dumps(value, ensure_ascii=False)
        labels = find_ids(raw, ids)
        if not labels:
            continue
        if "url" in key.lower():
            for u in URL.findall(raw):
                for label in find_ids(u, ids):
                    yield label, "url", url_host(u)
        else:
            place = "query" if key.lower() in ("query", "q", "queries", "prompt", "search", "goal") else "body"
            for label in labels:
                yield label, place, provider


def analyze(tool, payload, ids, own):
    """Return {"leaks": [(identifier, where, host)], "snippet": ...} or None when nothing personal leaves."""
    text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    if isinstance(payload, dict) and isinstance(payload.get("command"), str):
        text = payload["command"]
    shell_like = bool(CLIENT.search(text))
    fetch_tool = bool(FETCH_TOOL.search(tool or "")) and not LOCAL_TOOL.search(tool or "") and not shell_like
    if not (shell_like or fetch_tool) or not find_ids(text, ids):
        return None
    leaks = shell_leaks(text, ids) if shell_like else tool_leaks(tool, payload, ids)
    best = {}
    for label, place, host in leaks:
        if host.startswith("(") or host_kind(host, own) == "third-party":
            key = (label, host)
            if key not in best or ORDER[place] < ORDER[best[key]]:
                best[key] = place
    if not best:
        return None
    return {"tool": tool, "leaks": sorted((label, place, host) for (label, host), place in best.items()),
            "snippet": SECRET.sub(lambda m: m.group(1) + "***", text)[:300]}


def tool_calls(line):
    """Yield (tool name, input) for every tool call recorded on one transcript line."""
    try:
        obj = json.loads(line)
    except ValueError:
        return
    stack = [obj]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            t = o.get("type")
            if t == "tool_use" and "input" in o:
                yield o.get("name", ""), o["input"]
                continue
            if t in ("function_call", "custom_tool_call", "local_shell_call"):
                raw = o.get("arguments", o.get("input", o.get("action")))
                if isinstance(raw, str):
                    try:
                        raw = json.loads(raw)
                    except ValueError:
                        pass
                if isinstance(raw, dict) and isinstance(raw.get("command"), list):
                    raw = {"command": " ".join(map(str, raw["command"]))}
                yield o.get("name", t), raw
                continue
            stack.extend(o.values())
        elif isinstance(o, list):
            stack.extend(o)


def scan(args):
    ids, own, _ = load_config(args.config)
    if not ids:
        sys.exit("No identifiers in the config. Ask the user for the email, name and phone to look for.")
    roots = args.path or [p for p in ("~/.claude/projects", "~/.codex/sessions") if os.path.isdir(os.path.expanduser(p))]
    files = [f for r in roots for f in glob.glob(os.path.join(os.path.expanduser(r), "**", "*.jsonl"), recursive=True)]
    groups, hidden = {}, 0
    for f in files:
        ts = "?"  # a line without a timestamp takes the last one seen in the file
        with open(f, errors="replace") as fh:
            for line in fh:
                m = re.search(r'"timestamp"\s*:\s*"(\d{4}-\d\d-\d\d)', line)
                ts = m.group(1) if m else ts
                if '"input"' not in line and '"arguments"' not in line:
                    continue
                for tool, payload in tool_calls(line):
                    r = analyze(tool, payload, ids, own)
                    if not r:
                        continue
                    for label, place, host in r["leaks"]:
                        if place == "same command" and not args.all:
                            hidden += 1
                            continue
                        g = groups.setdefault((label, place, host), {"count": 0, "dates": set(), "files": set(), "example": r["snippet"]})
                        g["count"] += 1
                        g["dates"].add(ts)
                        g["files"].add(os.path.relpath(f, os.path.expanduser("~")))
    rows = sorted(groups.items(), key=lambda kv: (ORDER[kv[0][1]], kv[0][2]))
    if args.json:
        print(json.dumps([{"identifier": k[0], "where": k[1], "host": k[2], "count": v["count"],
                           "dates": sorted(v["dates"]), "transcripts": sorted(v["files"]), "example": v["example"]}
                          for k, v in rows], indent=1))
        return
    print(f"Scanned {len(files)} transcripts in {', '.join(roots) or 'nothing'}.")
    if hidden:
        print(f"({hidden} call(s) had an identifier elsewhere in a command that made a request, e.g. a file path "
              "or commit author; rerun with --all to list them.)")
    if not rows:
        print("No identifier was sent in a header, URL, body or search query to a host outside own_hosts.")
        return
    print(f"{len(rows)} leak groups (identifier, where, host):")
    for (label, place, host), v in rows:
        d = sorted(v["dates"])
        print(f"- {label} in the {place} to {host}: {v['count']} call(s), {d[0]} to {d[-1]}, {len(v['files'])} transcript(s)")
        print(f"    e.g. {re.sub(chr(10), ' ', v['example'])[:200]}")


def guard(args):
    try:
        ids, own, mode = load_config(args.config)
        event = json.load(sys.stdin)
        r = analyze(event.get("tool_name", ""), event.get("tool_input") or {}, ids, own)
    except Exception:
        return  # Fail open: a broken guard must not block every tool call.
    leaks = [l for l in (r or {}).get("leaks", []) if l[1] != "same command"]
    if not leaks:
        return
    found = ", ".join(sorted({f"{label.split(':')[0]} in the {place}" for label, place, _ in leaks}))
    hosts = ", ".join(sorted({host for _, _, host in leaks}))
    fix = ("use a generic User-Agent and no contact email" if any(p == "header" for _, p, _ in leaks)
           else "leave the personal details out")
    reason = (f"This request would send your {found} to {hosts}, which isn't in own_hosts. "
              + (f"Rerun it without them: {fix}." if mode == "deny" else
                 f"Allow it only if you asked for that; otherwise deny it and {fix}."))
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "permissionDecision": "deny" if mode == "deny" else "ask",
                                             "permissionDecisionReason": reason}}))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode", choices=["scan", "guard"])
    p.add_argument("--config", default="~/.security-watch/privacy.json")
    p.add_argument("--path", action="append", help="transcript folder to scan (repeatable)")
    p.add_argument("--json", action="store_true", help="scan: print JSON instead of text")
    p.add_argument("--all", action="store_true", help="scan: also list identifiers found only elsewhere in the command")
    a = p.parse_args()
    scan(a) if a.mode == "scan" else guard(a)


if __name__ == "__main__":
    main()
