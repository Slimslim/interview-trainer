from _helpers import code


def fc(id_, stage, pattern, tags, front, back, example=None, difficulty=1, source=None):
    it = {
        "id": f"fde-fc-{id_}", "type": "flashcard", "stage": stage,
        "difficulty": difficulty, "tags": tags, "pattern": pattern,
        "front": front, "back": back,
    }
    if example:
        it["example"] = example
    if source:
        it["source"] = source
    return it


ALGORITHMS = [
    fc("two-pointers", "coding", "two pointers", ["arrays", "two-pointers"],
       "When do two pointers beat a nested loop?",
       "When the input is sorted (or can be sorted) and you need pairs or ranges: move the "
       "left or right pointer based on a comparison. O(n) after sorting instead of O(n^2). "
       "Also for in-place dedupe/partition with a slow and a fast pointer.",
       code('''
           l, r = 0, len(a) - 1
           while l < r:
               s = a[l] + a[r]
               if s == target: return l, r
               if s < target: l += 1
               else: r -= 1
       ''')),
    fc("hash-complement", "coding", "hashing", ["dict", "hashing"],
       "Two-sum on an unsorted list in O(n)?",
       "One pass with a dict of value -> index. For each x, check whether target - x is "
       "already in the dict before inserting x. Trades O(n) memory for time.",
       code('''
           seen = {}
           for i, x in enumerate(nums):
               if target - x in seen:
                   return seen[target - x], i
               seen[x] = i
       ''')),
    fc("hash-grouping", "coding", "hashing", ["dict", "defaultdict", "grouping"],
       "Group items by a derived key (e.g. anagrams)?",
       "defaultdict(list) keyed by a canonical form: tuple(sorted(word)) or a Counter as a "
       "frozenset. One pass, O(n * k log k) for anagrams.",
       code('''
           groups = defaultdict(list)
           for w in words:
               groups["".join(sorted(w))].append(w)
       ''')),
    fc("top-k", "coding", "heaps / top-k", ["heap", "heapq", "top-k"],
       "Top k largest of n items: which tool and what cost?",
       "heapq.nlargest(k, items, key=...), or a min-heap of size k that pops the smallest "
       "when it overflows: O(n log k). Counter.most_common(k) for frequencies. Sort only if "
       "k is close to n.",
       code('''
           heapq.nlargest(3, scores.items(), key=lambda kv: kv[1])
       ''')),
    fc("merge-k", "coding", "heaps / top-k", ["heap", "merge"],
       "Merge k sorted lists?",
       "Push the head of each list into a min-heap as (value, list_idx, elem_idx); pop the "
       "smallest, push that list's next item. O(N log k). heapq.merge does it lazily."),
    fc("bfs", "coding", "BFS / DFS", ["bfs", "graphs"],
       "When BFS rather than DFS?",
       "BFS (deque, visited set) gives the shortest path in an unweighted graph and explores "
       "level by level: crawl depth limits, fewest hops. DFS (stack or recursion) suits "
       "reachability, cycle detection, and exhaustive search. Both are O(V + E).",
       code('''
           q, seen = deque([(start, 0)]), {start}
           while q:
               node, d = q.popleft()
               for nb in graph[node]:
                   if nb not in seen:
                       seen.add(nb); q.append((nb, d + 1))
       ''')),
    fc("visited-when", "coding", "BFS / DFS", ["bfs", "graphs", "gotcha"],
       "BFS: mark visited when enqueuing or when dequeuing?",
       "When enqueuing. Marking on dequeue lets the same node be queued many times, which "
       "blows up the work and can duplicate crawl requests."),
    fc("sliding-window", "coding", "sliding window", ["sliding-window", "strings"],
       "Longest substring/subarray satisfying a constraint?",
       "Variable sliding window: extend the right edge each step; while the window is "
       "invalid, shrink from the left. Track state in a Counter or set. O(n) because each "
       "index enters and leaves once.",
       code('''
           left = 0
           for right, ch in enumerate(s):
               count[ch] += 1
               while count[ch] > 1:
                   count[s[left]] -= 1; left += 1
               best = max(best, right - left + 1)
       ''')),
    fc("binary-search-answer", "coding", "binary search", ["binary-search", "bisect"],
       "Binary search beyond 'find x in a sorted array'?",
       "Search on the answer: if a predicate ok(x) is monotonic (false...false true...true), "
       "binary search for the first true. Examples: minimum capacity, smallest timestamp "
       "<= t. Use bisect for sorted lists.",
       code('''
           # latest version at or before ts (times sorted)
           i = bisect_right(times, ts) - 1
       ''')),
    fc("toposort", "coding", "topological sort", ["graphs", "toposort"],
       "Order tasks with dependencies (build steps, package installs)?",
       "Kahn's algorithm: count in-degrees, queue nodes with in-degree 0, pop and decrement "
       "neighbours. If you output fewer than V nodes there is a cycle. "
       "graphlib.TopologicalSorter is in the stdlib.",
       code('''
           from graphlib import TopologicalSorter
           list(TopologicalSorter({"b": {"a"}, "c": {"b"}}).static_order())
           # ['a', 'b', 'c']
       ''')),
    fc("union-find", "coding", "union-find", ["graphs", "union-find"],
       "Union-find: what is it for and what makes it fast?",
       "Dynamic connectivity: connected components, merging accounts, cycle check in "
       "Kruskal. A parent array with find (path compression) and union (by size/rank) is "
       "nearly O(1) amortized per operation.",
       code('''
           def find(x):
               while parent[x] != x:
                   parent[x] = parent[parent[x]]
                   x = parent[x]
               return x
       ''')),
    fc("intervals", "coding", "intervals", ["intervals", "sorting"],
       "Merge overlapping intervals?",
       "Sort by start, then walk: if the next start <= the current end, extend the end to "
       "max(end, next_end); otherwise start a new interval. O(n log n). For meeting rooms, "
       "use a min-heap of end times.",
       code('''
           out = []
           for s, e in sorted(iv):
               if out and s <= out[-1][1]:
                   out[-1][1] = max(out[-1][1], e)
               else:
                   out.append([s, e])
       ''')),
    fc("monotonic-stack", "coding", "monotonic stack", ["stack"],
       "'Next greater element' or 'days until warmer' in O(n)?",
       "Monotonic stack of indices: while the current value beats the value at the stack "
       "top, pop and record the answer for that index; then push the current index. Each "
       "index is pushed and popped once.",
       code('''
           st = []
           for i, t in enumerate(temps):
               while st and temps[st[-1]] < t:
                   j = st.pop(); ans[j] = i - j
               st.append(i)
       ''')),
    fc("memo-dp", "coding", "memoization / DP", ["dp", "memoization", "recursion"],
       "How do you get from brute-force recursion to DP?",
       "1) Write the recursion with clear state (the arguments). 2) Notice repeated "
       "subproblems. 3) Add @functools.cache (top-down). 4) If needed, turn it into a "
       "bottom-up table in dependency order. Cost = number of states x work per state.",
       code('''
           @cache
           def ways(n):
               return 1 if n <= 1 else ways(n - 1) + ways(n - 2)
       ''')),
    fc("prefix-sums", "coding", "prefix sums", ["arrays", "hashing"],
       "Count subarrays summing to k (with negatives)?",
       "Running prefix sum plus a Counter of prefix sums seen so far. At each step add "
       "count[prefix - k] to the answer. O(n). A sliding window fails here because "
       "negatives break monotonicity."),
    fc("progressive-design", "coding", "progressive coding", ["oop", "extensibility"],
       "Progressive multi-level problem (KV store, bank): what structure survives level 4?",
       "A small class with dict-based state, one method per operation, and private "
       "helpers. Store values with metadata (value, timestamp, ttl) from the start. Keep "
       "earlier tests as asserts and refactor before adding each level.",
       code('''
           @dataclass
           class Entry:
               value: str
               ts: int
               ttl: int | None = None
       ''')),
]

