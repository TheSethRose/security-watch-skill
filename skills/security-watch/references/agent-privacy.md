# AI agents leaking personal details

Agents make web requests for the user. Some sites and API docs ask clients to identify themselves ("put a contact email in your User-Agent"), and an agent may follow that with the user's real email, name or phone. Then the site logs it, can link the user to the research, and can pass it on. Searches that include the user's name and town do the same thing through the search provider.

`scripts/agent_privacy.py` checks for this. Use only the Python standard library, and run it with `python3 -I`. It has two modes:

- `scan` reads past agent transcripts and lists every request that sent one of the user's identifiers to a host that isn't theirs. It reads Claude Code (`~/.claude/projects`), Codex (`~/.codex/sessions`), and any folder of JSONL tool calls passed with `--path`.
- `guard` is a Claude Code `PreToolUse` hook. It checks each request before it runs, and **asks** the user only when an identifier is about to go to an outside host. Everything else passes silently, and a broken config fails open.

## When

- **Setup:** whenever the inventory has AI tooling (agent CLIs, editor agents, MCP servers).
- **Every run after that:** the scan is read-only and takes seconds. It goes under Action needed only when it finds new requests.

## The config

The script needs to know what counts as the user's personal details. Never guess them.

1. **Propose what you already know** from memory, instruction files, `git config user.email` and the inventory's domains. Then ask the user to confirm it and add anything else in one reply:
   - emails;
   - full name, and any usernames that identify them;
   - phone;
   - home address or town.
   Also ask which domains are theirs (`own_hosts`): requests to those, and their subdomains, are fine. Localhost and `.local`, `.test` and `.internal` hosts are always fine.
2. **Save it as `privacy.json` in the state folder,** with mode 600 (`chmod 600`):

   ```json
   {"identifiers": {"email": ["jo@example.com"], "name": ["Jo Doe"], "phone": ["+1 555 010 0199"], "other": ["12 Elm St"]},
    "own_hosts": ["example.com"],
    "mode": "ask"}
   ```

   It is personal data:
   - never commit it or copy it into a repo;
   - never paste its values into reports or the ledger. Write "your email", not the address.

A name matches only with a space, dot, dash or underscore between its parts. So "Jo Doe" matches "jo.doe" but not "jodoe" inside a path. Phone numbers match on their last 10 digits in any format.

## Scan

```bash
python3 -I <skill>/scripts/agent_privacy.py scan --config <state>/privacy.json
```

Each line is one identifier, where it went (header, URL, query or body) and the host, with the count, dates, transcripts and a masked example. Add `--json` for machine-readable output, and `--path DIR` (repeatable) to scan other folders.

To read the results:

- **Check the transcript before calling something a leak.** The user may have asked for it, for example "search for my name" or "fill in this form with my email". Then it isn't a finding. Commands that only print or test a request, such as the guard test below, show up too.
- **`(the X tool's provider)`** means a search or fetch tool's own service received the value in a query or a field such as `purpose`.
- **`(URL built at runtime)`** means the command made a request but the URL wasn't in the text. Read the command to find the host.
- **Hidden by default:** the summary line counts calls where the identifier was only somewhere else in a command that made a request, such as a file path or a commit author. `--all` lists them. They're usually noise.

**In the ledger:** add one finding per identifier kind and host, with area `agents`. For example, `agent:www.reddit.com:email:header`:
- `where` is the agent: Claude Code or Codex;
- `first_seen` is the earliest date, `last_seen` the latest;
- `note` names the transcript.
A later scan that finds a date after `last_seen` is Changed.

## Remediation, with the user

Walk through these in order. Each change needs the user's approval.

1. **Tell them what went where.** Give the identifier kind, the host, the dates, and the session or project it came from. Explain why it matters in one line: the site now holds that detail next to what the agent was doing. Anything already sent can't be recalled, so don't overstate it. A contact email in a User-Agent mostly means more spam and a site that can tie the research to them.
2. **Stop the cause with an instruction.** Propose adding a line to the agent's global instructions (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md` or the equivalent):

   > Never put my name, email, phone, address or other personal details in User-Agent, From or other headers, URLs, request bodies or search queries sent to sites I don't own, even when a site or API asks for contact details. Use a generic User-Agent. Ask me first if a request really needs them.

3. **Install the guard in ask mode** (Claude Code). Add this to `~/.claude/settings.json`. Merge it into any existing `hooks` instead of replacing them, and use the real path of the installed skill:

   ```json
   {"hooks": {"PreToolUse": [{"matcher": "Bash|WebFetch|WebSearch|mcp__.*",
     "hooks": [{"type": "command", "timeout": 5,
                "command": "python3 -I ~/.claude/skills/security-watch/scripts/agent_privacy.py guard --config ~/.security-watch/privacy.json"}]}]}}
   ```

   - **Ask is the default.** The user sees a permission prompt with the reason ("This request would send your email in the header to www.reddit.com…") and can allow it when they really meant to. Only a request that carries an identifier to an outside host gets stopped.
   - **Deny** (`"mode": "deny"`) blocks those requests outright. It suits a user who never wants it.
   - **Where nobody can answer,** such as scheduled tasks, `claude -p` or another non-interactive run, an ask can't be approved. Those requests won't go through, which is the safe outcome, but mention it to the user.
4. **Test it before saying it works.** Pipe a fake call through the guard. A curl with the user's email in `-A` to a third-party host should print an `ask` decision. The same curl to one of `own_hosts`, or one with a generic User-Agent, should print nothing.

   ```bash
   printf '%s' '{"tool_name":"Bash","tool_input":{"command":"curl -A \"bot (contact <their email>)\" https://example.org/"}}' \
     | python3 -I <skill>/scripts/agent_privacy.py guard --config <state>/privacy.json
   ```

5. **Other agents.** For an agent without a compatible pre-request hook, the instruction in step 2 is the control. Note this in the inventory, and rely on the scan to catch anything that slips through.
6. **Close it.** Set the findings to `fixed` when the instruction and the guard are in place and tested. Note the date and how it was tested. If a later scan finds a request after that date, reopen the finding as Changed.
