#!/usr/bin/env python
"""Agent evaluation harness.

Every bug found in this agent so far - three under-counting faults and one
false negative - was caught by hand-comparing an answer against the
database. The unit tests cover the decision logic; nothing checked whether
a given question produces a *true* answer. This does.

For each case it runs a ground-truth Cypher query directly, runs the same
question through the agent, and checks that the true figure appears in the
answer. Ground truth is computed live rather than hardcoded, so reloading
the graph does not invalidate the suite.

Some cases additionally assert which relationship the agent's own Cypher
must touch. That catches the class of failure where the agent substitutes
a plausible proxy - it once answered a modus-operandi question by
comparing weapon types, which reads as correct and is not.

    python eval_agent.py            # full run
    python eval_agent.py --quick    # first four cases

Exits non-zero if the pass rate falls below THRESHOLD, so it can gate CI.
"""

import argparse
import re
import sys
import time

from dotenv import load_dotenv

load_dotenv()

from database import Database  # noqa: E402
from langgraph_agent import CrimeInvestigationAgent  # noqa: E402

THRESHOLD = 0.80

# Behaviour worth watching that this suite does not assert on:
#
# The agent narrows questions. Asked the looser "are any suspects related to
# each other by family?" it required the relatives to have co-offended,
# found 3 such pairs, and reported "a total of 3 documented relationships"
# - true of the query it wrote, misleading as an answer, since there are 40.
# It states the narrowed result as though it were the whole picture rather
# than saying which question it actually answered.
EVAL_NOTES = __doc__

# question, ground-truth Cypher returning a single scalar `n`, relationship
# the generated Cypher must reference (or None)
CASES = [
    (
        "How many crimes are recorded in the database?",
        "MATCH (c:Crime) RETURN count(c) AS n",
        None,
    ),
    (
        "How many suspects are in the database?",
        "MATCH (p:Person) RETURN count(p) AS n",
        None,
    ),
    (
        "How many criminal organizations are there?",
        "MATCH (o:Organization) RETURN count(o) AS n",
        None,
    ),
    (
        "What crimes did Carlos Brown commit?",
        "MATCH (p:Person)-[:PARTY_TO]->(c:Crime) "
        "WHERE toLower(p.name) CONTAINS 'carlos brown' RETURN count(c) AS n",
        "PARTY_TO",
    ),
    (
        # Phrased precisely on purpose. The looser "are any suspects related
        # by family?" is ambiguous about whether the relatives must also be
        # co-offenders, and the agent reads it narrowly - see EVAL_NOTES.
        "How many family relationships are recorded between people in the database?",
        "MATCH (a:Person)-[r:FAMILY_REL]-(b:Person) WHERE a.name < b.name "
        "RETURN count(DISTINCT r) AS n",
        "FAMILY_REL",
    ),
    (
        "How many distinct modus operandi patterns are recorded?",
        "MATCH (m:ModusOperandi) RETURN count(m) AS n",
        "ModusOperandi",
    ),
    (
        "How many weapons have been recovered?",
        "MATCH (w:Weapon) WHERE w.recovered = true RETURN count(w) AS n",
        None,
    ),
    (
        "How many pieces of evidence are marked critical significance?",
        "MATCH (e:Evidence) WHERE e.significance = 'critical' RETURN count(e) AS n",
        None,
    ),
    (
        "How many investigators are assigned to cases?",
        "MATCH (i:Investigator) RETURN count(i) AS n",
        None,
    ),
    (
        "How many people are directly connected to Carlos Brown?",
        "MATCH (p:Person)-[:KNOWS]-(o:Person) "
        "WHERE toLower(p.name) CONTAINS 'carlos brown' RETURN count(DISTINCT o) AS n",
        "KNOWS",
    ),
]


def numbers_in(text: str) -> set[int]:
    """Every integer in the answer, comma separators removed."""
    return {int(m.replace(",", "")) for m in re.findall(r"\b\d[\d,]*\b", text)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="run only the first four cases")
    args = ap.parse_args()

    cases = CASES[:4] if args.quick else CASES
    db = Database()
    agent = CrimeInvestigationAgent()

    print(f"\n{'=' * 78}\nAGENT EVALUATION  ({len(cases)} cases)\n{'=' * 78}\n")

    passed, results = 0, []
    for i, (question, truth_cypher, must_use) in enumerate(cases, 1):
        expected = db.query(truth_cypher)[0]["n"]

        started = time.time()
        try:
            result = agent.ask(question)
        except Exception as e:  # a crash is a failure, not a stack trace
            results.append((question, expected, None, False, f"raised {type(e).__name__}", 0.0))
            print(f"[{i:2}/{len(cases)}] FAIL  {question}\n        raised {e}\n")
            continue
        elapsed = time.time() - started

        answer = result["answer"]
        cypher = " ".join(q for _, q in result["cypher_queries"])

        figure_ok = expected in numbers_in(answer)
        usage_ok = must_use is None or must_use.lower() in cypher.lower()
        ok = figure_ok and usage_ok
        passed += ok

        notes = []
        if not figure_ok:
            notes.append(f"expected {expected:,} not stated")
        if not usage_ok:
            notes.append(f"did not query {must_use}")

        results.append((question, expected, answer, ok, "; ".join(notes), elapsed))
        print(
            f"[{i:2}/{len(cases)}] {'PASS' if ok else 'FAIL'}  {question}\n"
            f"        truth={expected:,}  {elapsed:.1f}s"
            + (f"  -> {'; '.join(notes)}" if notes else "")
            + "\n"
        )

    rate = passed / len(cases)
    print(f"{'=' * 78}\nPASSED {passed}/{len(cases)}  ({rate:.0%})\n{'=' * 78}")

    if rate < THRESHOLD:
        print(f"\nBelow threshold ({THRESHOLD:.0%}). Failing cases:")
        for q, exp, ans, ok, notes, _ in results:
            if not ok:
                print(f"  - {q}\n      {notes}")
                if ans:
                    print(f"      said: {ans[:150].strip()}...")
        return 1

    print("\nNote: cases whose true figure is a small number can pass on a\n"
          "coincidental match; the relationship assertions are the stronger\n"
          "signal for those.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