CACHING_CONCURRENCY = [
    fc("lru", "coding", "LRU cache", ["caching", "lru", "ordereddict"],
       "Implement an LRU cache with O(1) get/put in Python?",
       "OrderedDict: on get, move_to_end(key); on put, set it, move_to_end, and if over "
       "capacity, popitem(last=False). Underneath it's a hash map plus a doubly linked list. "
       "functools.lru_cache does this for function calls.",
       code('''
           def put(self, k, v):
               self.d[k] = v
               self.d.move_to_end(k)
               if len(self.d) > self.cap:
                   self.d.popitem(last=False)
       ''')),
    fc("lru-key", "coding", "LRU cache", ["caching", "lru", "hashing"],
       "Memoizing f(*args, **kwargs): how do you build a correct cache key?",
       "Use args plus kwargs in a canonical order: (args, tuple(sorted(kwargs.items()))). "
       "Every part must be hashable. Watch for f(1, b=2) and f(1, 2) being different keys, "
       "and for mutable arguments."),
    fc("ttl", "coding", "TTL cache", ["caching", "ttl"],
       "Add TTL expiry to a cache?",
       "Store (value, expires_at) using an injected clock (time.monotonic in prod, a fake in "
       "tests). Expire lazily on read; optionally sweep periodically or keep a heap of "
       "expiry times so memory doesn't grow with dead keys.",
       code('''
           def get(self, k):
               v, exp = self.d.get(k, (None, 0))
               if self.now() >= exp:
                   self.d.pop(k, None); return None
               return v
       ''')),
    fc("invalidation", "design", "cache invalidation", ["caching"],
       "Main strategies for cache invalidation?",
       "TTL (simple, bounded staleness); explicit invalidation or delete on write; "
       "versioned keys (bump a version so old entries are never read); event-driven purges "
       "from change data capture. Pick based on how much staleness the business tolerates."),
    fc("write-policies", "design", "write-through vs write-back", ["caching"],
       "Write-through vs write-back vs cache-aside?",
       "Write-through: write cache and DB together; consistent but slower writes. "
       "Write-back: write the cache and flush later; fast but can lose data on a crash. "
       "Cache-aside: the app reads the cache, falls back to the DB and fills the cache; the "
       "most common pattern."),
    fc("threads-async-procs", "coding", "concurrency model", ["concurrency", "asyncio", "threads"],
       "Threads vs asyncio vs processes in Python?",
       "I/O-bound with many connections: asyncio (one thread, cooperative, needs async "
       "libraries). I/O-bound with blocking libraries: a ThreadPoolExecutor. CPU-bound: "
       "ProcessPoolExecutor or multiprocessing to get past the GIL."),
    fc("gil", "coding", "GIL", ["concurrency", "gil"],
       "What does the GIL mean in practice?",
       "In standard CPython only one thread runs Python bytecode at a time, so threads don't "
       "speed up pure-Python CPU work. They still help for I/O, which releases the GIL. The "
       "GIL does not make your compound operations atomic; you still need locks."),
    fc("race", "coding", "race conditions", ["concurrency", "threads", "locks"],
       "Classic race in a multithreaded crawler, and the fix?",
       "Check-then-act on shared state: two threads both see a URL as not visited and both "
       "fetch it. Make check-and-add one critical section under a threading.Lock, or have "
       "one coordinator own the visited set and hand work out through a queue.Queue.",
       code('''
           with lock:
               if url in visited:
                   continue
               visited.add(url)
       ''')),
    fc("asyncio-bound", "coding", "bounded concurrency", ["asyncio", "concurrency"],
       "Fetch 1,000 URLs concurrently without hammering the server?",
       "asyncio.gather plus an asyncio.Semaphore(n) around each fetch, or a fixed pool of "
       "worker tasks reading an asyncio.Queue. Add timeouts and retries with backoff on "
       "429/5xx.",
       code('''
           sem = asyncio.Semaphore(10)
           async def fetch(u):
               async with sem:
                   return await client.get(u)
           results = await asyncio.gather(*(fetch(u) for u in urls))
       ''')),
    fc("idempotency", "design", "idempotency", ["reliability", "retries"],
       "Why do idempotency keys matter for agent tools and retries?",
       "Retries after a timeout can repeat a side effect (double charge, duplicate email). "
       "The client sends a unique key per logical operation; the server stores key -> "
       "result and returns the stored result on repeats. Required before you auto-retry any "
       "write."),
    fc("backoff", "coding", "retry with backoff", ["reliability", "retries", "rate-limits"],
       "Retry policy for 429 / 529 / 5xx from an API?",
       "Exponential backoff with jitter, honor retry-after if present, cap the attempts and "
       "total time, and retry only retryable errors (not 400s). Inject sleep and clock so "
       "tests stay fast.",
       code('''
           delay = min(cap, base * 2 ** attempt) * random.uniform(0.5, 1)
       ''')),
    fc("rate-limiter", "coding", "rate limiting", ["rate-limits", "token-bucket"],
       "Token bucket vs sliding-window rate limiter?",
       "Token bucket: refill r tokens/s up to capacity b, spend one per request; allows "
       "bursts up to b. Sliding window log: keep a deque of timestamps and drop those older "
       "than the window; exact but O(requests) memory. Across many servers, keep shared "
       "state in something like Redis."),
]

