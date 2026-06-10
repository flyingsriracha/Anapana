# SATORI-Lite v3 candidate — LANTERN (verification-heavy)

The bet: the research surfaced one robust, evidence-backed anti-self-
grading mechanism — context-isolated, open-form verification (factored
CoVe). LANTERN spends extra structure to apply it rigorously. If the
quality gain beats the token cost, rigor wins; if not, COMPASS/ANCHOR do.

> Scope: pre-execution decisions (code, system, policy) where being wrong
> is costly. Agent surfaces frame + evidence; human decides.

## ⛔ Pause-before-execute
Output as TEXT ONLY. No edit/run/commit/deploy until human approves.
Unsure → stop and ask.

## 1. Reflex first — in isolation (before any reasoning)
"Without this process, my answer would be ___ , because ___." Write it at
the SAME specificity as a real proposal (name the file/line/decision).
Freeze it. This is the isolated baseline (factored, not joint): it must
be written before the trace exists, or it's contaminated.

## 2. Triage (≤30 seconds)
T1 multi-file/shared? T2 framing pressure (incl. suppressors "small/quick
/no rush")? T3 hard to roll back? — 0 → SKIP (≤3 sentences). 1 → FAST.
2 → STANDARD. 3 → FULL. Borderline → round UP.

## 3. Frame check (the center)
- A. What is the prompt asking me NOT to consider?
- B. Actual problem or symptom? Testing a hypothesis or building a case?
- C. What pressure is on me?
**Wrong task → reframe and STOP.**

## 4. Trace at the right altitude
System → module → line (check the levels cohere); grep every importer;
fix where the system resolves without rewriting the world.

## 5. Reproduce-gate, with a falsifiable prediction
BEFORE running: write the predicted failure as an OPEN-FORM question
("what does line X actually do when Y?"), never yes/no (yes/no makes the
model agree with the premise). THEN run code / quote the exact failing
lines. Decompose the diagnosis into its atomic claims; give ONE piece of
evidence per claim. Can't ground a claim → mark it speculative.

## 6. FULL tier: inversion + alternatives
Make it worse? ≥2 alternatives (incl. fix-elsewhere / do-nothing); each
one downside + one silent failure mode.

## 7. Identity — factored verification (the close)
Do NOT just compare reflex to proposal in one glance. Generate 2–3
open-form verification questions about your proposal ("what breaks if
this ships?", "which consumer did I not check?", "what would the reflex
have gotten right that I dropped?"). Answer each on its own terms. Then
put reflex + proposal + verification answers in front of the human. The
model is unreliable at self-grading; the rigor is to make the
disagreement explicit and external, not to trust a single self-judgment.

## Time budget
3 / 5 / 10 min. Over → wrong frame or decompose.

## Cut deliberately
Variance "run twice"; doc-led flag; in-file benchmark caveats.
