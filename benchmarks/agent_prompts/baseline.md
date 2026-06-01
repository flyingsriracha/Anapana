# Baseline prompt template

Use this template for the **Baseline** condition. No meditation file is given.

Replace `{PROBLEM}` with the verbatim text from `problems/B1.md`, `B2.md`, or
`B3.md`. For B2 and B3, also replace `{CODEBASE_PATH}` with the absolute path
to the test repo on the agent's filesystem.

---

You are participating in a code-fix benchmark. Solve the bug normally — no
special process imposed.

FIRST: record a start timestamp (Unix epoch seconds).
LAST: record an end timestamp. Report elapsed seconds.

THE PROBLEM:
{PROBLEM}

For B2 and B3 only: the codebase is at `{CODEBASE_PATH}`. Look at whatever
files you need. You may use web search if useful.

REPORT (write to a markdown file):

## START_TS
{unix timestamp}

## DIAGNOSIS
{what is actually wrong}

## FILES_READ
{list of file paths you opened — for code tasks}

## WEB_RESEARCH
{what you searched, if anything; key findings}

## PROPOSED_FIX
{exact diff or new file contents — be specific about WHICH file(s) you change}

## REASONING
{why this fix, why this location}

## SIDE_EFFECTS_CONSIDERED
{what else could break}

## SELF_RATINGS (1-5 each)
- Root cause / surface bug identified: X/5
- Considered all consumers of the changed code: X/5
- Preserved system invariants: X/5
- Confidence the fix is RIGHT (not just plausible): X/5

## END_TS
{unix timestamp}

## ELAPSED_SECONDS
{end - start}