EVALS = [
    fc("golden-set", "design", "golden sets", ["evals"],
       "What makes a good golden eval set?",
       "Real or realistic inputs covering the common cases, edge cases, and known past "
       "failures, each with an expected output or grading criteria. Versioned, reviewed by "
       "domain experts, and big enough to show differences (start with 50-200 and grow it "
       "from production failures)."),
    fc("grader-types", "design", "grader choice", ["evals", "llm-as-judge"],
       "Code-graded vs LLM-as-judge vs human grading: when to use each?",
       "Code: exact match, JSON schema, regex, tool-call correctness; cheap and "
       "deterministic, so use it whenever possible. LLM judge: open-ended quality against a "
       "rubric, at scale. Humans: the ground truth used to calibrate the judge, plus "
       "high-stakes or ambiguous cases."),
    fc("judge-calibration", "design", "judge calibration", ["evals", "llm-as-judge"],
       "How do you trust an LLM-as-judge?",
       "Have humans label a sample and measure agreement with the judge. Use a specific "
       "rubric, ask for reasoning before the score, prefer binary or small scales, and check "
       "for position and length bias. Re-check agreement when the judge prompt or model "
       "changes."),
    fc("regression-evals", "design", "regression evals", ["evals", "ci"],
       "A teammate edits the system prompt. How do you avoid shipping a regression?",
       "Treat prompts like code: version them, run the eval suite in CI on every change, and "
       "compare against the baseline per category, not just the overall average. Block the "
       "merge on drops, and add each newly found failure to the set."),
    fc("precision-recall", "design", "precision / recall", ["evals", "metrics"],
       "Precision vs recall, and which matters for an escalation classifier?",
       "Precision = of the items flagged, how many were right. Recall = of the true items, "
       "how many were flagged. For safety or escalation, recall usually matters more "
       "(missing one is costly); for auto-actions, precision matters more."),
    fc("pass-at-k", "design", "pass@k", ["evals", "metrics", "code-generation"],
       "What is pass@k?",
       "The probability that at least one of k sampled attempts passes the tests. pass@1 "
       "reflects single-shot reliability; pass@k with k > 1 shows potential when you can "
       "verify and retry. Report the k and the sampling settings."),
    fc("edd", "design", "eval-driven development", ["evals", "process"],
       "What is eval-driven development for an LLM feature?",
       "Define success criteria and build a small eval before writing prompts. Iterate on "
       "prompt, retrieval, and tools against it, and ship only when the metrics clear the "
       "bar. In production, keep feeding real failures back into the set."),
    fc("agent-evals", "design", "agent evals", ["evals", "agents"],
       "What do you evaluate in an agent beyond the final answer?",
       "Task success, tool selection and argument correctness, number of steps and cost, "
       "latency, whether it asked for approval when required, and safety violations. "
       "Grade traces as well as outcomes, and run several trials per task because agents "
       "are non-deterministic."),
]

