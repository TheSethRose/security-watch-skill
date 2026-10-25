#!/usr/bin/env python3
"""Offline self-test for agent_privacy.py. Made-up identifiers only. Run: python3 -I test_agent_privacy.py"""
import io, json, os, subprocess, sys, tempfile, unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import agent_privacy as ap  # noqa: E402

CONFIG = {
    "identifiers": {"email": ["jo.tester@example.org"], "name": ["Jo Tester"], "phone": ["+1 555 010 0199"]},
    "own_hosts": ["mysite.example"],
    "mode": "ask",
}


class Detector(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.cfg = os.path.join(self.dir.name, "privacy.json")
        with open(self.cfg, "w") as fh:
            json.dump(CONFIG, fh)
        self.ids, self.own, self.mode = ap.load_config(self.cfg)

    def tearDown(self):
        self.dir.cleanup()

    def hits(self, tool, payload):
        r = ap.analyze(tool, payload, self.ids, self.own)
        return r["leaks"] if r else []

    def test_email_in_user_agent_header(self):
        cmd = 'curl -A "bot (jo.tester@example.org)" https://api.third.example/data'
        self.assertIn(("email: jo.tester@example.org", "header", "api.third.example"), self.hits("Bash", {"command": cmd}))

    def test_name_in_search_query(self):
        leaks = self.hits("mcp__web__search", {"query": "Jo Tester plumber near me"})
        self.assertEqual([l[:2] for l in leaks], [("name: Jo Tester", "query")])

    def test_phone_in_url(self):
        leaks = self.hits("Bash", {"command": "curl https://lookup.third.example/?q=5550100199"})
        self.assertEqual(leaks[0][1], "url")

    def test_variable_expanded(self):
        cmd = 'UA="x jo.tester@example.org"; curl -A "$UA" https://api.third.example/'
        self.assertTrue(any(l[1] == "header" for l in self.hits("Bash", {"command": cmd})))

    def test_own_host_not_flagged(self):
        cmd = 'curl -A "jo.tester@example.org" https://app.mysite.example/ping'
        self.assertEqual(self.hits("Bash", {"command": cmd}), [])

    def test_localhost_not_flagged(self):
        self.assertEqual(self.hits("Bash", {"command": 'curl -H "From: jo.tester@example.org" http://localhost:3000/'}), [])

    def test_no_identifier_not_flagged(self):
        self.assertEqual(self.hits("Bash", {"command": 'curl -A "plain-agent" https://api.third.example/'}), [])

    def test_local_tool_not_flagged(self):
        self.assertEqual(self.hits("Grep", {"pattern": "Jo Tester"}), [])

    def test_identifier_in_path_without_request_not_flagged(self):
        self.assertEqual(self.hits("Bash", {"command": "ls /home/jo.tester@example.org"}), [])

    def test_secret_masked_in_snippet(self):
        cmd = 'curl -H "Authorization: Bearer abc123secret" -A "jo.tester@example.org" https://api.third.example/'
        self.assertNotIn("abc123secret", ap.analyze("Bash", {"command": cmd}, self.ids, self.own)["snippet"])


class Cli(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.cfg = os.path.join(self.dir.name, "privacy.json")
        with open(self.cfg, "w") as fh:
            json.dump(CONFIG, fh)

    def tearDown(self):
        self.dir.cleanup()

    def run_cli(self, *args, stdin=""):
        return subprocess.run([sys.executable, "-I", os.path.join(HERE, "agent_privacy.py"), *args],
                              input=stdin, capture_output=True, text=True, timeout=30)

    def test_help(self):
        r = self.run_cli("--help")
        self.assertEqual(r.returncode, 0)
        self.assertIn("scan", r.stdout)

    def test_guard_asks_on_leak(self):
        event = {"tool_name": "Bash", "tool_input": {"command": 'curl -A "jo.tester@example.org" https://api.third.example/'}}
        out = json.loads(self.run_cli("guard", "--config", self.cfg, stdin=json.dumps(event)).stdout)
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "ask")

    def test_guard_denies_in_deny_mode(self):
        with open(self.cfg, "w") as fh:
            json.dump(dict(CONFIG, mode="deny"), fh)
        event = {"tool_name": "WebSearch", "tool_input": {"query": "Jo Tester"}}
        out = json.loads(self.run_cli("guard", "--config", self.cfg, stdin=json.dumps(event)).stdout)
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_guard_silent_when_clean(self):
        event = {"tool_name": "Bash", "tool_input": {"command": "curl https://api.third.example/"}}
        self.assertEqual(self.run_cli("guard", "--config", self.cfg, stdin=json.dumps(event)).stdout, "")

    def test_guard_fails_open_on_bad_input(self):
        self.assertEqual(self.run_cli("guard", "--config", self.cfg, stdin="not json").stdout, "")

    def test_scan_finds_leak_in_transcript(self):
        line = {"timestamp": "2026-10-01T10:00:00Z", "message": {"content": [
            {"type": "tool_use", "name": "Bash",
             "input": {"command": 'curl -A "jo.tester@example.org" https://api.third.example/'}}]}}
        with open(os.path.join(self.dir.name, "t.jsonl"), "w") as fh:
            fh.write(json.dumps(line) + "\n")
        r = self.run_cli("scan", "--config", self.cfg, "--path", self.dir.name, "--json")
        rows = json.loads(r.stdout)
        self.assertEqual([(x["where"], x["host"]) for x in rows], [("header", "api.third.example")])

    def test_scan_clean_transcript(self):
        line = {"message": {"content": [{"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}]}}
        with open(os.path.join(self.dir.name, "t.jsonl"), "w") as fh:
            fh.write(json.dumps(line) + "\n")
        r = self.run_cli("scan", "--config", self.cfg, "--path", self.dir.name)
        self.assertIn("No identifier was sent", r.stdout)


if __name__ == "__main__":
    unittest.main()
