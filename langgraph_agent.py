# langgraph_agent.py - LangGraph-based Graph RAG agent (replaces graph_rag.py)
#
# Graph shape:
#   extract_entities -> generate_cypher -> execute_query -> validate
#                            ^                                 |
#                            +--------- (retry on failure) ----+
#                                                              |
#                                                              v
#                                                       generate_answer
#
# Public surface mirrors GraphRAG exactly:
#   CrimeInvestigationAgent().ask_with_context(question, conversation_history)
#     -> {'answer', 'sources', 'cypher_queries', 'context'}

import json
import re
from typing import Annotated, Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph

import config
from database import Database

MAX_RETRIES = 2

# How many result rows are shown to the answer model per result set. Caps
# prompt size; the true total is always stated alongside (see generate_answer).
ANSWER_ROW_LIMIT = 40

# ============================================================
# GRAPH SCHEMA (fed to the LLM so it writes valid Cypher)
# ============================================================

GRAPH_SCHEMA = """NODE LABELS AND PROPERTIES:
  (:Person)        name, age, occupation
  (:Crime)         id, type, date, severity, status
  (:Organization)  name, type, territory, members_count
  (:Weapon)        id, type, make, model, recovered
  (:Vehicle)       id, make, model, year, color, license_plate, reported_stolen
  (:Evidence)      id, type, description, significance, verified
  (:Investigator)  id, name, badge_number, department, specialization, cases_solved, active_cases
  (:Location)      name
  (:ModusOperandi) id, description, signature_element, frequency, confidence_score

RELATIONSHIPS (direction matters):
  (Person)-[:KNOWS]-(Person)                  // treat as undirected, do NOT use an arrow
  (Person)-[:PARTY_TO]->(Crime)
  (Person)-[:MEMBER_OF]->(Organization)
  (Person)-[:OWNS]->(Weapon)
  (Person)-[:OWNS]->(Vehicle)
  (Crime)-[:OCCURRED_AT]->(Location)
  (Crime)-[:HAS_EVIDENCE]->(Evidence)
  (Crime)-[:USED_WEAPON]->(Weapon)
  (Crime)-[:INVOLVED_VEHICLE]->(Vehicle)
  (Crime)-[:INVESTIGATED_BY]->(Investigator)
  (Crime)-[:MATCHES_MO]->(ModusOperandi)
  (Evidence)-[:LINKS_TO]->(Person)
  (Person)-[:FAMILY_REL]->(Person)             // has a `relation` property, e.g. 'brother'

IMPORTANT - MODUS OPERANDI:
Questions about modus operandi, M.O., method, technique, signature or
"crimes committed the same way" must use (:ModusOperandi) via MATCHES_MO.
Do NOT approximate an MO by comparing weapon, vehicle or evidence type -
the graph records the actual MO, so inferring one from other attributes
produces a confidently wrong answer.

To find crimes sharing an MO:
  MATCH (c1:Crime)-[:MATCHES_MO]->(m:ModusOperandi)<-[:MATCHES_MO]-(c2:Crime)
  WHERE c1.id < c2.id
  RETURN m.description AS mo, m.signature_element AS signature,
         c1.type AS crime1, c2.type AS crime2 LIMIT 50

FAMILY_REL is stored one-way but is semantically mutual - match it without
an arrow, -[:FAMILY_REL]-, so relatives are found from either side.

DEDUPING SYMMETRIC PAIRS (applies to KNOWS, FAMILY_REL, and any arrowless
match): an undirected match returns every pair TWICE, once from each end,
which doubles counts and wastes the LIMIT. Always constrain the ordering so
each pair appears once:
  MATCH (a:Person)-[r:FAMILY_REL]-(b:Person)
  WHERE a.name < b.name
  RETURN a.name AS person1, b.name AS person2, r.relation AS relation
  LIMIT 50"""


# ============================================================
# STEP 4 (built here, on purpose): Neo4j query as a LangChain @tool
# ------------------------------------------------------------
# The execute_query node needs a callable retriever, so the tool wrapper
# from step 4 of the plan is defined here rather than in a separate file.
# It is a real @tool object, so it can also be bound to an LLM later if
# we ever move to tool-calling instead of a fixed graph edge.
# ============================================================

_db = None