RAG = [
    fc("chunking", "design", "chunking", ["rag"],
       "How should you chunk documents for RAG?",
       "Split on document structure (headings, sections) rather than fixed character counts. "
       "Aim for a few hundred tokens with some overlap, and keep metadata (source, section, "
       "date, permissions) on each chunk. Tune chunk size with retrieval evals."),
    fc("embeddings", "design", "embeddings", ["rag", "embeddings"],
       "What do embeddings give you and what do they miss?",
       "Semantic similarity: paraphrases match without shared words. They miss exact tokens "
       "(part numbers, error codes, names) and can't filter by permission or date on their "
       "own. Use the same model for queries and documents and re-embed when you change it."),
    fc("hybrid", "design", "hybrid search", ["rag", "bm25"],
       "Why use hybrid search (BM25 + vectors)?",
       "BM25 catches exact keywords and identifiers; vectors catch meaning. Run both and "
       "fuse the results (e.g. reciprocal rank fusion). This usually beats either alone on "
       "enterprise data full of SKUs and jargon."),
    fc("rerank", "design", "reranking", ["rag", "reranking"],
       "What does a reranker add?",
       "Retrieve broadly (e.g. top 50-100), then score each query-chunk pair with a "
       "cross-encoder or LLM and keep the top few. Higher precision in the context window "
       "at the cost of extra latency."),
    fc("contextual-retrieval", "design", "contextual retrieval", ["rag"],
       "What is contextual retrieval?",
       "Before indexing, prepend a short, LLM-generated description of where each chunk sits "
       "in its document (e.g. 'From the 2024 Q2 report, revenue section') to both the "
       "embedding text and the BM25 index. This fixes chunks that are ambiguous out of "
       "context. Prompt caching keeps it cheap."),
    fc("citations", "design", "citations", ["rag", "trust"],
       "Why require citations in RAG answers?",
       "Users can verify claims, evals can check that answers are grounded, and "
       "unsupported statements become visible. Instruct the model to answer only from the "
       "provided sources and to say when they don't contain the answer."),
    fc("freshness", "design", "freshness", ["rag", "ingestion"],
       "How do you keep a RAG index fresh?",
       "Incremental ingestion triggered by change events or a schedule, deletes propagated "
       "(tombstones), a last-modified date on chunks, and recency boosting where it "
       "matters. Monitor index lag as an SLO."),
    fc("rbac", "design", "RBAC filtering", ["rag", "security", "rbac"],
       "How do you stop RAG from leaking documents a user can't see?",
       "Store ACLs or groups as chunk metadata and filter at query time by the caller's "
       "identity, before ranking and before anything reaches the model. Never rely on the "
       "prompt to hide content. Sync permission changes and test with users from different "
       "roles."),
]

