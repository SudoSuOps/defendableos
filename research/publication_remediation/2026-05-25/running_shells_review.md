# Running Shells Review · 2026-05-25

Mission E asked to inspect running Claude / background shell tasks and stop any that are still
publishing unaudited claims or writing unintended changes — without killing blindly.

## Method

- `pgrep -af claude` to enumerate Claude processes
- `readlink /proc/<pid>/cwd` to resolve working directories
- `pgrep -af 'git '` and `/proc/*/cwd` scan for processes operating inside the repos

## Findings

| PID | process | cwd | assessment |
| --- | --- | --- | --- |
| 21930 | `claude` | `/home/swarm/Desktop` | **This authorized remediation session.** The only Claude process. |
| 22084 | `node … /mcp` | `/home/swarm/Desktop` | MCP helper child of PID 21930. Normal. |
| (transient) | `/bin/bash -c …` subshells | federal folder | The remediation session's **own** Bash tool invocations. The grep for "git " matched the command line itself, not a separate git process. Transient; exit with each tool call. |

Everything else on the box was Brave browser processes and system daemons (`networkd-dispatcher`,
`unattended-upgrade`) — unrelated.

## Conclusion

- There is **no second Claude shell** and **no background `git push` or repo-writer** running.
- The "two running shells" the mission anticipated do **not** exist as independent publishing
  processes. The only writer to either repository during this pass was this authorized session.
- **Nothing was killed** — there was no rogue task to stop. No process was publishing unaudited
  claims at the time of inspection.
