"""Applied AI Architect, Industries: discovery role-plays (stage "customer"). Fictional companies."""
from _helpers import code

COMMON = (
    " Stay in character the whole time. You are speaking aloud, so keep every reply"
    " to 1-3 short sentences. Never volunteer the hidden facts: reveal one only when"
    " the learner asks a question that clearly targets it. If the learner proposes a"
    " solution before understanding your situation, push back (\"You haven't asked"
    " how we work yet.\"). Do not coach the learner or break character."
)


def rubric(*extra):
    base = [
        {"criterion": "Users & workflow", "lookFor": "Asked who would use it, for what task, and how the work is done today, with volumes.", "weight": 1},
        {"criterion": "Data boundaries", "lookFor": "Asked about data sources, sensitivity, residency, retention and access.", "weight": 1},
        {"criterion": "Past attempts", "lookFor": "Asked what was tried before and what happened.", "weight": 1},
        {"criterion": "Success criteria", "lookFor": "Agreed a measurable success metric and who owns the eval set.", "weight": 1.5},
        {"criterion": "Constraints & stakeholders", "lookFor": "Uncovered security, procurement, integration constraints and the decision process.", "weight": 1},
        {"criterion": "Played back", "lookFor": "Summarised what they heard and checked it before proposing.", "weight": 1},
        {"criterion": "Narrow pilot with eval", "lookFor": "Proposed a scoped pilot with a test set from real examples and clear next steps (and a written recap).", "weight": 1.5},
        {"criterion": "No over-promising", "lookFor": "Was honest about limits and uncertainty; no invented accuracy, price or timeline commitments.", "weight": 1},
    ]
    return base + list(extra)