MCP = [
    fc("mcp-what", "design", "MCP basics", ["mcp"],
       "What is MCP in one line?",
       "Model Context Protocol: an open protocol for connecting AI applications (clients) "
       "to external tools and data (servers) through one standard interface, so each "
       "integration is built once and reused across hosts."),
    fc("mcp-primitives", "design", "MCP primitives", ["mcp"],
       "MCP server primitives: tools vs resources vs prompts?",
       "Tools: functions the model can call (model-controlled, may have side effects). "
       "Resources: data the application can read and attach as context "
       "(application-controlled). Prompts: reusable templates the user picks "
       "(user-controlled)."),
    fc("mcp-transports", "design", "MCP transports", ["mcp"],
       "MCP transports: stdio vs Streamable HTTP?",
       "stdio: the client launches the server as a local subprocess; simple, for local "
       "tools. Streamable HTTP: a remote server over HTTP, optionally streaming via SSE; "
       "used for shared or hosted servers and needs proper auth (OAuth)."),
    fc("mcp-trust", "design", "MCP trust boundaries", ["mcp", "security"],
       "Where are the trust boundaries in an MCP deployment?",
       "Between the user and the model, between the model and each server, and between the "
       "server and the backend systems. Tool outputs and fetched content are untrusted "
       "input. The server enforces authorization; the model's choice to call a tool is not "
       "permission."),
    fc("mcp-least-priv", "design", "least privilege", ["mcp", "security"],
       "Designing an MCP tool surface with least privilege?",
       "Small, task-shaped tools ('create_refund_request', not 'run_sql'), scoped "
       "credentials per user, read-only by default, separate write tools that require "
       "approval, input validation and limits on the server, and every call logged."),
    fc("mcp-auth", "design", "MCP auth", ["mcp", "auth"],
       "How should a remote MCP server authenticate users?",
       "OAuth: the server acts on behalf of the signed-in user with scoped tokens, so "
       "backend permissions match that user. Avoid one shared admin key and don't pass "
       "tokens through to unrelated services."),
]

