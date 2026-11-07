#!/usr/bin/env python3
"""Offline self-test for agent_secrets.py. All values are made up. Run with `python3 -I`."""
import json, os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import agent_secrets as sec  # noqa: E402

SCRIPT = os.path.join(HERE, "agent_secrets.py")
VALUE = "plumTree-4417-kettle"


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)


def rule(command):
    return json.dumps({"permissions": {"allow": [f"Bash({command})"]}})


class Detector(unittest.TestCase):
    def test_passwords_inside_commands(self):
        self.assertEqual(sec.find_kinds(f"PGPASSWORD={VALUE} psql:*"), {"password in a variable": 1})
        self.assertEqual(sec.find_kinds(f"sshpass -p {VALUE} ssh host"), {"password argument": 1})
        self.assertEqual(sec.find_kinds(f"mysql -u app -p{VALUE} db"), {"password argument": 1})

    def test_connection_string(self):
        self.assertEqual(sec.find_kinds(f"postgres://app:{VALUE}@db.example.test/main"),
                         {"connection string": 1})

    def test_placeholders_are_kept_and_labelled(self):
        self.assertEqual(sec.find_kinds("PGPASSWORD=$DB_PASS psql"),
                         {"password in a variable (likely placeholder)": 1})
        self.assertEqual(sec.find_kinds("API_KEY=your_key_here"),
                         {"token in a variable (likely placeholder)": 1})

    def test_ordinary_rules_are_clean(self):
        self.assertEqual(sec.find_kinds("npm run test:* git status psql:*"), {})


class Cli(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.root = self.dir.name

    def run_cli(self, *args):
        r = subprocess.run([sys.executable, "-I", SCRIPT, "scan", "--path", self.root, *args],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def git(self, repo, *args):
        subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@example.test",
                        "-c", "commit.gpgsign=false", *args], check=True, capture_output=True)

    def test_output_never_holds_the_value(self):
        write(os.path.join(self.root, "app/.claude/settings.local.json"), rule(f"PGPASSWORD={VALUE} psql:*"))
        for out in (self.run_cli(), self.run_cli("--json")):
            out = out.replace(self.root, "")
            self.assertNotIn(VALUE, out)
            self.assertNotIn(VALUE[:4], out)
            self.assertNotIn(str(len(VALUE)), out)
        self.assertIn("password in a variable x1", self.run_cli())

    def test_skips_files_outside_agent_folders(self):
        write(os.path.join(self.root, "app/config/settings.json"), rule(f"PGPASSWORD={VALUE} psql:*"))
        self.assertIn("Nothing found", self.run_cli())

    def test_finds_a_deleted_file_in_history(self):
        repo = os.path.join(self.root, "app")
        path = os.path.join(repo, ".claude/settings.json")
        write(path, rule(f"PGPASSWORD={VALUE} psql:*"))
        subprocess.run(["git", "init", "-q", repo], check=True)
        self.git(repo, "add", "-f", ".claude/settings.json")
        self.git(repo, "commit", "-qm", "add")
        self.git(repo, "rm", "-q", "--cached", ".claude/settings.json")
        self.git(repo, "commit", "-qm", "remove")
        os.remove(path)
        out = self.run_cli()
        self.assertIn("history of", out)
        self.assertIn("password in a variable", out)
        self.assertNotIn(VALUE, out)


if __name__ == "__main__":
    unittest.main()
