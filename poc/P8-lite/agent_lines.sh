#!/usr/bin/env bash
# P8-lite: added lines per commit author (agent = commit message has "Co-Authored-By: Claude").
# Run from the repo root: bash poc/P8-lite/agent_lines.sh origin/main HEAD apps
base=$1; head=$2; shift 2; paths=${@:-apps}
for c in $(git rev-list --no-merges "$base..$head"); do
  who=human
  git log -1 --format=%B "$c" | grep -qi "Co-Authored-By: Claude" && who=agent
  git show --numstat --format= "$c" -- $paths | awk -v w=$who '{a+=$1} END {print w, a+0}'
done | awk '{s[$1]+=$2; t+=$2} END {for (k in s) printf "%s %d (%.0f%%)\n", k, s[k], t ? 100*s[k]/t : 0; print "total", t}'
