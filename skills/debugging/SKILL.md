---
name: debugging
description: Finding and fixing bugs, failing tests and runtime errors
triggers: [bug, error, traceback, exception, fix, failing, crash, broken, "not working", pytest, stacktrace, debug]
---
- Reproduce the problem first. Run the failing test or command and read the full error.
- Locate the failing line with `search_code` and `read_file`, then trace inputs back to their source.
- Form one hypothesis at a time and verify it before editing.
- Fix the root cause with the smallest change, not the symptom.
- Re-run the failing case and the surrounding tests to confirm the fix and catch regressions.
- Add a test that fails without the fix when the project has a test suite.