CLAUDE_API = [
    fc("tool-loop", "design", "tool use loop", ["claude-api", "tool-use"],
       "Shape of the tool use loop?",
       "Send messages and tool definitions. If stop_reason is tool_use, run each tool_use "
       "block, append the assistant message, then a user message of tool_result blocks with "
       "matching tool_use_id. Repeat until end_turn. Cap iterations and handle tool errors "
       "with is_error.",
       code('''
           while resp.stop_reason == "tool_use":
               results = [run(b) for b in resp.content if b.type == "tool_use"]
               messages += [{"role": "assistant", "content": resp.content},
                            {"role": "user", "content": results}]
               resp = client.messages.create(model=M, tools=T, messages=messages,
                                             max_tokens=1024)
       ''')),
    fc("stop-reasons", "design", "stop reasons", ["claude-api"],
       "Main stop_reason values?",
       "end_turn: finished naturally. max_tokens: hit your limit, output truncated. "
       "stop_sequence: matched one of your stop sequences. tool_use: wants a tool call. "
       "Handle each explicitly; don't treat max_tokens as a complete answer."),
    fc("caching-api", "design", "prompt caching", ["claude-api", "caching", "cost"],
       "Prompt caching: how do you use it well?",
       "Mark the end of a stable prefix (tools, system prompt, long documents) with "
       "cache_control. Later requests with an identical prefix read it at a fraction of the "
       "input price and with lower latency. Keep variable content after the breakpoint and "
       "watch the cache read/write usage fields."),
    fc("batches-api", "design", "batch vs real-time", ["claude-api", "batches", "cost"],
       "Message Batches API: trade-off?",
       "About 50% cheaper than standard calls and asynchronous: you submit many requests and "
       "collect results later (within 24 hours). Good for evals, backfills and nightly "
       "classification; wrong for interactive or step-dependent agent work."),
    fc("streaming", "design", "streaming", ["claude-api", "streaming"],
       "Why stream responses?",
       "Users see tokens immediately (better perceived latency), and long generations avoid "
       "HTTP timeouts. You handle server-sent events and assemble the content blocks, "
       "including tool_use input that arrives as partial JSON."),
    fc("thinking", "design", "extended thinking", ["claude-api", "reasoning"],
       "When to turn on extended thinking?",
       "For multi-step reasoning, complex coding, analysis and planning, where quality "
       "matters more than latency and cost. You set a token budget for thinking. Skip it "
       "for simple extraction or classification. Measure the gain with evals."),
    fc("tiering", "design", "model tiering", ["claude-api", "cost", "architecture"],
       "What is model tiering?",
       "Route each step to the smallest model that passes its evals: a fast, cheap model for "
       "classification, routing and extraction; a frontier model for hard reasoning and "
       "agent planning. Escalate on low confidence. Re-run evals when you swap models."),
    fc("structured-output", "design", "structured output", ["claude-api", "tool-use", "json"],
       "Reliable JSON out of Claude?",
       "Define a tool with a JSON schema and force it with tool_choice, or use structured "
       "outputs where available. Always validate with a schema (e.g. Pydantic) on your side "
       "and retry or repair on failure."),
]

