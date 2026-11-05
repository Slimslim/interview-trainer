"""Parsons (put-the-lines-in-order) items for the Anthropic FDE pack (stage: coding)."""
from _helpers import code, lines


def _par(id, title, difficulty, pattern, tags, prompt, src, tests, lesson):
    ls = lines(src)
    assert 5 <= len(ls) <= 10, f"{id}: {len(ls)} lines"
    assert len(set(ls)) == len(ls), f"{id}: duplicate lines"
    return {
        "id": id, "type": "parsons", "stage": "coding", "difficulty": difficulty,
        "tags": tags, "pattern": pattern, "title": title, "prompt": prompt,
        "lines": ls, "tests": code(tests), "lesson": lesson,
    }


ITEMS = [
    _par(
        "fde-par-bfs-grid", "Shortest path on a grid (BFS)", 2, "BFS",
        ["graphs", "bfs", "grid"],
        "Order the lines so `shortest(grid, start, goal)` returns the number of steps between two "
        "cells of a grid of `'.'` (open) and `'#'` (wall), or -1 if unreachable.",
        '''
        from collections import deque
        def shortest(grid, start, goal):
            q, seen = deque([(start, 0)]), {start}
            while q:
                (r, c), d = q.popleft()
                if (r, c) == goal: return d
                for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                    if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] == "." and (nr, nc) not in seen:
                        seen.add((nr, nc)); q.append(((nr, nc), d + 1))
            return -1
        ''',
        '''
        G = ["..#",
             ".##",
             "..."]

        def test_path():
            assert shortest(G, (0, 0), (2, 2)) == 4

        def test_same_cell():
            assert shortest(G, (0, 0), (0, 0)) == 0

        def test_blocked():
            assert shortest([".#", "#."], (0, 0), (1, 1)) == -1
        ''',
        "BFS explores in distance order, so the first time you pop the goal you have the shortest "
        "path. Mark cells as seen when you enqueue them (not when you pop) so no cell is queued twice.",
    ),
    _par(
        "fde-par-lru-get", "LRU cache with OrderedDict", 2, "LRU cache",
        ["design", "ordereddict", "cache"],
        "Order the lines to build an LRU cache: `get` returns -1 on a miss and refreshes recency on a "
        "hit; `put` evicts the least recently used key when over capacity.",
        '''
        from collections import OrderedDict
        class LRU:
            def __init__(self, cap): self.cap, self.d = cap, OrderedDict()
            def get(self, k):
                if k not in self.d: return -1
                self.d.move_to_end(k)
                return self.d[k]
            def put(self, k, v):
                self.d[k] = v; self.d.move_to_end(k)
                if len(self.d) > self.cap: self.d.popitem(last=False)
        ''',
        '''
        def test_miss():
            assert LRU(2).get("x") == -1

        def test_get_refreshes():
            c = LRU(2); c.put("a", 1); c.put("b", 2)
            assert c.get("a") == 1
            c.put("c", 3)
            assert c.get("b") == -1, "b was least recently used"
            assert c.get("a") == 1 and c.get("c") == 3

        def test_update_existing():
            c = LRU(1); c.put("a", 1); c.put("a", 5)
            assert c.get("a") == 5
        ''',
        "Check the miss before touching the dict, then move_to_end on a hit so recency is updated "
        "before you return. popitem(last=False) removes the oldest entry.",
    ),
    _par(
        "fde-par-token-bucket", "Token bucket refill", 2, "rate limiter",
        ["rate-limit", "design", "time"],
        "Order the lines so `allow()` refills tokens based on elapsed time (capped at capacity) and "
        "then spends one if available. The clock is injected.",
        '''
        class TokenBucket:
            def __init__(self, rate, capacity, clock):
                self.rate, self.cap, self.clock, self.tokens, self.last = rate, capacity, clock, capacity, clock()
            def allow(self):
                now = self.clock()
                self.tokens = min(self.cap, self.tokens + (now - self.last) * self.rate)
                self.last = now
                if self.tokens >= 1:
                    self.tokens -= 1; return True
                return False
        ''',
        '''
        class Clock:
            t = 0.0
            def __call__(self):
                return self.t

        def test_burst_then_block():
            clk = Clock(); b = TokenBucket(1, 2, clk)
            assert [b.allow(), b.allow(), b.allow()] == [True, True, False]

        def test_refill():
            clk = Clock(); b = TokenBucket(2, 2, clk)
            b.allow(); b.allow()
            clk.t = 0.5
            assert b.allow() is True, "0.5 s at 2 tokens/s refills one token"
            assert b.allow() is False

        def test_cap():
            clk = Clock(); b = TokenBucket(1, 2, clk)
            clk.t = 100
            assert sum(b.allow() for _ in range(5)) == 2, "refill is capped at capacity"
        ''',
        "Refill first (using time since the last refill, capped at capacity), update `last`, and only "
        "then decide. Updating `last` before computing elapsed time would refill nothing.",
    ),
    _par(
        "fde-par-tool-loop", "Agent tool-use loop", 3, "tool-use loop",
        ["llm", "tool-use", "agents"],
        "Order the lines so `run(client, messages, tools)` keeps calling the model, runs each requested "
        "tool, sends the results back in a user turn, and returns the final text.",
        '''
        def run(client, messages, tools):
            while True:
                resp = client.create(messages=messages)
                messages.append({"role": "assistant", "content": resp["content"]})
                if resp["stop_reason"] != "tool_use":
                    return resp["content"][-1]["text"]
                calls = [b for b in resp["content"] if b["type"] == "tool_use"]
                results = [{"type": "tool_result", "tool_use_id": b["id"], "content": tools[b["name"]](**b["input"])} for b in calls]
                messages.append({"role": "user", "content": results})
        ''',
        '''
        class Fake:
            def __init__(self):
                self.n = 0
            def create(self, messages):
                self.n += 1
                assert self.n < 5, "runaway loop"
                assert messages[-1]["role"] == "user"
                if self.n == 1:
                    return {"stop_reason": "tool_use", "content": [
                        {"type": "tool_use", "id": "t1", "name": "add", "input": {"a": 2, "b": 3}}]}
                res = messages[-1]["content"][0]
                assert res["tool_use_id"] == "t1"
                return {"stop_reason": "end_turn", "content": [{"type": "text", "text": f"= {res['content']}"}]}

        def test_loop():
            msgs = [{"role": "user", "content": "2+3?"}]
            assert run(Fake(), msgs, {"add": lambda a, b: a + b}) == "= 5"
            assert [m["role"] for m in msgs] == ["user", "assistant", "user", "assistant"]
        ''',
        "Append the assistant turn before checking stop_reason so the history is complete; only a "
        "\"tool_use\" stop continues the loop, and the tool results must go in the next user turn, "
        "each tagged with its tool_use_id.",
    ),
    _par(
        "fde-par-retry-backoff", "Retry with exponential backoff", 2, "retry/backoff",
        ["llm", "retry", "errors"],
        "Order the lines so `retry(fn, sleep)` retries transient errors with delays 1, 2, 4, ... and "
        "re-raises after the last attempt. `sleep` is injected.",
        '''
        class Transient(Exception):
            pass
        def retry(fn, sleep, attempts=4, base=1):
            for i in range(attempts):
                try:
                    return fn()
                except Transient:
                    if i == attempts - 1:
                        raise
                    sleep(base * 2 ** i)
        ''',
        '''
        def make(fails):
            n = []
            def fn():
                n.append(1)
                if len(n) <= fails:
                    raise Transient()
                return "ok"
            return fn

        def test_succeeds_after_retries():
            waits = []
            assert retry(make(3), waits.append) == "ok"
            assert waits == [1, 2, 4]

        def test_gives_up():
            waits = []
            try:
                retry(make(10), waits.append)
                assert False, "should re-raise"
            except Transient:
                pass
            assert waits == [1, 2, 4], "no sleep after the final failure"

        def test_no_error_no_sleep():
            waits = []
            assert retry(make(0), waits.append) == "ok" and waits == []
        ''',
        "`return fn()` sits inside try so success exits immediately; the last-attempt check comes "
        "before sleeping so you re-raise without a pointless final wait. Injecting `sleep` keeps tests "
        "instant.",
    ),
    _par(
        "fde-par-binary-search", "Binary search (leftmost index)", 2, "binary search",
        ["search", "arrays"],
        "Order the lines so `lower_bound(xs, t)` returns the first index i with xs[i] >= t in a sorted list.",
        '''
        def lower_bound(xs, t):
            lo, hi = 0, len(xs)
            while lo < hi:
                mid = (lo + hi) // 2
                if xs[mid] < t:
                    lo = mid + 1
                else:
                    hi = mid
            return lo
        ''',
        '''
        import bisect

        def test_matches_bisect():
            xs = [1, 3, 3, 5, 8]
            for t in range(0, 10):
                assert lower_bound(xs, t) == bisect.bisect_left(xs, t), f"t={t}"

        def test_empty():
            assert lower_bound([], 4) == 0
        ''',
        "Use a half-open range [lo, hi) with `while lo < hi`; move lo past mid when xs[mid] is too "
        "small, otherwise keep mid as a candidate (hi = mid). This always terminates and returns the "
        "insertion point.",
    ),
    _par(
        "fde-par-sliding-window", "Longest substring without repeats", 2, "sliding window",
        ["strings", "sliding-window", "two-pointer"],
        "Order the lines so `longest_unique(s)` returns the length of the longest substring with no "
        "repeated characters.",
        '''
        def longest_unique(s):
            last, left, best = {}, 0, 0
            for right, ch in enumerate(s):
                if ch in last and last[ch] >= left:
                    left = last[ch] + 1
                last[ch] = right
                best = max(best, right - left + 1)
            return best
        ''',
        '''
        def test_examples():
            assert longest_unique("abcabcbb") == 3
            assert longest_unique("bbbbb") == 1
            assert longest_unique("pwwkew") == 3

        def test_stale_index():
            assert longest_unique("abba") == 2, "ignore last-seen positions left of the window"

        def test_empty():
            assert longest_unique("") == 0
        ''',
        "Shrink the window (move left past the previous occurrence) before recording the new position "
        "and measuring; otherwise the window still contains the duplicate.",
    ),
    _par(
        "fde-par-merge-intervals", "Merge overlapping intervals", 2, "intervals",
        ["sorting", "intervals"],
        "Order the lines so `merge(intervals)` merges overlapping [start, end] pairs.",
        '''
        def merge(intervals):
            out = []
            for s, e in sorted(intervals):
                if out and s <= out[-1][1]:
                    out[-1][1] = max(out[-1][1], e)
                else:
                    out.append([s, e])
            return out
        ''',
        '''
        def test_merge():
            assert merge([[8, 10], [1, 3], [2, 6], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]

        def test_touching_and_contained():
            assert merge([[1, 4], [4, 5]]) == [[1, 5]]
            assert merge([[1, 10], [2, 3]]) == [[1, 10]]

        def test_empty():
            assert merge([]) == []
        ''',
        "Sort by start first; then each interval either extends the last merged one (take the max end, "
        "since it may be contained) or starts a new one.",
    ),
    _par(
        "fde-par-topo-sort", "Topological sort (Kahn's algorithm)", 3, "topological sort",
        ["graphs", "dag", "dependencies"],
        "Order the lines so `topo(deps)` returns an order where every task comes after its "
        "dependencies; `deps` maps task -> list of tasks it depends on. Raise ValueError on a cycle.",
        '''
        def topo(deps):
            indeg = {t: len(d) for t, d in deps.items()}
            ready, order = [t for t, n in indeg.items() if n == 0], []
            while ready:
                t = ready.pop(); order.append(t)
                for u in [u for u, d in deps.items() if t in d]:
                    indeg[u] -= 1
                    if indeg[u] == 0: ready.append(u)
            if len(order) < len(deps): raise ValueError("cycle")
            return order
        ''',
        '''
        def _ok(deps, order):
            pos = {t: i for i, t in enumerate(order)}
            return set(order) == set(deps) and all(pos[d] < pos[t] for t, ds in deps.items() for d in ds)

        def test_order():
            deps = {"deploy": ["test", "build"], "test": ["build"], "build": [], "lint": []}
            assert _ok(deps, topo(deps))

        def test_cycle():
            try:
                topo({"a": ["b"], "b": ["a"]})
                assert False, "cycle should raise"
            except ValueError:
                pass
        ''',
        "Start from tasks with no unmet dependencies; when one finishes, decrement its dependents and "
        "release those that hit zero. If some tasks never reach zero, there is a cycle.",
    ),
    _par(
        "fde-par-safe-json", "Safe JSON parse of model output", 2, "parse model JSON",
        ["llm", "json", "validation"],
        "Order the lines so `parse(text, required)` strips a ```json fence, parses, validates that the "
        "result is an object with the required keys, and returns None on any failure.",
        '''
        import json
        def parse(text, required=()):
            t = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
            try:
                data = json.loads(t)
            except json.JSONDecodeError:
                return None  # not JSON at all
            if not isinstance(data, dict) or any(k not in data for k in required):
                return None  # wrong shape
            return data
        ''',
        '''
        def test_fenced():
            assert parse('```json\\n{"a": 1}\\n```', ["a"]) == {"a": 1}

        def test_invalid():
            assert parse("Sure! {a: 1}") is None

        def test_missing_key():
            assert parse('{"a": 1}', ["a", "b"]) is None

        def test_not_object():
            assert parse("[1, 2]") is None
        ''',
        "Clean the text before parsing, keep only json.loads inside the try (so you don't hide other "
        "bugs), and validate shape after parsing: valid JSON is not the same as the JSON you asked for.",
    ),
    _par(
        "fde-par-stream-assembly", "Assemble a streamed response", 3, "streaming",
        ["llm", "streaming", "events"],
        "Order the lines so `assemble(events)` rebuilds the text of each content block from streaming "
        "events (`content_block_start`, `content_block_delta`, `message_delta`) and returns "
        "`(texts, stop_reason)`.",
        '''
        def assemble(events):
            blocks, stop = {}, None
            for ev in events:
                if ev["type"] == "content_block_start":
                    blocks[ev["index"]] = ""
                elif ev["type"] == "content_block_delta":
                    blocks[ev["index"]] += ev["delta"]["text"]
                elif ev["type"] == "message_delta":
                    stop = ev["delta"]["stop_reason"]
            return [blocks[i] for i in sorted(blocks)], stop
        ''',
        '''
        EVENTS = [
            {"type": "message_start"},
            {"type": "content_block_start", "index": 0},
            {"type": "content_block_delta", "index": 0, "delta": {"text": "Hel"}},
            {"type": "content_block_start", "index": 1},
            {"type": "content_block_delta", "index": 1, "delta": {"text": "B"}},
            {"type": "content_block_delta", "index": 0, "delta": {"text": "lo"}},
            {"type": "content_block_stop", "index": 0},
            {"type": "message_delta", "delta": {"stop_reason": "end_turn"}},
            {"type": "message_stop"},
        ]

        def test_assemble():
            assert assemble(EVENTS) == (["Hello", "B"], "end_turn")

        def test_empty_stream():
            assert assemble([]) == ([], None)
        ''',
        "Key deltas by block index (blocks can interleave), create the block on content_block_start "
        "before appending deltas, and read stop_reason from message_delta, which arrives at the end.",
    ),
    _par(
        "fde-par-counter-topk", "Top-k most common words", 1, "Counter",
        ["collections", "counter", "strings"],
        "Order the lines so `top_words(text, k)` returns the k most common lower-cased words as "
        "(word, count) pairs.",
        '''
        from collections import Counter
        import re
        def top_words(text, k):
            words = re.findall(r"[a-z']+", text.lower())
            counts = Counter(words)
            return counts.most_common(k)
        ''',
        '''
        def test_top():
            assert top_words("the cat and The hat and THE bat", 2) == [("the", 3), ("and", 2)]

        def test_k_larger():
            assert top_words("a a b", 5) == [("a", 2), ("b", 1)]

        def test_empty():
            assert top_words("", 3) == []
        ''',
        "Normalise (lower-case, tokenise) before counting, otherwise 'The' and 'the' are different "
        "keys. Counter.most_common(k) does the sort for you (ties keep first-seen order).",
    ),
    _par(
        "fde-par-dataclass-factory", "Dataclass with default_factory", 1, "dataclass",
        ["dataclasses", "defaults"],
        "Order the lines to define a `Conversation` dataclass whose `messages` list is fresh per "
        "instance, with an `add(role, text)` method that returns self for chaining.",
        '''
        from dataclasses import dataclass, field
        @dataclass
        class Conversation:
            model: str = "claude"
            messages: list = field(default_factory=list)
            def add(self, role, text):
                self.messages.append({"role": role, "content": text})
                return self
        ''',
        '''
        def test_independent_lists():
            a, b = Conversation(), Conversation()
            a.add("user", "hi")
            assert b.messages == [], "each instance needs its own list"

        def test_chain():
            c = Conversation(model="x").add("user", "a").add("assistant", "b")
            assert [m["role"] for m in c.messages] == ["user", "assistant"] and c.model == "x"
        ''',
        "@dataclass must sit directly above the class, and mutable defaults need "
        "field(default_factory=list); a bare `= []` is rejected because it would be shared by every "
        "instance.",
    ),
    _par(
        "fde-par-async-gather", "Bounded concurrent requests", 3, "async gather",
        ["asyncio", "concurrency", "llm"],
        "Order the lines so `fetch_all(fetch, items, limit)` runs `fetch` concurrently, never more than "
        "`limit` at once, and returns results in input order.",
        '''
        import asyncio
        async def fetch_all(fetch, items, limit):
            sem = asyncio.Semaphore(limit)
            async def one(x):
                async with sem:
                    return await fetch(x)
            return await asyncio.gather(*(one(x) for x in items))
        ''',
        '''
        import asyncio

        async def test_order_and_limit():
            live, peak = 0, 0
            async def fetch(x):
                nonlocal live, peak
                live += 1; peak = max(peak, live)
                await asyncio.sleep(0.001 * (5 - x))
                live -= 1
                return x * 10
            out = await fetch_all(fetch, [1, 2, 3, 4], 2)
            assert out == [10, 20, 30, 40], "gather keeps input order"
            assert peak <= 2, f"peak concurrency {peak} > limit"
            assert peak == 2, "should actually run in parallel"
        ''',
        "Create the semaphore once, outside the per-item coroutine, so all tasks share it; acquire it "
        "around the awaited call; then gather (and await) all coroutines, which preserves input order.",
    ),
    _par(
        "fde-par-context-manager", "Timing context manager", 2, "context manager",
        ["contextlib", "generators", "observability"],
        "Order the lines so `timed(name, log, clock)` records `(name, elapsed)` in `log` when the block "
        "exits, even if it raised.",
        '''
        from contextlib import contextmanager
        @contextmanager
        def timed(name, log, clock):
            start = clock()
            try:
                yield
            finally:
                log.append((name, clock() - start))
        ''',
        '''
        def ticker():
            t = iter(range(0, 100, 5))
            return lambda: next(t)

        def test_logs():
            log = []
            with timed("call", log, ticker()):
                pass
            assert log == [("call", 5)]

        def test_logs_on_error():
            log = []
            try:
                with timed("bad", log, ticker()):
                    raise RuntimeError("boom")
            except RuntimeError:
                pass
            assert log == [("bad", 5)], "finally must run even when the block raises"
        ''',
        "Read the start time before yielding; the `yield` is where the with-block runs, and putting "
        "it in try/finally guarantees the exit code runs on exceptions too.",
    ),
    _par(
        "fde-par-two-pointer", "Pair with target sum (two pointers)", 1, "two-pointer",
        ["arrays", "two-pointer", "sorting"],
        "Order the lines so `pair_sum(xs, target)` returns a pair of values from the sorted list `xs` "
        "that add up to `target`, or None.",
        '''
        def pair_sum(xs, target):
            i, j = 0, len(xs) - 1
            while i < j:
                s = xs[i] + xs[j]
                if s == target:
                    return xs[i], xs[j]
                if s < target: i += 1
                else: j -= 1
            return None
        ''',
        '''
        def test_found():
            assert pair_sum([1, 2, 4, 7, 11], 15) == (4, 11)

        def test_missing():
            assert pair_sum([1, 2, 3], 10) is None

        def test_no_self_pair():
            assert pair_sum([5], 10) is None
        ''',
        "Start the pointers at both ends of the sorted list; a sum that is too small can only grow by "
        "moving the left pointer right, and a sum too big only shrinks by moving the right one left.",
    ),
]