# Anything that could mutate the graph. The agent is read-only by design.
_WRITE_CLAUSES = re.compile(
    r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|LOAD\s+CSV|FOREACH|CALL\s*\{)\b",
    re.IGNORECASE,
)


def get_db():
    """Lazily create one shared Database (neo4j driver) for the process."""
    global _db
    if _db is None:
        _db = Database()
    return _db


def _jsonable(value):
    """Make neo4j return values safe for json.dumps and st.json()."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    # neo4j Node / Relationship / Path / temporal types
    try:
        return {k: _jsonable(v) for k, v in dict(value).items()}
    except Exception:
        return str(value)


@tool
def run_cypher_query(cypher: str) -> list:
    """Run a read-only Cypher query against the Neo4j crime graph.

    Args:
        cypher: A complete Cypher statement. Read-only (MATCH/RETURN/WITH only).

    Returns:
        A list of result rows, each row a dict of column name -> value.
    """
    if _WRITE_CLAUSES.search(cypher):
        raise ValueError("Write/procedure clauses are not allowed - this agent is read-only.")

    rows = get_db().query(cypher)
    return [_jsonable(row) for row in rows]


# ============================================================
# STATE
# ============================================================


def _merge_dict(left: dict, right: dict) -> dict:
    return {**(left or {}), **(right or {})}


class AgentState(TypedDict, total=False):
    question: str
    conversation_history: list
    entities: dict
    plan: list                      # [{'name': str, 'cypher': str}] for this attempt
    plan_source: str                # 'llm' | 'fallback' - see validate()
    cypher_queries: list            # [(display_name, cypher)] accumulated across attempts
    context: Annotated[dict, _merge_dict]
    last_error: str
    retries: int
    verdict: str                    # 'ok' | 'retry'
    answer: str


# ============================================================
# AGENT
# ============================================================


class CrimeInvestigationAgent:
    def __init__(self, checkpointer=None):
        self.llm = None
        self.use_llm = False

        try:
            if not config.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY is not set")

            from langchain_groq import ChatGroq

            self.llm = ChatGroq(
                api_key=config.GROQ_API_KEY,
                model=config.GROQ_MODEL,
                temperature=0.2,
                max_tokens=1200,
            )
            self.use_llm = True
            print(f"✅ ChatGroq initialized ({config.GROQ_MODEL})")
        except Exception as e:
            print(f"⚠️ LLM unavailable, falling back to heuristics: {e}")

        self.graph = self._build_graph(checkpointer)

    # --------------------------------------------------------
    # Graph wiring
    # --------------------------------------------------------

    def _build_graph(self, checkpointer=None):
        workflow = StateGraph(AgentState)

        workflow.add_node("extract_entities", self.extract_entities)
        workflow.add_node("generate_cypher", self.generate_cypher)
        workflow.add_node("execute_query", self.execute_query)
        workflow.add_node("validate", self.validate)
        workflow.add_node("generate_answer", self.generate_answer)

        workflow.add_edge(START, "extract_entities")
        workflow.add_edge("extract_entities", "generate_cypher")
        workflow.add_edge("generate_cypher", "execute_query")
        workflow.add_edge("execute_query", "validate")
        workflow.add_conditional_edges(
            "validate",
            self.route_after_validate,
            {"retry": "generate_cypher", "answer": "generate_answer"},
        )
        workflow.add_edge("generate_answer", END)

        # checkpointer stays None until step 5 (SqliteSaver)
        return workflow.compile(checkpointer=checkpointer)

    # --------------------------------------------------------
    # LLM helpers
    # --------------------------------------------------------

    def _chat(self, system_prompt, user_prompt):
        response = self.llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
        return (response.content or "").strip()

    @staticmethod
    def _parse_json(raw):
        """Pull a JSON object/array out of an LLM response (handles ``` fences)."""
        text = raw.strip()
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        match = re.search(r"[\[{].*[\]}]", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError(f"Could not parse JSON from LLM response: {raw[:200]}")

    @staticmethod
    def _history_block(state, turns=4):
        """Recent turns, for nodes that must resolve references like "he".

        Without this the query-writing side of the agent sees each question
        in isolation, so a follow-up ("what crimes did he commit?") has no
        subject to resolve and the whole run derails.
        """
        history = (state.get("conversation_history") or [])[-turns:]
        if not history:
            return ""
        lines = "\n".join(
            f"{m.get('role', 'user').upper()}: {str(m.get('content', ''))[:400]}"
            for m in history
        )
        return (
            "\n\nRECENT CONVERSATION (resolve pronouns and references like "
            f'"he", "she", "they", "that gang" against this):\n{lines}'
        )

    @staticmethod
    def _heuristic_names(question):
        """Regex name extraction - same rules as GraphRAG._extract_person_names."""
        exclude = {"i", "chicago", "detective", "side", "gang", "crew",
                   "street", "show", "his", "her", "their", "who", "what", "which"}
        words = question.split()
        names = []
        i = 0
        while i < len(words):
            word = words[i].strip(".,!?*")
            if word and word[0].isupper() and word.lower() not in exclude:
                if i + 1 < len(words):
                    nxt = words[i + 1].strip(".,!?*")
                    if nxt and nxt[0].isupper() and nxt.lower() not in exclude:
                        names.append(f"{word} {nxt}")
                        i += 2
                        continue
            i += 1
        return names

    # --------------------------------------------------------
    # NODE 1: extract_entities
    # --------------------------------------------------------

    def extract_entities(self, state: AgentState) -> dict:
        question = state["question"]
        print(f"\n🔍 [extract_entities] {question}")

        entities = {"persons": [], "organizations": [], "locations": [], "intent": "general"}

        if self.use_llm:
            system_prompt = (
                "You extract entities from crime-investigation questions. "
                "Return ONLY a JSON object, no prose, with keys: "
                '"persons" (list of person names mentioned), '
                '"organizations" (list of gang/organization names), '
                '"locations" (list of place names), '
                '"intent" (one of: network, collaboration, influence, path, '
                'weapons, vehicles, evidence, investigators, hotspots, '
                'modus_operandi, family, general). '
                "Use [] when nothing matches. Do not invent names. "
                "If the question refers back to someone mentioned earlier "
                '(e.g. "he", "they", "that suspect"), resolve it to the '
                "actual name from the conversation below and return that."
            )
            try:
                parsed = self._parse_json(
                    self._chat(system_prompt, question + self._history_block(state))
                )
                for key in ("persons", "organizations", "locations"):
                    value = parsed.get(key) or []
                    entities[key] = [str(v) for v in value if isinstance(v, (str, int))]
                entities["intent"] = str(parsed.get("intent") or "general")
            except Exception as e:
                print(f"⚠️ entity extraction failed, using regex: {e}")
                entities["persons"] = self._heuristic_names(question)
        else:
            entities["persons"] = self._heuristic_names(question)

        print(f"   entities: {entities}")

        # Baseline stats, exactly like GraphRAG did - keeps the transparency
        # panel populated even if every generated query comes back empty.
        context = {}
        cypher_queries = []
        stats_query = "MATCH (c:Crime) RETURN count(c) as n"
        try:
            context["database_stats"] = {
                "total_crimes": run_cypher_query.invoke({"cypher": stats_query})[0]["n"],
                "total_persons": run_cypher_query.invoke(
                    {"cypher": "MATCH (p:Person) RETURN count(p) as n"}
                )[0]["n"],
            }
            cypher_queries.append(("Database Stats", stats_query))
        except Exception as e:
            print(f"❌ stats error: {e}")

        return {
            "entities": entities,
            "context": context,
            "cypher_queries": cypher_queries,
            "retries": 0,
            "last_error": "",
        }

    # --------------------------------------------------------
    # NODE 2: generate_cypher
    # --------------------------------------------------------

    def generate_cypher(self, state: AgentState) -> dict:
        question = state["question"]
        entities = state.get("entities", {})
        retries = state.get("retries", 0)
        last_error = state.get("last_error", "")

        print(f"🧠 [generate_cypher] attempt {retries + 1}")

        if not self.use_llm:
            return {"plan": self._fallback_plan(entities), "plan_source": "fallback"}

        system_prompt = f"""You write Cypher queries for a Neo4j crime-investigation knowledge graph.

{GRAPH_SCHEMA}

RULES:
1. Return ONLY a JSON array, no prose and no markdown fences.
2. Each element is an object: {{"name": "Short Human Readable Title", "cypher": "MATCH ..."}}
3. Produce 1-3 queries that together answer the question. Fewer, better queries beat many.
4. READ-ONLY. Never use CREATE, MERGE, SET, DELETE, REMOVE, DROP or CALL.
5. Always alias returned columns with AS (e.g. RETURN p.name AS name).
6. Always add a LIMIT (<= 50).
7. Match person/organization names case-insensitively so near-misses still hit:
   WHERE toLower(p.name) CONTAINS toLower('rodriguez')
8. KNOWS has no direction in this graph: use -[:KNOWS]- not -[:KNOWS]->.
9. Multi-hop uses a bounded range, e.g. -[:KNOWS*1..2]-.
10. Only use the labels, properties and relationships listed above."""

        user_prompt = (
            f"QUESTION: {question}\n\nEXTRACTED ENTITIES: {json.dumps(entities)}"
            + self._history_block(state)
        )

        if last_error:
            user_prompt += (
                f"\n\nThe previous attempt FAILED. Fix it.\n"
                f"PROBLEM: {last_error}\n"
                f"PREVIOUS CYPHER:\n"
                + "\n".join(q["cypher"] for q in state.get("plan", []))
                + "\n\nWrite different Cypher. If the problem was empty results, loosen the "
                "matching (case-insensitive CONTAINS, wider hop range, drop optional filters)."
            )

        try:
            parsed = self._parse_json(self._chat(system_prompt, user_prompt))
            if isinstance(parsed, dict):
                parsed = [parsed]

            plan = []
            for item in parsed:
                cypher = (item.get("cypher") or "").strip()
                if not cypher:
                    continue
                name = (item.get("name") or "Generated Query").strip()
                plan.append({"name": name, "cypher": cypher})

            if not plan:
                raise ValueError("LLM returned no usable queries")

            for step in plan:
                print(f"   → {step['name']}")
            return {"plan": plan, "plan_source": "llm"}

        except Exception as e:
            # The fallback is a safety net, not an answer to the question -
            # validate() must know these results are generic so it does not
            # mistake them for a successful retrieval.
            print(f"⚠️ cypher generation failed, using fallback plan: {e}")
            return {"plan": self._fallback_plan(entities), "plan_source": "fallback"}

    def _fallback_plan(self, entities):
        """Deterministic queries for when the LLM is down or unparseable."""
        persons = entities.get("persons") or []
        if persons:
            name = persons[0].replace("'", "")
            return [
                {
                    "name": f"{name} - Profile",
                    "cypher": (
                        f"MATCH (p:Person) WHERE toLower(p.name) CONTAINS toLower('{name}') "
                        "RETURN p.name AS name, p.age AS age, p.occupation AS occupation LIMIT 10"
                    ),
                },
                {
                    "name": f"{name} - Connections",
                    "cypher": (
                        f"MATCH (p:Person)-[:KNOWS]-(other:Person) "
                        f"WHERE toLower(p.name) CONTAINS toLower('{name}') "
                        "OPTIONAL MATCH (other)-[:MEMBER_OF]->(o:Organization) "
                        "RETURN DISTINCT other.name AS name, other.age AS age, "
                        "o.name AS gang LIMIT 30"
                    ),
                },
                {
                    "name": f"{name} - Crimes",
                    "cypher": (
                        f"MATCH (p:Person)-[:PARTY_TO]->(c:Crime) "
                        f"WHERE toLower(p.name) CONTAINS toLower('{name}') "
                        "RETURN c.type AS crime_type, c.date AS date, "
                        "c.severity AS severity LIMIT 20"
                    ),
                },
            ]

        return [
            {
                "name": "All Organizations",
                "cypher": (
                    "MATCH (o:Organization) RETURN o.name AS name, o.type AS type, "
                    "o.territory AS territory, o.members_count AS members "
                    "ORDER BY o.members_count DESC LIMIT 25"
                ),
            },
            {
                "name": "Repeat Offenders",
                "cypher": (
                    "MATCH (p:Person)-[:PARTY_TO]->(c:Crime) WITH p, count(c) AS crimes "
                    "WHERE crimes >= 2 OPTIONAL MATCH (p)-[:MEMBER_OF]->(o:Organization) "
                    "RETURN p.name AS name, p.age AS age, crimes, o.name AS gang "
                    "ORDER BY crimes DESC LIMIT 15"
                ),
            },
        ]

    # --------------------------------------------------------
    # NODE 3: execute_query  (uses the @tool from step 4)
    # --------------------------------------------------------

    def execute_query(self, state: AgentState) -> dict:
        plan = state.get("plan") or []
        print(f"⚡ [execute_query] running {len(plan)} quer{'y' if len(plan) == 1 else 'ies'}")

        context = {}
        cypher_queries = list(state.get("cypher_queries") or [])
        errors = []

        for step in plan:
            name, cypher = step["name"], step["cypher"]
            key = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "result"

            try:
                rows = run_cypher_query.invoke({"cypher": cypher})
                context[key] = rows
                cypher_queries.append((name, cypher))
                print(f"   ✅ {name}: {len(rows)} rows")
            except Exception as e:
                errors.append(f"{name}: {e}")
                print(f"   ❌ {name}: {e}")

        return {
            "context": context,
            "cypher_queries": cypher_queries,
            "last_error": " | ".join(errors),
        }

    # --------------------------------------------------------
    # NODE 4: validate
    # --------------------------------------------------------

    def validate(self, state: AgentState) -> dict:
        retries = state.get("retries", 0)
        errors = state.get("last_error", "")

        # Did anything other than the baseline stats come back with rows?
        data_rows = sum(
            len(v)
            for k, v in (state.get("context") or {}).items()
            if k != "database_stats" and isinstance(v, list)
        )

        if errors:
            problem = f"Cypher execution errors: {errors}"
        elif data_rows == 0:
            problem = "All queries executed successfully but returned 0 rows."
        elif state.get("plan_source") == "fallback":
            # The fallback plan asks generic questions (all organizations,
            # repeat offenders) that return rows regardless of what was
            # actually asked. Treating those rows as success let the agent
            # answer a question it never queried - and report absence of
            # evidence as evidence of absence.
            problem = (
                "Query generation failed, so a generic fallback plan ran instead. "
                "Its results do not answer the question. Write Cypher that targets "
                "the question directly, resolving any reference to an earlier turn "
                "into an explicit name."
            )
        else:
            problem = ""

        if problem and retries < MAX_RETRIES:
            print(f"🔁 [validate] retry {retries + 1}/{MAX_RETRIES} - {problem}")
            return {"verdict": "retry", "retries": retries + 1, "last_error": problem}

        print(f"✅ [validate] proceeding with {data_rows} data rows")
        return {"verdict": "answer", "last_error": problem}

    def route_after_validate(self, state: AgentState) -> str:
        return state.get("verdict", "answer")

    # --------------------------------------------------------
    # NODE 5: generate_answer
    # --------------------------------------------------------

    ANSWER_SYSTEM_PROMPT = """You are a crime investigation AI assistant. Answer using ONLY the provided database results.

CRITICAL FORMATTING RULES:
1. Write in NATURAL PARAGRAPHS - NO bullet points, NO lists, NO numbered items
2. Use **bold** for important names, numbers, and key facts
3. Write 2-4 flowing paragraphs that read naturally
4. Connect ideas smoothly between sentences
5. End with ONE follow-up question

WHAT TO BOLD:
- **Suspect names** (exact from data)
- **Organization names** (gangs, crews)
- **Exact numbers** (crime counts, connections, scores)
- **Crime types** when mentioned
- **Key findings** (influence scores, rankings)

ANTI-HALLUCINATION:
- Use ONLY data from the context
- Count items accurately - no rounding
- A result set may list only some of its rows. When it says rows are not
  shown, use the stated Count as the total - never count the visible rows
- Real names only - never invent
- If the results are empty, say so plainly instead of guessing

REMEMBER: Flowing paragraphs, not lists."""

    def generate_answer(self, state: AgentState) -> dict:
        context = state.get("context") or {}
        question = state["question"]
        print("✍️  [generate_answer]")

        if not self.use_llm:
            return {"answer": self._fallback_answer(context)}

        context_str = "\n=== DATABASE RESULTS ===\n\n"
        for key, value in context.items():
            if not value:
                continue
            context_str += f"{key.upper()}:\n"
            if isinstance(value, list):
                # The row cap keeps the prompt bounded, but a truncated list
                # previously looked identical to a complete one - so the model
                # counted the rows it could see and under-reported totals
                # (e.g. answering "3" when the result set held 50). State the
                # true total, and say explicitly when rows are withheld.
                context_str += f"Count: {len(value)} (this is the TRUE total)\n"
                for item in value[:ANSWER_ROW_LIMIT]:
                    context_str += f"  • {json.dumps(item, default=str)}\n"
                if len(value) > ANSWER_ROW_LIMIT:
                    context_str += (
                        f"  ... {len(value) - ANSWER_ROW_LIMIT} further rows not shown. "
                        f"Cite the Count above ({len(value)}) as the total; do NOT count "
                        f"the rows listed here.\n"
                    )
            elif isinstance(value, dict):
                context_str += f"{json.dumps(value, indent=2, default=str)}\n"
            context_str += "\n"

        history = ""
        for msg in (state.get("conversation_history") or [])[-6:]:
            history += f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}\n"
        if history:
            history = f"=== RECENT CONVERSATION ===\n{history}\n"

        try:
            answer = self._chat(
                self.ANSWER_SYSTEM_PROMPT, f"{history}QUESTION: {question}\n\n{context_str}"
            )
            if not answer or len(answer.strip()) < 10:
                answer = self._fallback_answer(context)
        except Exception as e:
            print(f"⚠️ answer generation failed: {e}")
            answer = self._fallback_answer(context)

        return {"answer": answer}

    def _fallback_answer(self, context):
        """Always return something readable, in the same paragraph style."""
        stats = context.get("database_stats") or {}
        data_keys = [k for k, v in context.items() if k != "database_stats" and v]

        if data_keys:
            summary = ", ".join(
                f"**{len(context[k])}** results for {k.replace('_', ' ')}"
                for k in data_keys[:4]
                if isinstance(context[k], list)
            )
            return (
                f"I queried the knowledge graph and retrieved {summary}. The raw records are "
                f"shown in the query transparency panel below, since the language model was "
                f"unavailable to summarise them.\n\nWould you like to rephrase the question?"
            )

        if stats.get("total_crimes"):
            return (
                f"I searched the knowledge graph but this question returned no matching records. "
                f"The database currently holds **{stats.get('total_crimes', 0)} crime incidents** "
                f"involving **{stats.get('total_persons', 0)} suspects**.\n\n"
                f"Would you like to try a broader question, such as who the most connected "
                f"suspects are?"
            )

        return (
            "I could not retrieve data from the knowledge graph for this question. Try something "
            "specific like 'Show me everyone within 2 degrees of David Rodriguez' or "
            "'Which suspects connect to multiple gangs?'\n\nWhat would you like to explore?"
        )

    # --------------------------------------------------------
    # PUBLIC API - same shape as GraphRAG
    # --------------------------------------------------------

    def ask(self, question):
        return self.ask_with_context(question, [])

    def ask_with_context(self, question, conversation_history, thread_id=None):
        """Returns {'answer', 'sources', 'cypher_queries', 'context'} - identical
        shape to GraphRAG.ask_with_context so app.py's transparency panel works."""
        initial_state = {
            "question": question,
            "conversation_history": conversation_history or [],
            "context": {},
            "cypher_queries": [],
            "retries": 0,
        }

        # thread_id is unused until the SqliteSaver checkpointer lands (step 5)
        run_config = {"configurable": {"thread_id": thread_id}} if thread_id else None

        try:
            final_state = self.graph.invoke(initial_state, config=run_config)
        except Exception as e:
            print(f"❌ agent run failed: {e}")
            return {
                "answer": f"The investigation agent hit an error: {e}",
                "sources": [],
                "cypher_queries": [],
                "context": {},
            }

        context = final_state.get("context") or {}
        return {
            "answer": final_state.get("answer") or self._fallback_answer(context),
            "sources": list(context.keys()),
            "cypher_queries": final_state.get("cypher_queries") or [],
            "context": context,
        }


# Test
if __name__ == "__main__":
    agent = CrimeInvestigationAgent()

    questions = [
        "Show me everyone within 2 degrees of David Rodriguez",
        "Which suspects share connections with multiple gangs?",
        "Find suspects who committed crimes together but aren't in the same gang",
    ]

    for q in questions:
        print(f"\n{'=' * 60}")
        print(f"Q: {q}")
        result = agent.ask(q)
        print(f"\nA: {result['answer']}")
        print(f"\nCypher Queries: {len(result['cypher_queries'])}")
        for i, (name, cypher) in enumerate(result['cypher_queries'], 1):
            print(f"  {i}. {name}")
        print(f"Context keys: {result['sources']}")