GUARDRAILS = [
    fc("prompt-injection", "design", "prompt injection", ["security", "guardrails"],
       "Defenses against indirect prompt injection (malicious text in docs, emails, web "
       "pages)?",
       "Treat retrieved content as data: mark it clearly in the prompt, give the agent "
       "least-privilege tools, require human approval for sensitive actions, restrict where "
       "data can be sent (no arbitrary URLs), screen inputs with classifiers, and red-team "
       "with injected documents. No single layer is enough."),
    fc("classifiers", "design", "input/output classifiers", ["guardrails"],
       "Input vs output classifiers in a deployment?",
       "Input: screen requests for policy violations, jailbreaks, or off-scope topics "
       "before the main model. Output: check responses for PII, policy breaches, or "
       "ungrounded claims before showing or acting. A small fast model or rules work; tune "
       "thresholds on labelled data."),
    fc("hitl", "design", "human-in-the-loop", ["guardrails", "approvals"],
       "Which agent actions need human approval?",
       "Irreversible or high-impact ones: sending external messages, payments, deletes, "
       "production changes, anything legal or financial. Show the human the exact action "
       "and arguments, record who approved, and expire stale approvals."),
    fc("audit-logs", "design", "audit logging", ["guardrails", "observability"],
       "What goes in an agent audit log?",
       "Who asked, what the model saw (prompt and versions), each tool call with arguments "
       "and results, approvals and approver, final output, timestamps, model and cost. "
       "Make it append-only and redact secrets and PII per policy."),
    fc("pii", "design", "PII redaction", ["guardrails", "privacy"],
       "How do you handle PII in an LLM pipeline?",
       "Minimize first (don't send fields the task doesn't need). Detect and redact or "
       "tokenize PII before logging, and restore it after if needed. Respect retention and "
       "residency rules, and keep PII out of eval sets unless approved."),
]

VALUES = [
    fc("rsp-what", "values", "RSP", ["anthropic", "rsp"],
       "What is the Responsible Scaling Policy (RSP), and its current version?",
       "Anthropic's framework tying safeguards to model capability thresholds. Version 3.4 "
       "took effect 2026-07-08; v3.0 (2026-02-24) was a comprehensive rewrite. v3.x adds "
       "Frontier Safety Roadmaps and Risk Reports that quantify risk across deployed "
       "models.",
       source="S4"),
    fc("asl", "values", "ASL levels", ["anthropic", "rsp", "asl"],
       "ASL levels: what is ASL-2 vs the ASL-3 Deployment Standard?",
       "ASL-2 is the baseline. The ASL-3 Deployment Standard is four-layer defense in depth "
       "focused on CBRN misuse: access controls, real-time prompt/completion classifiers, "
       "asynchronous monitoring, and jailbreak detection with rapid response.",
       source="S4", difficulty=2),
    fc("asl3-security", "values", "ASL levels", ["anthropic", "rsp", "security"],
       "What does the ASL-3 Security Standard include?",
       "Protections for model weights: multi-party authorization for weight access, binary "
       "authorization, supply-chain security, honeypots, and red teaming.",
       source="S4", difficulty=2),
    fc("rsp-thresholds", "values", "RSP", ["anthropic", "rsp"],
       "Which capability thresholds does the RSP track?",
       "CBRN weapons risk and AI R&D (including automating entry-level AI research and "
       "dramatically accelerating effective scaling). Anthropic determined Claude Opus 4.6 "
       "does not cross AI R&D-4.",
       source="S4", difficulty=2),
    fc("core-views", "values", "Core Views", ["anthropic", "safety"],
       "Core Views on AI Safety (2023): the three scenarios?",
       "Optimistic: existing methods like RLHF and Constitutional AI mostly suffice. "
       "Intermediate: solvable with substantial work. Pessimistic: safety can't be solved, "
       "so sound the alarm and don't build. Anthropic says frontier safety research is "
       "needed because some risks only appear at the frontier.",
       source="S6"),
    fc("core-views-empirical", "values", "Core Views", ["anthropic", "safety"],
       "Core Views: the research portfolio and approach?",
       "Three areas: capabilities (largely unpublished), alignment capabilities (RLHF, "
       "Constitutional AI), and alignment science (interpretability, red-teaming). An "
       "empirical approach: 'show, don't tell'.",
       source="S6"),
    fc("values-list", "values", "Anthropic values", ["anthropic", "values"],
       "Anthropic's stated company values?",
       "Act for the global good. Hold light and shade. Be good to our users. Ignite a race "
       "to the top on safety. Do the simple thing that works. Be helpful, honest, and "
       "harmless. Put the mission first.",
       source="S3"),
    fc("ai-guidance", "values", "candidate AI guidance", ["anthropic", "hiring"],
       "Anthropic's guidance on candidates using Claude in hiring?",
       "Applications: write your own first draft, then refine with Claude. Take-homes: "
       "without Claude unless told otherwise. Prep: encouraged. Live interviews: no AI "
       "unless indicated. Never use it to invent experience.",
       source="S1"),
    fc("perform-alignment", "values", "values answers", ["values", "behavioral"],
       "What reportedly sinks values-round answers?",
       "Performing alignment: generic safety enthusiasm without substance. What works: "
       "specific views on things you've read (e.g. the RSP), calibrated uncertainty, saying "
       "'I don't know', and willingness to disagree, even with Anthropic.",
       source="S28 S29 S30"),
    fc("star", "values", "STAR", ["behavioral", "star"],
       "STAR structure, and what Anthropic-style interviewers add?",
       "Situation (one or two lines), Task (your responsibility), Action (what you did, "
       "with 'I' not 'we'), Result (a metric). Add an honest reflection: what you'd do "
       "differently. Keep it to about 2 minutes and expect follow-ups."),
]

