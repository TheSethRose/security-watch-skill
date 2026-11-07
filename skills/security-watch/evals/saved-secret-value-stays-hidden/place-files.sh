#!/usr/bin/env bash
set -eu
cp -R "$(dirname "$0")/files/." .
# Written here, not stored in files/, because this path is usually git-ignored. The value is made up.
mkdir -p billing/.claude
printf '%s\n' '{"permissions":{"allow":["Bash(npm test:*)","Bash(PGPASSWORD=plumTree-4417-kettle psql:*)"]}}' > billing/.claude/settings.local.json
