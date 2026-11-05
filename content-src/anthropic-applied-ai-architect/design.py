"""Applied AI Architect, Industries: enterprise design scenarios (fictional customers)."""
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
        "id": "aia-ds-quality-deviation-rag",
        "type": "design",
        "stage": "design",
        "difficulty": 3,
        "tags": ["manufacturing", "rag", "multilingual", "quality"],
        "pattern": "Multilingual RAG over controlled documents",
        "title": "Quality-deviation assistant over multilingual SOPs",
        "minutes": 15,
        "prompt": code("""
            A machinery maker with plants in Germany, the French-speaking part of
            Switzerland and China wants quality engineers to describe a deviation
            (e.g. weld porosity on line 3) and get the relevant SOP steps, past
            deviation reports and a draft CAPA.

            Constraints:
            - 12,000 SOPs and reports in German, French and Chinese; many have
              several revisions and only the released one is valid.
            - The quality system (QMS) is the system of record; audits are strict.
            - China plant data must stay in-region.

            Design it.
        """),
        "rubric": rubric(
            "Asks who uses it (quality engineers vs operators), top deviation types, how CAPAs are written and approved today, revision control rules, audit requirements, residency per plant.",
            "Ingest only released SOP revisions from the QMS with metadata (plant, line, revision, language); contextual retrieval (contextual embeddings + BM25 + rerank) across languages; Claude answers in the user's language but quotes the source in its original language with citations; CAPA draft as structured output; regional deployment for China data.",
            "Golden set of ~50 past deviations per plant with the SOPs an expert would cite and the final CAPA; retrieval recall@k by language; citation accuracy (code check that cited revision is the released one); LLM-judge for CAPA quality calibrated with quality engineers; regression on re-indexing.",
            "Answer only from retrieved released documents; flag when no SOP matches; never invent SOP numbers; translation shown as aid with original text; documents treated as data.",
            "Quality engineer edits and approves every CAPA in the QMS; Claude never writes to the QMS directly; escalation for safety-critical deviations.",
            "RBAC from plant/role in identity provider applied at retrieval; regional data separation; audit log of queries, retrieved docs and drafts; retention settings reviewed with IT and quality.",
            "Pilot one plant and one deviation category, measure time-to-draft and citation accuracy against golden set, then add plants/languages; shadow mode on live deviations before engineers rely on it.",
        ),
        "outline": code("""
            - Discovery: users, top deviation types, CAPA process, audit rules, residency per plant.
            - Corpus: released revisions only, metadata per chunk, multilingual contextual retrieval + rerank.
            - Answer: user's language, original-language quotes, citations with revision id; CAPA as structured draft.
            - Evals: 50 past deviations per plant; recall@k per language; citation validity; calibrated judge for CAPA.
            - Guardrails: no answer without source; never fabricate SOP ids.
            - Human: engineer approves CAPA in QMS; no direct writes.
            - Security: RBAC by plant/role, China data in-region, audit trail.
            - Rollout: one plant/category -> shadow -> expand.
        """),
    },
    {
        "id": "aia-ds-field-service-offline",
        "type": "design",
        "stage": "design",
        "difficulty": 3,
        "tags": ["oil-and-gas", "field-service", "offline", "connectivity"],
        "pattern": "Design for intermittent connectivity",
        "title": "Field-service assistant for remote oil & gas sites",
        "minutes": 15,
        "prompt": code("""
            An oilfield services company wants a technician assistant for pump and
            compressor maintenance: troubleshooting help from manuals, past work orders
            and sensor alarms, plus drafting the work report.

            Constraints:
            - Many sites have satellite links that drop for hours; bandwidth is low.
            - Technicians wear gloves; tablets are shared.
            - Safety procedures (lock-out/tag-out) must never be skipped or paraphrased.
            - Parts orders go through SAP and need supervisor approval.

            Design it.
        """),
        "rubric": rubric(
            "Asks about connectivity patterns, which tasks happen offline vs online, device constraints (gloves, shared tablets, voice), safety-critical procedures, SAP workflow, languages.",
            "Hybrid: pre-sync job packs before a visit (manuals, asset history, safety procedures) for offline lookup; Claude calls queued when online for troubleshooting and report drafting; compact prompts and responses for low bandwidth; voice-to-text input; SAP integration via a narrow tool that creates a draft parts request only.",
            "Eval set from past work orders with known root causes; measure top-3 diagnosis hit rate, report completeness against template, and safety-procedure fidelity (code check that LOTO text is verbatim); test with degraded/timeout network conditions.",
            "Safety procedures displayed verbatim from source, never generated; assistant says 'unknown, contact engineering' when out of scope; no instructions that override safety documents.",
            "Supervisor approves any parts order; technician signs off the report; high-risk equipment recommendations escalated to an engineer.",
            "Per-user login on shared tablets; device encryption for synced packs; scoped SAP permissions; audit log synced when connectivity returns; data retention reviewed.",
            "Pilot at one well-connected site first, then one remote site to test offline behaviour; collect technician feedback; scale by asset type.",
        ),
        "outline": code("""
            - Discovery: connectivity, offline tasks, devices, safety-critical steps, SAP flow.
            - Offline layer: pre-synced job packs + local search; safety docs shown verbatim.
            - Online layer: Claude for troubleshooting and report drafts, queued and retried; small payloads.
            - SAP: draft-only parts request tool; supervisor approval.
            - Evals: past work orders, top-3 diagnosis, LOTO verbatim check, degraded-network tests.
            - Security: per-user auth on shared devices, encryption, scoped SAP access.
            - Rollout: connected site -> remote site -> scale by asset type.
        """),
    },
    {
        "id": "aia-ds-take-home-plan",
        "type": "design",
        "stage": "technical",
        "difficulty": 2,
        "tags": ["take-home", "presentation", "demo"],
        "pattern": "Take-home presentation structure",
        "source": "S13",
        "title": "Take-home: present a small Claude app for a fictional customer",
        "minutes": 12,
        "prompt": code("""
            Take-home brief (practice version): "Coastline Logistics wants to cut the
            time dispatchers spend reading carrier emails about delays. Build a small
            Claude-powered app in ~4 hours and present it in 30 minutes."

            You've built a prototype that reads emails, extracts shipment id, new ETA
            and reason, and flags urgent ones.

            Outline your 30-minute presentation and live demo. What do you show, in
            what order, and what numbers do you bring?
        """),
        "rubric": rubric(
            "Opens with the customer's problem and success criteria in their terms (minutes per dispatcher per day, missed urgent delays); states assumptions explicitly.",
            "Simple architecture diagram: email in -> Claude with structured output (JSON schema) -> validation -> dashboard/alert; explains model choice (small fast model for extraction, why), and why a workflow, not an agent.",
            "Shows a small labelled eval set (e.g. 30-50 emails incl. edge cases) with field-level accuracy and urgent-flag precision/recall; shows one failure case honestly.",
            "Covers failure modes: missing fields, ambiguous dates/time zones, prompt injection in emails; 'unknown' allowed; validation rules.",
            "Explains where a dispatcher confirms before any customer notification is sent.",
            "Mentions API keys server-side (never in the browser), data retention options, PII in emails.",
            "Cost and latency per email (caching for the shared prompt, batches for backfill), and a concrete next step: pilot with 3 dispatchers, success metric, timeline; leaves time for Q&A.",
        ),
        "outline": code("""
            1. Customer problem + success criteria (2 min); assumptions.
            2. Live demo of the happy path, then one tricky email (5-7 min).
            3. Architecture diagram; workflow vs agent; model choice (3 min).
            4. Prompt and schema design; tool design if any (3 min).
            5. Evals with numbers: dataset, accuracy per field, urgent recall, one failure (5 min).
            6. Failure modes and guardrails; security (keys server-side, retention) (3 min).
            7. Cost/latency per email; caching, batches (2 min).
            8. Next steps with the customer: pilot, metric, owner (2 min).
            9. Q&A (5+ min).
        """),
    },
    {
        "id": "aia-ds-pdm-report-summarizer",
        "type": "design",
        "stage": "design",
        "difficulty": 2,
        "tags": ["manufacturing", "predictive-maintenance", "summarization", "evals"],
        "pattern": "Summarisation evals that check facts, not style",
        "title": "Predictive-maintenance report summariser",
        "minutes": 10,
        "prompt": code("""
            A packaging-machine manufacturer sends customers monthly predictive-
            maintenance reports: 40-page PDFs with vibration trends, alarms and
            recommendations. Customers don't read them. The company wants Claude to
            produce a one-page summary per machine for plant managers, in English,
            German or Spanish.

            Constraints: 3,000 reports/month; numbers and recommendations must match
            the source exactly; the service team is liable for recommendations.

            Design the system with a strong eval plan.
        """),
        "rubric": rubric(
            "Asks what plant managers decide from the report, which fields matter (risk level, recommended action, deadline), how the service team writes recommendations today, languages and timing.",
            "Monthly Batch API run (cost, not latency-sensitive); structured extraction of key facts first, then summary generation from extracted facts; shared instructions cached; template per language.",
            "Eval set of past reports with service-engineer-written summaries; code checks that every number and part id in the summary exists in the source; LLM judge for completeness of top risks calibrated against engineers; track 'missed critical alarm' rate as a gate.",
            "Recommendations copied from the engineer-written source, not invented; summary must cite page/section; uncertainty language preserved; no new advice generated.",
            "Service engineer approves summaries for machines flagged high-risk; random sample review for the rest.",
            "Customer data separated per customer tenant; retention settings; audit trail of source, summary and approver.",
            "Pilot with 3 friendly customers and one machine type, gather plant manager feedback (did they act sooner?), then expand languages and machine types.",
        ),
        "outline": code("""
            - Clarify decisions plant managers make; critical fields; liability.
            - Pipeline: batch extraction of facts -> summary from facts -> per-language template.
            - Evals: number/part-id faithfulness check by code, critical-alarm recall, calibrated judge.
            - Guardrails: no new recommendations; citations to page.
            - Human: engineer approves high-risk; sampling for the rest.
            - Rollout: 3 customers, one machine type, measure action rate.
        """),
    },
    {
        "id": "aia-ds-legacy-erp-integration",
        "type": "design",
        "stage": "design",
        "difficulty": 3,
        "tags": ["integration", "legacy", "erp", "mcp"],
        "pattern": "Secure integration with legacy systems",
        "source": "S12",
        "title": "Claude agent on a legacy ERP",
        "minutes": 12,
        "prompt": code("""
            A chemicals distributor runs a 15-year-old on-prem ERP with a SOAP API and
            nightly CSV exports. Sales reps want to ask Claude about order status,
            stock and customer credit limits from Microsoft Teams, and later let it
            create quotes.

            Constraints: the ERP team will only expose read endpoints at first; credit
            limits are confidential to finance and the rep's own accounts; the ERP
            slows down under load.

            Design the integration.
        """),
        "rubric": rubric(
            "Asks top rep questions, data freshness needed (live vs nightly ok), who may see credit limits, ERP load limits, future write use cases.",
            "Integration layer (MCP server or internal API) in front of the ERP with task-shaped read tools; cache/replica from nightly exports for heavy queries; live SOAP calls only where freshness matters; Teams bot front end; workflow over agent for phase 1.",
            "Test set of real rep questions with ERP-verified answers; code graders on figures; tool-selection accuracy; load tests against the ERP; regression on tool or prompt changes.",
            "Read-only tools; rate limiting and circuit breaker; tool results validated and summarised; refuse when data unavailable.",
            "Future quote creation as draft for rep confirmation, with manager approval above a threshold.",
            "User identity passed through so reps only see their accounts; credit limits filtered by role; service credentials in a vault; audit log of every tool call.",
            "Phase 1 read-only with 10 reps, measure time saved and ERP load; phase 2 draft quotes behind approval.",
        ),
        "outline": code("""
            - Clarify questions, freshness, permissions, ERP limits.
            - Integration layer with few read tools; cache from nightly exports; live calls sparingly.
            - Identity passthrough and role filtering for credit data.
            - Evals: real questions with ERP answers; tool selection; load tests.
            - Phase 2: draft quotes + approval gate.
            - Rollout: 10 reps read-only -> writes behind approval.
        """),
    },
]