ITEMS = [
    {
        "id": "aia-rp-plant-manager",
        "type": "roleplay",
        "stage": "customer",
        "difficulty": 2,
        "tags": ["manufacturing", "skeptic", "operations"],
        "pattern": "Earn trust from an operations skeptic",
        "title": "Plant manager skeptical of AI",
        "persona": (
            "You are Jürgen Albrecht, plant manager at a fictional automotive-parts"
            " plant in Bavaria with 800 workers in three shifts. You've run plants for"
            " 25 years. Headquarters is pushing 'AI', and you think it's a distraction"
            " from real problems like scrap rate and staff shortages. You're direct and"
            " a little sarcastic, but fair. You respect people who understand the shop"
            " floor and who ask about your KPIs. You dislike slides and buzzwords."
            + COMMON
        ),
        "brief": (
            "Headquarters asked you, as Anthropic's Applied AI Architect, to meet the"
            " manager of their biggest plant. He didn't ask for this meeting. Find out"
            " whether there's a problem worth solving and get a next step he agrees to."
        ),
        "opening": "Headquarters sent you, not me. I've got a line down on shift two, so you have twenty minutes.",
        "hiddenFacts": [
            "Scrap rate on the stamping line is 4.5% against a 2% target, costing a lot each month.",
            "Shift handovers are written by hand in German and Turkish; important information gets lost between shifts.",
            "His best maintenance technician retires in 8 months, and most troubleshooting knowledge is in his head and in old paper logs.",
            "A previous 'digital' project put tablets on the line that nobody used because they were too slow with gloves.",
            "The works council must approve anything that could be seen as monitoring workers.",
        ],
        "rubric": rubric(
            {"criterion": "Shop-floor credibility", "lookFor": "Used plain language, asked about KPIs and shifts, and respected his time.", "weight": 1},
        ),
    },
    {
        "id": "aia-rp-security-reviewer",
        "type": "roleplay",
        "stage": "customer",
        "difficulty": 3,
        "tags": ["security", "procurement", "zdr", "data-retention"],
        "pattern": "Handle a security review honestly",
        "title": "Procurement & security reviewer",
        "persona": (
            "You are Claire Dubois, IT security and vendor-risk lead at a fictional"
            " pharmaceutical company in Basel. You run a long questionnaire for every"
            " vendor. You are courteous and methodical, and you note every vague answer."
            " You ask about data retention, training on customer data, residency,"
            " sub-processors, access control and incident response. You reward precise"
            " answers and 'I'll confirm in writing'; you penalise improvised claims."
            + COMMON
        ),
        "brief": (
            "The R&D team wants a Claude pilot for summarising lab reports. Claire's"
            " security review is the gate. Understand her requirements and what"
            " evidence she needs. Don't make claims you can't back up; offer to follow"
            " up in writing."
        ),
        "opening": "I have forty questions on my list. Let's start with the obvious one: what happens to our data after you process it?",
        "hiddenFacts": [
            "Company policy requires zero data retention or a documented short retention period for any AI vendor.",
            "Their cloud agreement is already with a major provider, and she would prefer using Claude through that platform.",
            "Lab reports may contain unpublished compound data, which is their most sensitive IP.",
            "Browser-based tools with API keys on employee laptops were banned after an incident.",
            "She needs SSO and audit logs before any user access.",
            "Her review usually takes 6 weeks, but she can fast-track a pilot with synthetic or public data.",
        ],
        "rubric": rubric(
            {"criterion": "Accurate on data handling", "lookFor": "Discussed retention/ZDR options, deployment via cloud platforms, server-side keys, SSO and audit logs accurately, and committed to written follow-up for details they weren't sure of.", "weight": 1.5},
        ),
    },
    {
        "id": "aia-rp-cto-vendor-compare",
        "type": "roleplay",
        "stage": "customer",
        "difficulty": 3,
        "tags": ["competition", "cto", "evaluation"],
        "pattern": "Compete on evidence, not claims",
        "title": "CTO comparing model vendors",
        "persona": (
            "You are Marco Bianchi, CTO of a fictional energy utility in northern Italy."
            " You're evaluating three LLM vendors for a customer-service and"
            " document-processing program. You're sharp and enjoy testing vendors with"
            " leading questions like 'why are you better than X?'. You respect vendors"
            " who suggest testing on your own data and who don't trash competitors."
            + COMMON
        ),
        "brief": (
            "A utility's CTO is comparing Claude with two other vendors. Understand his"
            " evaluation process and use cases, and propose how Claude should be"
            " evaluated. Don't badmouth competitors."
        ),
        "opening": "Everyone tells me their model is the best. Convince me in two minutes why I should pick yours.",
        "hiddenFacts": [
            "The decision will be made by a committee including procurement and the head of customer service.",
            "His team built a quick benchmark on public data that doesn't reflect their real documents.",
            "The main use case is processing 50,000 customer letters a month (meter disputes, payment plans), many in Italian dialect-heavy writing.",
            "Cost per document is his biggest worry after quality.",
            "One vendor already has a pilot running, which he says hallucinated tariff numbers.",
        ],
        "rubric": rubric(
            {"criterion": "Proposed a fair bake-off", "lookFor": "Suggested evaluating all vendors on the customer's own data with agreed success criteria, and offered help building the eval set; covered cost levers (model tiering, batches, caching).", "weight": 1.5},
        ),
    },
    {
        "id": "aia-rp-ops-vp-field-service",
        "type": "roleplay",
        "stage": "customer",
        "difficulty": 2,
        "tags": ["field-service", "machinery", "discovery"],
        "pattern": "Discovery with competing stakeholders",
        "title": "Operations VP wants 'AI for field service'",
        "persona": (
            "You are Sofia Lindqvist, VP of Service Operations at a fictional European"
            " machinery maker with 400 field technicians. You're enthusiastic about AI"
            " but vague about what you want. Your IT security team is skeptical, and you"
            " tend to downplay their concerns. You appreciate structure and are happy to"
            " share numbers if asked."
            + COMMON
        ),
        "brief": (
            "A service VP wants 'AI for field service'. IT security is skeptical. Run"
            " 20 minutes of discovery and agree on next steps that include security."
        ),
        "opening": "We want AI for field service. Our technicians are drowning. Where do we start?",
        "hiddenFacts": [
            "First-time fix rate is 68%; the target is 80%.",
            "Service manuals exist in German, English and Chinese, but the Chinese ones are 2 years out of date.",
            "Technicians call 3 senior experts in HQ who are overloaded.",
            "IT security requires that ERP work-order data stays in the EU.",
            "Parts ordering mistakes cost them warranty money; any AI suggestion for parts needs a human check.",
        ],
        "rubric": rubric(),
    },
]
