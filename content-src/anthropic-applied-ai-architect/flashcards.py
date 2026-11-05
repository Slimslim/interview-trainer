"""Applied AI Architect, Industries: pre-sales architecture flashcards.

Facts come from research/anthropic-applied-ai-architect.md; `source` is the
research source id (S#, D#, B#).
"""
from _helpers import code


def card(id, stage, front, back, source=None, example=None, difficulty=1, tags=(), pattern=""):
    it = {
        "id": "aia-fc-" + id,
        "type": "flashcard",
        "stage": stage,
        "difficulty": difficulty,
        "tags": list(tags),
        "pattern": pattern,
        "front": front,
        "back": back,
    }
    if example:
        it["example"] = example
    if source:
        it["source"] = source
    return it


ITEMS = [
    # ---------- customer ----------
    card("discovery-structure", "customer",
         "What are the steps of a discovery call for an enterprise Claude deployment?",
         "1) Agenda & roles  2) Business context & KPIs  3) Current process & quantified pain  4) Data: sources, sensitivity, residency, access  5) Constraints: security, compliance (ZDR, region), procurement, integration  6) Success criteria & who owns the eval set  7) Stakeholders & decision process  8) Scoped pilot & next steps, then a written recap.",
         source="S13", difficulty=1, tags=["discovery"], pattern="Discovery structure"),
    card("play-back", "customer",
         "Before proposing a solution in discovery, what should you do?",
         "Play back what you heard in the customer's words (goal, pain, constraints, success metric) and check it's right. Then propose a narrow pilot with an eval set built from their real examples.",
         source="S13", difficulty=1, tags=["discovery"], pattern="Play back before proposing"),
    card("zdr-objection", "customer",
         "Customer: \"Our data can't leave the EU and we need zero data retention.\" What do you cover?",
         "Clarify the actual requirement (law, policy, or preference). Walk through the API data-retention / ZDR options, and deploying via cloud platforms (Bedrock, Google Cloud, Microsoft Foundry, Claude Platform on AWS) in their region. Confirm exact terms in writing; don't improvise.",
         source="D2", difficulty=2, tags=["zdr", "residency", "security"], pattern="Data-retention objection"),

    # ---------- design ----------
    card("workflow-vs-agent", "design",
         "Workflow vs agent: what's the difference, and which do you start with?",
         "Workflow: LLMs and tools follow predefined code paths. Agent: the LLM dynamically directs its own process and tool use. Start with the simplest thing (often a single call or a workflow); use an agent only when the steps can't be predicted and the extra cost/latency/risk is worth it.",
         source="B1", difficulty=1, tags=["agents", "architecture"], pattern="Workflow vs agent"),
    card("workflow-patterns", "design",
         "Name the five workflow patterns in 'Building effective agents'.",
         "Prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer.",
         source="B1", difficulty=2, tags=["agents", "patterns"], pattern="Workflow patterns"),
    card("agent-principles", "design",
         "What three principles does 'Building effective agents' give for agents?",
         "Keep the design simple; make the agent's planning visible (transparency); invest in the agent-computer interface (tool docs and testing).",
         source="B1", difficulty=2, tags=["agents"], pattern="Agent design principles"),
    card("model-tiering", "design",
         "How would you tier current Claude models in a customer architecture?",
         "Haiku 5.5 for high-volume, low-latency steps (routing, classification). Sonnet 5.5 for a speed/intelligence balance. Opus 5.5 is the recommended starting point for most workloads. Fable 5.1 for demanding reasoning and long-horizon agentic work. Choose per step using evals and cost.",
         source="D1", difficulty=2, tags=["models", "cost"], pattern="Model tiering"),
    card("contextual-retrieval", "design",
         "What is Contextual Retrieval and how much did it help?",
         "Prepend chunk-specific context (explaining where the chunk sits in its document) before embedding and BM25 indexing. It cut top-20 retrieval failures by 49% (contextual embeddings + contextual BM25), and by 67% with reranking.",
         source="B4", difficulty=2, tags=["rag", "retrieval"], pattern="Contextual retrieval"),
    card("rbac-retrieval", "design",
         "How do you enforce role-based access in an enterprise RAG system?",
         "Store source ACLs as metadata on every chunk, sync them from the source systems, and filter at retrieval time using the user's SSO identity (not a shared service account). Add leakage tests with users of different roles to the eval set, and audit-log queries and returned documents.",
         source="S12", difficulty=2, tags=["rag", "rbac", "security"], pattern="Permission-aware retrieval"),
    card("tool-design", "design",
         "Tool design tips from 'Writing effective tools for agents'?",
         "Choose a few deliberate, task-shaped tools (not a wrapper per API endpoint); namespace them (e.g. crm_search, erp_get_order); return high-signal, compact context; and test tools with evals.",
         source="B3", difficulty=2, tags=["tools", "mcp"], pattern="Tool design"),
    card("rollout", "design",
         "What's a safe rollout sequence for an enterprise LLM feature?",
         "Pilot with a small group and an eval set, then shadow mode (model runs alongside humans, outputs compared, not acted on), then staged launch by group or category. Add monitoring, cost controls and a feedback loop into the eval set.",
         source="S12", difficulty=1, tags=["rollout"], pattern="Pilot -> shadow -> staged"),
    card("human-checkpoints", "design",
         "Where do human checkpoints belong in an agent design?",
         "Before irreversible or high-impact actions (sending to customers, payments, writes to systems of record, parts orders), and as escalation for low confidence or out-of-scope cases. Log every approval.",
         difficulty=1, tags=["guardrails", "human-in-the-loop"], pattern="Approval gates"),

    # ---------- technical ----------
    card("prompt-caching", "technical",
         "How much do prompt-cache reads cost, and when do you use caching?",
         "Cache reads cost 10% of the base input price (5% on Opus 5.5 and Sonnet 5.5; 2.5% on Fable 5.1). Use it for long, repeated prefixes: system prompts, tool definitions, policy documents, few-shot examples.",
         source="D1", difficulty=2, tags=["cost", "caching"], pattern="Prompt caching"),
    card("batches", "technical",
         "When do you recommend the Message Batches API, and what does it save?",
         "For asynchronous, non-latency-sensitive work (overnight extraction, backfills, monthly reports, eval runs). Batches get a 50% discount.",
         source="D1", difficulty=1, tags=["cost", "batch"], pattern="Batch processing"),
    card("context-window", "technical",
         "Context window and max output on current Claude models?",
         "1M-token context window and 128K max output tokens on the current models (Fable 5.1, Opus 5.5, Sonnet 5.5, Haiku 5.5).",
         source="D1", difficulty=1, tags=["models"], pattern="Model limits"),
    card("browser-keys", "technical",
         "Can you call the Claude API directly from a browser for a customer app?",
         "Docs recommend a back end. Direct browser calls need the `anthropic-dangerous-direct-browser-access: true` header and are acceptable only for trusted internal tools or short-lived dev keys. Orgs with ZDR or the Compliance API enabled can't make browser (CORS) calls at all: they get a 401.",
         source="D4", difficulty=2, tags=["security", "api"], pattern="Keys server-side"),
    card("api-version", "technical",
         "What breaks if you move to `anthropic-version: 2026-10-21`?",
         "The `temperature`, `top_p` and `top_k` parameters are removed and return a 400 error. Don't send them with that version.",
         source="D3", difficulty=3, tags=["api"], pattern="API versioning"),
    card("take-home-structure", "technical",
         "Structure for presenting a take-home Claude app to a panel?",
         "1) Customer problem & success criteria  2) Architecture diagram  3) Prompt & tool design  4) Evals with numbers  5) Failure modes & guardrails  6) Cost & latency (caching, batches, model choice)  7) Next steps with the customer. State assumptions; leave time for Q&A.",
         source="S12", difficulty=1, tags=["take-home", "presentation"], pattern="Take-home presentation structure"),
    card("take-home-ai", "technical",
         "May you use Claude while building Anthropic's take-home?",
         "Not unless Anthropic says otherwise. Take-homes are done without Claude unless indicated, and live interviews are 'all you'. Using Claude to prepare is encouraged.",
         source="S9", difficulty=1, tags=["process"], pattern="Candidate AI guidance"),
    card("eval-harness", "technical",
         "How do you build an eval harness with a customer?",
         "Define success criteria with the customer; build a golden set from real cases (agents: start with 20-50 tasks from real failures); pick graders: code where possible, LLM judges calibrated against humans, human review; grade outcomes rather than paths; rerun on every prompt/model change; watch for saturation.",
         source="B2", difficulty=2, tags=["evals"], pattern="Eval harness for customers"),
    card("grader-types", "technical",
         "Three kinds of graders for LLM evals, and a trade-off for each?",
         "Code-based (fast, cheap, objective, but only for checkable outputs); model-based / LLM judge (flexible for open-ended outputs, must be calibrated against human labels); human (gold standard, slow and expensive, use for calibration and spot checks).",
         source="B2", difficulty=2, tags=["evals"], pattern="Grader types"),

    # ---------- screen / values ----------
    card("rsp-version", "values",
         "Current RSP version, and what triggers stronger safeguards?",
         "RSP v3.4, effective 2026-07-08. Capability thresholds trigger stronger ASL safeguards. The ASL-3 deployment standard is defense in depth: access controls, real-time classifiers, async monitoring, jailbreak rapid response.",
         source="B5", difficulty=2, tags=["rsp", "safety"], pattern="RSP basics"),
    card("core-views", "values",
         "Core Views on AI Safety in one sentence?",
         "Transformative AI may arrive within about a decade and nobody yet knows how to make it reliably safe, so Anthropic does empirical safety research on frontier systems with a portfolio approach across optimistic, intermediate and pessimistic scenarios.",
         source="B6", difficulty=2, tags=["core-views", "mission"], pattern="Core Views"),
    card("reported-screen-qs", "screen",
         "Which hiring-manager questions were reported on Glassdoor for Anthropic SA roles?",
         "Why you want to join; your views on Anthropic's research papers; and (one candidate) whether you'd be fine if the stock went to zero.",
         source="S10", difficulty=1, tags=["process", "motivation"], pattern="Reported screen questions"),
]
