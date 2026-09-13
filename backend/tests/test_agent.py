"""Agent-logic regression tests.

Deliberately free of LLM and database calls - these exercise the decision
logic that let a confidently wrong answer through, so they must be fast
and deterministic enough to run on every commit.

Regression target: asked "Who is Carlos Brown?" then "What crimes did he
commit?", the agent answered "no record of crimes linked to Carlos Brown"
for a person with ten. Two independent faults combined:

  1. conversation history never reached entity extraction or Cypher
     generation, so "he" had no referent and query generation failed;
  2. the generic fallback plan then ran and returned rows, which validate()
     accepted as a successful retrieval.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from langgraph_agent import CrimeInvestigationAgent  # noqa: E402


def _agent():
    # Bypass __init__: these tests touch no LLM and need no credentials.
    return CrimeInvestigationAgent.__new__(CrimeInvestigationAgent)


def _rows(n):
    return [{"x": i} for i in range(n)]


class TestValidateDistrustsFallback:
    def test_fallback_results_do_not_count_as_an_answer(self):
        """Generic fallback queries return rows whatever was asked."""
        verdict = _agent().validate(
            {
                "context": {"all_organizations": _rows(5), "repeat_offenders": _rows(9)},
                "plan_source": "fallback",
                "retries": 0,
            }
        )
        assert verdict["verdict"] == "retry"
        assert verdict["retries"] == 1
        assert "fallback" in verdict["last_error"].lower()

    def test_generated_results_are_accepted(self):
        verdict = _agent().validate(
            {"context": {"crimes_by_person": _rows(10)}, "plan_source": "llm", "retries": 0}
        )
        assert verdict["verdict"] == "answer"

    def test_fallback_stops_retrying_once_exhausted(self):
        """The distrust must not turn into an infinite loop."""
        verdict = _agent().validate(
            {"context": {"all_organizations": _rows(5)}, "plan_source": "fallback", "retries": 2}
        )
        assert verdict["verdict"] == "answer"

    def test_zero_rows_still_retries(self):
        verdict = _agent().validate(
            {"context": {"database_stats": {"total_crimes": 670}}, "plan_source": "llm", "retries": 0}
        )
        assert verdict["verdict"] == "retry"

    def test_execution_errors_still_retry(self):
        verdict = _agent().validate(
            {"context": {}, "plan_source": "llm", "retries": 0, "last_error": "SyntaxError"}
        )
        assert verdict["verdict"] == "retry"


class TestHistoryReachesQueryGeneration:
    def test_recent_turns_are_included(self):
        block = _agent()._history_block(
            {
                "conversation_history": [
                    {"role": "user", "content": "Who is Carlos Brown?"},
                    {"role": "assistant", "content": "Carlos Brown is a 31 year old mechanic."},
                ]
            }
        )
        assert "Carlos Brown" in block
        # the instruction is what makes the model resolve the pronoun
        assert "he" in block.lower()

    def test_empty_history_adds_nothing(self):
        assert _agent()._history_block({"conversation_history": []}) == ""
        assert _agent()._history_block({}) == ""

    def test_history_is_bounded(self):
        """Long conversations must not grow the prompt without limit."""
        history = [{"role": "user", "content": f"question {i}"} for i in range(40)]
        block = _agent()._history_block({"conversation_history": history}, turns=4)
        assert "question 39" in block
        assert "question 0" not in block

    def test_long_messages_are_truncated(self):
        block = _agent()._history_block(
            {"conversation_history": [{"role": "assistant", "content": "x" * 5000}]}
        )
        assert len(block) < 1000
