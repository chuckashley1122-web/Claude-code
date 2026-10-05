# Environment inventory (names and status only - never a secret value)

Recorded 2026-10-05 from commands actually run in the build session. Anything not
produced by a command is marked `NEEDS_EVIDENCE` or `unavailable`.

| Item | Value | Source |
|---|---|---|
| Detected OS | `Linux-6.18.44-fc-v70-x86_64-with-glibc2.39` | `python3 -c "import platform; print(platform.platform())"` |
| Python version | `Python 3.11.15` | `python3 --version` |
| Interpreter name | `python3` (`/usr/bin/python3`) in this build session; Chuck's Windows machine uses `python`. No code hardcodes either name; tests use `sys.executable`. | `sys.executable` |
| Hermes version | unavailable - no Hermes installation or session was reachable by this agent | - |
| Active profile / session | unavailable - headless coding-agent session, no Hermes profile | - |
| Model / provider labels | unavailable for the pilot runtime; the pipeline itself calls no model | - |
| File tools | available: write/read probe passed (`evidence/preflight.md`) | `evidence/file_probe.txt` |
| Web tools | **none: no web tool and no browser** are available to the pipeline or this agent; live retrieval is blocked (`LiveRetriever` raises `LiveCallBlocked`) | `src/retrieval.py` |
| Resolved PROJECT_ROOT | `/home/user/Claude-code/build/caj-hvac-research-pilot` | `pwd` |
| Target PROJECT_ROOT on Chuck's machine | `C:\Users\chuck\Desktop\CA&J Enterprises\agency-agents\caj-growth-system\build\caj-hvac-research-pilot\` - NEEDS_EVIDENCE (not verified from this session) | SPEC-06 section 4 |
| Network egress by the pipeline | none (no network module is imported by `src/` or `scripts/`) | code review |

This pilot does not require new personalities, departments, or memory infrastructure;
existing identity, memory, and unrelated configuration are preserved untouched.