CUSTOMER = [
    fc("discovery-order", "customer", "discovery structure", ["discovery", "customer"],
       "Discovery call order when an exec says 'put Claude on our knowledge base'?",
       "Agenda, then business goal and success metric, current workflow and systems, data "
       "location and owners, constraints (privacy, residency, security review, budget, "
       "timeline), past attempts and why they failed, stakeholders. Play it back, then "
       "propose a narrow pilot with an eval set."),
    fc("resist-design", "customer", "discovery structure", ["discovery", "customer"],
       "Why not start sketching the architecture in a discovery call?",
       "You don't yet know the goal, data, or constraints, so you'll design the wrong thing "
       "and anchor the customer on it. Ask first, then play back what you heard; design "
       "once they confirm the problem statement."),
    fc("success-metric", "customer", "success metrics", ["discovery", "evals"],
       "Turning 'we want AI for support' into a measurable pilot goal?",
       "Ask what changes if it works: e.g. deflect 30% of tier-1 tickets at equal or better "
       "CSAT, or cut handle time from 12 to 8 minutes. Agree on the baseline, the eval "
       "set, and who signs off, before building."),
    fc("skeptic", "customer", "handling skeptics", ["customer", "objections"],
       "A skeptical architect says 'LLMs hallucinate, this can't go near our data.' "
       "Response?",
       "Acknowledge it as a real risk, then get specific: which failures matter most? Offer "
       "controls: grounding with citations, abstaining when unsure, human review, data "
       "boundaries, and an eval they help design. Propose a low-risk, read-only pilot."),
    fc("past-failures", "customer", "past attempts", ["discovery", "customer"],
       "Why ask about past AI attempts?",
       "It shows hidden constraints (data quality, security blockers, politics), what "
       "stakeholders now fear, and what success must look like this time. It also stops you "
       "proposing the thing that already failed."),
    fc("pushback", "customer", "pushing back", ["customer", "scoping"],
       "Customer wants a fully autonomous agent sending emails to suppliers in week one. "
       "What do you do?",
       "Push back with reasons, in their terms (risk of a wrong supplier email, cost of a "
       "mistake). Offer a path: drafts with human approval first, measure the error rate, "
       "then widen autonomy for low-risk cases once evals and audit logs show it's safe."),
]

ITEMS = (ALGORITHMS + CACHING_CONCURRENCY + EVALS + RAG + MCP + CLAUDE_API
         + GUARDRAILS + VALUES + CUSTOMER)
