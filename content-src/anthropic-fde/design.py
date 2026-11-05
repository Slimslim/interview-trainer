"""FDE: Claude deployment & system design scenarios (stage "design").

Scenarios are fictional. Rubric always has the same 7 criteria; evals weigh more.
"""
from _helpers import code


def rubric(req, arch, evals, guard, human, sec, roll):
    return [
        {"criterion": "Requirements", "lookFor": req, "weight": 1},
        {"criterion": "Architecture", "lookFor": arch, "weight": 1},
        {"criterion": "Evals", "lookFor": evals, "weight": 1.5},
        {"criterion": "Guardrails", "lookFor": guard, "weight": 1},
        {"criterion": "Human checkpoints", "lookFor": human, "weight": 1},
        {"criterion": "Security", "lookFor": sec, "weight": 1},
        {"criterion": "Rollout", "lookFor": roll, "weight": 1},
    ]


ITEMS = [
    {
        "id": "fde-ds-mcp-five-systems",
        "type": "design",
        "stage": "design",
        "difficulty": 3,
        "tags": ["mcp", "tools", "trust-boundaries", "enterprise"],
        "pattern": "MCP tool surface with least privilege",
        "source": "S15",
        "title": "Analysts need Claude on five siloed systems",
        "minutes": 15,
        "prompt": code("""
            A logistics company's 40 analysts spend hours pulling data from five systems:
            a Postgres warehouse, Salesforce, Jira, SharePoint and a legacy SOAP pricing
            service. They want to ask Claude questions and get answers with sources.

            Constraints:
            - Each analyst already has different permissions per system.
            - The pricing service is fragile (5 req/s max) and owned by another team.
            - Security insists nothing writes to Salesforce in phase 1.
            - Answers feed weekly exec reports, so wrong numbers are costly.

            Design the MCP tool surface, trust boundaries and how you'd prove it works.
        """),
        "rubric": rubric(
            "Asks which questions analysts ask most (top 20), latency tolerance, which numbers go to execs, who owns each system, and what 'correct' means for a figure.",
            "One MCP server per system (or per domain) with a few high-level, read-only tools (e.g. `query_shipments(filters)`, not raw SQL everywhere); namespaced tool names; Claude orchestrates with tool use; results returned compact with source ids; a cache/queue in front of the pricing service.",
            "Golden set of ~30-50 real analyst questions with known answers from past reports; grade numeric answers by code (exact/tolerance), tool choice by trace checks, narrative by LLM judge calibrated on human labels; regression run on every prompt/tool change.",
            "Read-only tools in phase 1; parameterised queries with row/column limits; tool outputs treated as untrusted (prompt injection in Jira/SharePoint text); answers must cite the tool result that produced each number; 'I couldn't find it' preferred over guessing.",
            "Numbers going into exec reports are reviewed by the analyst before export; any future write tool (Salesforce) gated behind explicit confirmation.",
            "Per-user auth passthrough (OAuth/on-behalf-of) so Claude sees only what the analyst can see; no shared super-user service account; secrets in a vault; audit log of every tool call with user, args and result hash.",
            "Start with 2 systems and 5 analysts, measure time saved and answer accuracy vs. golden set, then add systems one by one; rate-limit and circuit-breaker metrics for the pricing service before scaling.",
        ),
        "outline": code("""
            - Clarify: top questions, accuracy bar for exec numbers, per-system owners and permissions, volume (40 users).
            - Architecture: Claude + MCP servers per system; few task-shaped tools, namespaced (warehouse_*, crm_*); compact results with ids.
            - Pricing service: queue + cache + rate limiter (<5 req/s), circuit breaker, owner sign-off.
            - Trust boundaries: user identity passed through; read-only phase 1; tool results are data, never instructions.
            - Evals: 30-50 golden questions from past reports; code graders for numbers, trace checks for tool choice, calibrated LLM judge for prose; CI regression.
            - Guardrails: citations per number, refusal when data missing, query limits.
            - Human: analyst approves anything going into exec report.
            - Security: OAuth on-behalf-of, vault, per-call audit log.
            - Rollout: 2 systems, 5 analysts -> measure accuracy and hours saved -> add systems.
        """),
    },
    {
        "id": "fde-ds-finserv-drafting",
        "type": "design",
        "stage": "design",
        "difficulty": 3,
        "tags": ["regulated", "drafting", "financial-services", "compliance"],
        "pattern": "Draft-only agent with compliance review",
        "title": "Agent drafting customer messages at a bank",
        "minutes": 12,
        "prompt": code("""
            A mid-size retail bank wants Claude to draft replies to customer emails about
            card disputes, fees and account changes. 3,000 emails/day, 60 agents.

            Constraints:
            - Regulators require that no advice or binding promise is sent without
              human sign-off, and every outbound message is retained for 7 years.
            - Replies must follow approved wording for fees and dispute timelines.
            - Customer data includes account numbers and transaction history.
            - Compliance has vetoed two previous AI tools.

            Design the system and explain how you'd win compliance's approval.
        """),
        "rubric": rubric(
            "Clarifies email categories and their volume split, which topics are 'advice', approved templates/wording, target handle time, retention rules, and what compliance rejected before and why.",
            "Classify (fast cheap model) -> retrieve approved policy snippets and customer context via tools -> draft (stronger model) with structured output (draft, cited policy ids, risk flags) -> agent review UI in the existing CRM.",
            "Golden set of real anonymised emails per category with compliance-approved answers; graders for policy-wording adherence (code/regex for mandatory phrases), factual consistency with account data, tone; track agent edit distance and override rate in production.",
            "Drafts restricted to approved templates for fees/timelines; forbidden-promise detector (e.g. 'we will refund'); out-of-scope categories routed to human with no draft; prompt-injection defences since emails are untrusted input.",
            "Every draft reviewed and sent by a human agent; high-risk flags (complaint, vulnerability, legal threat) require supervisor review; compliance samples a % weekly.",
            "Data minimisation (only fields needed for the case); check data retention / ZDR options and residency with the bank; least-privilege tool access; immutable audit log of input, draft, edits and final message for 7 years.",
            "Shadow mode first (drafts generated but not shown, compared to human replies), then one category (e.g. fee questions) with 5 agents, then expand by category once override rate and compliance sampling meet agreed thresholds.",
        ),
        "outline": code("""
            - Discovery: categories and volumes, what counts as advice, approved wording, why prior tools were vetoed.
            - Flow: classify (Haiku) -> retrieve policy + customer context -> draft (Sonnet/Opus) with structured output incl. cited policy ids and risk flags.
            - Human: agent always sends; supervisor for complaints/vulnerable customers; compliance sampling.
            - Guardrails: template-locked fee/timeline wording, forbidden-promise check, untrusted email content, no draft for out-of-scope.
            - Evals: per-category golden set signed off by compliance; mandatory-phrase checks; edit distance and override rate live.
            - Security: data minimisation, retention/ZDR and residency review, 7-year audit trail.
            - Rollout: shadow -> one category -> expand; bring compliance in as co-owner of the eval set.
        """),
    },
    {
        "id": "fde-ds-hosted-vs-self-hosted",
        "type": "design",
        "stage": "design",
        "difficulty": 2,
        "tags": ["deployment", "hosted", "self-hosted", "tradeoffs"],
        "pattern": "Hosted vs self-hosted decision framing",
        "source": "S15",
        "title": "Hosted API or self-hosted open weights?",
        "minutes": 10,
        "prompt": code("""
            An industrial manufacturer wants an assistant over 20 years of service tickets
            and manuals. Their CISO says: "No data leaves our network. Let's just run an
            open-weights model on our own GPUs." The CTO wants the best answer quality and
            a pilot in 8 weeks. The IT team has never run GPU infrastructure.

            Compare hosted Claude (API or via a cloud platform) with self-hosting, and
            make a recommendation you can defend to both the CISO and the CTO.
        """),
        "rubric": rubric(
            "Unpacks 'no data leaves': is it a legal requirement, a policy, or a fear? Which data is actually sensitive? Residency needs, quality bar, users and volume, 8-week deadline.",
            "Lays out options: Claude API with retention controls, Claude via the customer's existing cloud provider in their region/VPC, self-hosted open weights; compares quality, ops burden, time to pilot, cost at their volume; keeps retrieval index on-prem either way.",
            "Proposes a side-by-side eval on 50 real tickets with known resolutions so the decision is made on data, not opinions; same harness reused later for regressions.",
            "Redaction/minimisation of sensitive fields before any model call; citations to source tickets; refusal when no supporting document.",
            "Technicians confirm suggested fixes before acting; feedback button feeds the eval set.",
            "Clear data-flow diagram; contractual terms, data retention/ZDR options and cloud-region choices reviewed with the CISO; customer-managed keys and private networking where available; audit logs.",
            "Recommend a hosted pilot through the cloud platform the CISO already trusts, limited to non-sensitive manuals first, with an exit criterion and a documented path if the eval says otherwise.",
        ),
        "outline": code("""
            - Start with the CISO's actual requirement; separate law/policy/fear; classify data.
            - Options table: API (+ retention settings), Claude via existing cloud provider in-region, self-host open weights.
            - Criteria: answer quality, ops burden (they have no GPU team), time-to-pilot (8 weeks), security posture, cost.
            - Keep documents and vector index inside their network; send only retrieved snippets.
            - Settle it with a 50-ticket bake-off eval.
            - Recommendation: hosted via their cloud provider, non-sensitive corpus first; revisit with eval data.
            - Be honest about tradeoffs; don't trash self-hosting.
        """),
    },
    {
        "id": "fde-ds-ticket-triage",
        "type": "design",
        "stage": "design",
        "difficulty": 2,
        "tags": ["triage", "classification", "escalation", "support"],
        "pattern": "Routing workflow with confidence-based escalation",
        "title": "Support-ticket triage agent with escalation",
        "minutes": 12,
        "prompt": code("""
            A SaaS company gets 8,000 support tickets/day in English, German and Spanish.
            Today humans tag each ticket (product area, severity, language) and route it,
            with a 4-hour median delay. They want Claude to triage, suggest an answer for
            easy tickets, and escalate anything risky.

            Constraints:
            - Sev-1 outages must reach on-call within 5 minutes.
            - About 15% of tickets are billing disputes that legal wants humans to own.
            - Budget is tight: cost per ticket matters.

            Design it.
        """),
        "rubric": rubric(
            "Asks for current tag taxonomy and its accuracy, examples of misroutes, what 'easy' means, SLA per severity, languages, peak volume, cost target per ticket.",
            "Workflow, not open-ended agent: small fast model classifies to structured JSON (area, severity, language, confidence); deterministic routing rules; KB retrieval + draft only for easy categories; batch API for non-urgent backfill/re-tagging; prompt caching for the long system prompt and taxonomy.",
            "Labelled set from historical tickets (stratified by area, severity and language); per-class precision/recall with special focus on Sev-1 recall and billing detection; confusion matrix review; monitor drift weekly.",
            "Low-confidence or ambiguous -> human queue; Sev-1 keyword/heuristic backstop in parallel with the model; billing always routed to humans with no draft; injection-safe handling of ticket text.",
            "Human agents approve suggested answers before sending; on-call paged directly for Sev-1; weekly review of escalations and misroutes.",
            "PII in tickets: minimise fields sent, retention settings, access by role; logs of classification decisions for audit.",
            "Shadow mode: model tags in parallel with humans for 2 weeks and compare; then auto-route high-confidence tickets in one language; add suggested answers last.",
        ),
        "outline": code("""
            - Clarify taxonomy, SLAs, what 'easy' and 'risky' mean, cost target.
            - Workflow: classify (Haiku, structured output with confidence) -> rules route -> optional draft with KB retrieval for easy classes.
            - Cost: caching of system prompt/taxonomy; batch for non-urgent work; small model for routing.
            - Escalation: low confidence, billing, Sev-1 (with keyword backstop), legal threats.
            - Evals: historical labelled set; Sev-1 recall is the key metric; per-language breakdown.
            - Rollout: shadow -> auto-route high-confidence -> drafts.
        """),
    },
    {
        "id": "fde-ds-kb-rbac",
        "type": "design",
        "stage": "design",
        "difficulty": 3,
        "tags": ["rag", "rbac", "knowledge-base", "citations"],
        "pattern": "Permission-aware retrieval",
        "title": "Knowledge-base Q&A with role-based access",
        "minutes": 15,
        "prompt": code("""
            A 5,000-person engineering firm wants employees to ask Claude questions over
            Confluence, SharePoint and a contracts archive. HR and legal documents must
            only be visible to people allowed to see them today. Leadership wants
            "ChatGPT for our company" in Teams within one quarter.

            Constraints:
            - Permissions change daily (joiners, leavers, project teams).
            - Many documents are outdated or contradictory.
            - Contract terms must be quoted exactly, never paraphrased.

            Design the system.
        """),
        "rubric": rubric(
            "Identifies the top use cases and user groups instead of 'everything for everyone'; asks about document owners, freshness, which sources are authoritative, and what a wrong answer costs.",
            "Ingest with ACL metadata per chunk; contextual retrieval (chunk context + embeddings + BM25, rerank); permission filter applied at retrieval time from the user's identity; Claude answers with citations; Teams bot front end.",
            "Golden set per use case (HR policy, project docs, contracts) incl. 'should refuse / not permitted' cases; retrieval metrics (recall@k) separately from answer quality; leakage tests with test users of different roles; regression on index or prompt changes.",
            "Answer only from retrieved sources with citations; quote contract clauses verbatim from source; flag conflicting or stale docs (show date); say 'not found' instead of guessing; documents treated as untrusted content.",
            "Content owners review flagged stale/conflicting docs; legal confirms any contract interpretation; feedback buttons route to owners.",
            "ACL sync from source systems on a schedule plus check at query time; no index-wide service account answering for users; SSO identity; audit log of queries and documents returned; retention settings reviewed.",
            "Pilot one department and one source with clean permissions, measure accuracy and leakage tests, then add sources; communicate limits clearly to set expectations.",
        ),
        "outline": code("""
            - Narrow: pick 2-3 use cases and one department first.
            - Ingest: chunk + contextual retrieval, store ACLs and doc dates as metadata; sync permissions often.
            - Query: SSO identity -> permission-filtered hybrid search -> rerank -> Claude answers with citations.
            - Contracts: verbatim quotes only, link to source.
            - Evals: retrieval recall, answer correctness, refusal cases, cross-role leakage tests.
            - Guardrails: citations required, freshness flags, 'not found' over guessing.
            - Rollout: one department, one source -> expand; owners fix stale content.
        """),
    },
    {
        "id": "fde-ds-batch-extraction",
        "type": "design",
        "stage": "design",
        "difficulty": 2,
        "tags": ["batch", "extraction", "structured-output", "evals"],
        "pattern": "Batch extraction pipeline with an eval set",
        "title": "Batch document extraction pipeline",
        "minutes": 10,
        "prompt": code("""
            An insurer receives 200,000 PDF claim forms and repair invoices per month.
            Clerks type 25 fields per document into the claims system. They want Claude
            to extract the fields overnight, with results ready by 7 am.

            Constraints:
            - Some PDFs are scans, some are handwritten, some in French or Italian.
            - Payment amounts must be right: a wrong IBAN or amount is a real loss.
            - Finance wants a cost estimate before approving the project.

            Design the pipeline and how you'd measure accuracy.
        """),
        "rubric": rubric(
            "Asks for field list and which fields are critical (amount, IBAN, policy number), document mix, current clerk error rate, overnight window, cost ceiling.",
            "Queue -> Batch API (50% cheaper, async fits overnight) -> structured output schema per document type -> validation layer (IBAN checksum, amount totals, policy lookup) -> claims system; prompt caching for the shared instructions; model choice by doc type after eval.",
            "Hand-labelled set of a few hundred documents stratified by type/language/scan quality; field-level accuracy with exact match for critical fields; compare against clerk baseline; cost per document measured; rerun on prompt/model changes.",
            "Schema-constrained output; deterministic checks (checksums, totals, cross-field consistency); 'unreadable' allowed as a value instead of guessing; documents treated as data, not instructions.",
            "Documents failing validation or with low-confidence critical fields go to a clerk review queue; payments above a threshold always human-confirmed.",
            "PII and bank data: retention settings, encrypted storage, least-privilege access to the claims system, audit trail linking each field to source document and model version.",
            "Run in parallel with clerks for a month on one document type, compare accuracy and cost, then switch clerks to review-only for that type and expand.",
        ),
        "outline": code("""
            - Clarify critical fields, doc mix, clerk baseline, budget.
            - Pipeline: ingest -> batch requests (cheap, async) -> JSON schema per doc type -> validators -> claims system.
            - Cost estimate: docs x tokens per doc x price, with batch discount and caching; test Haiku vs Sonnet on the eval.
            - Evals: labelled set, field-level accuracy, critical fields exact-match, compare to human baseline.
            - Human queue for failed validation / low confidence / large payments.
            - Rollout: parallel run on one doc type -> review-only -> expand.
        """),
    },
    {
        "id": "fde-ds-research-agent-evals",
        "type": "design",
        "stage": "design",
        "difficulty": 3,
        "tags": ["agents", "web-search", "evals", "research"],
        "pattern": "Evaluating an agent that browses",
        "title": "Supplier-research agent with web search",
        "minutes": 12,
        "prompt": code("""
            A procurement team wants an agent that, given a part description, searches the
            web and internal supplier records, then writes a one-page shortlist of 3-5
            qualified suppliers with prices and lead times. Today a buyer spends half a
            day per request.

            Constraints:
            - The agent must never contact suppliers or place orders.
            - Buyers distrust it after a demo invented a supplier.
            - 300 requests/month.

            Design the agent and especially how you'd evaluate it.
        """),
        "rubric": rubric(
            "Asks what makes a supplier 'qualified', where internal records live, how buyers judge a good shortlist today, acceptable turnaround, and what went wrong in the demo.",
            "Orchestrator with web search tool + read-only supplier-DB tool; fixed steps (search, verify, compare, write) rather than unlimited autonomy; every claim stored with its source URL/record; report template.",
            "20-50 past requests with buyer-made shortlists as reference; graders: code checks that every supplier has a valid source link, LLM judge for relevance calibrated against buyer ratings, human spot-checks; track hallucinated-supplier rate as a hard metric (target 0); run on each prompt change.",
            "No outbound actions (no email/order tools exposed at all); claims without a source are dropped or marked unverified; web content treated as untrusted (prompt injection); step and cost limits.",
            "Buyer reviews and approves the shortlist before any contact; buyer feedback captured per report.",
            "Read-only credentials for internal records; logs of searches and sources; no internal pricing data sent to external sites.",
            "Start with 2 buyers on low-value parts, show the hallucination metric weekly to rebuild trust, expand by category.",
        ),
        "outline": code("""
            - Rebuild trust: name the demo failure and design against it (source for every claim).
            - Agent: bounded steps, tools = web_search + supplier_db (read-only); no contact/order tools.
            - Output: template with source links per field.
            - Evals: past requests + buyer shortlists; link-validity code check; calibrated LLM judge; hallucination rate as a gate.
            - Guardrails: untrusted web content, step/cost caps.
            - Human: buyer approves before contact.
            - Rollout: 2 buyers, low-value parts, weekly metric review.
        """),
    },
]
