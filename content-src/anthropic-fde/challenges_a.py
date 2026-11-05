"""Progressive coding challenges (set A) for the Anthropic FDE pack.

One problem, four levels, each forcing a refactor (research/anthropic-fde.md §3).
Built to packs/anthropic-fde/challenges-a.json.
"""
from _helpers import code


def join(*parts):
    """Concatenate code blocks with two blank lines between them."""
    return "\n\n\n".join(p.strip("\n") for p in parts) + "\n"

# ---------------------------------------------------------------------------
# Shared test scaffolding (prepended to each step's tests)
# ---------------------------------------------------------------------------

CLOCK = code('''
    class FakeClock:
        """Injected clock: call it to read the time, advance() to move it."""
        def __init__(self, now=0.0):
            self.now = now
        def __call__(self):
            return self.now
        def advance(self, seconds):
            self.now += seconds
''')

AGENT_FAKES = code('''
    import copy

    def fake_text(t):
        return {"type": "text", "text": t}

    def fake_tool_use(id, name, input):
        return {"type": "tool_use", "id": id, "name": name, "input": input}

    def fake_response(stop_reason, *blocks):
        return {"stop_reason": stop_reason, "content": list(blocks)}

    class FakeClient:
        """Scripted stand-in for client.messages.create: returns canned responses
        in order and records a deep copy of the messages it was sent."""
        def __init__(self, responses):
            self.responses = list(responses)
            self.calls = []
        def create(self, messages, **kwargs):
            self.calls.append(copy.deepcopy(messages))
            assert self.responses, "the model was called more times than the script allows"
            return self.responses.pop(0)

    class LoopingClient:
        """A model that never stops asking for a tool."""
        def __init__(self):
            self.calls = 0
        def create(self, messages, **kwargs):
            self.calls += 1
            assert self.calls <= 50, "model called 50+ times: no max_iterations guard?"
            return fake_response("tool_use", fake_text("again"),
                                 fake_tool_use(f"t{self.calls}", "ping", {}))

    def last_tool_results(client, call_index=-1):
        """Tool_result blocks in the last user message of a recorded call."""
        msg = client.calls[call_index][-1]
        assert msg["role"] == "user", f"last message should be the user's tool results, got {msg}"
        assert isinstance(msg["content"], list), "tool results go in a list of content blocks"
        return msg["content"]
''')

TOKENS = code('''
    def _msg(role, n, tag, **extra):
        """A message whose content is n tokens (words) of `tag`."""
        return {"role": role, "content": " ".join([tag] * n), **extra}

    def _tags(messages):
        return [m["content"].split()[0] if m["content"] else "" for m in messages]
''')


# ===========================================================================
# 1. LRU cache
# ===========================================================================

LRU_S1 = code('''
    from collections import OrderedDict


    class LRUCache:
        def __init__(self, capacity):
            if capacity < 1:
                raise ValueError("capacity must be >= 1")
            self.capacity = capacity
            self._data = OrderedDict()  # oldest first, most recently used last

        def get(self, key, default=None):
            if key not in self._data:
                return default
            self._data.move_to_end(key)
            return self._data[key]

        def put(self, key, value):
            self._data[key] = value
            self._data.move_to_end(key)
            if len(self._data) > self.capacity:
                self._data.popitem(last=False)  # evict least recently used

        def __len__(self):
            return len(self._data)
''')

LRU_S1_TESTS = code('''
    def test_get_and_put():
        c = LRUCache(2)
        c.put("a", 1)
        assert c.get("a") == 1, "get should return the stored value"
        assert c.get("zzz") is None, "missing key should return None"
        assert c.get("zzz", "dflt") == "dflt", "missing key should return the default"

    def test_evicts_least_recently_used():
        c = LRUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        c.get("a")          # a is now most recent
        c.put("c", 3)       # evicts b
        assert c.get("b") is None, "b was least recently used and should be evicted"
        assert c.get("a") == 1 and c.get("c") == 3, "a and c should remain"

    def test_put_overwrites_and_refreshes():
        c = LRUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        c.put("a", 10)      # update + refresh a
        c.put("c", 3)       # evicts b, not a
        assert c.get("a") == 10, "put on an existing key should overwrite and refresh it"
        assert c.get("b") is None, "b should be evicted after a was refreshed"
        assert len(c) == 2, f"len should be 2, got {len(c)}"

    def test_falsy_values():
        c = LRUCache(3)
        c.put("zero", 0)
        c.put("empty", "")
        assert c.get("zero", "miss") == 0, "a stored 0 is a hit, not a miss"
        assert c.get("empty", "miss") == "", "a stored '' is a hit, not a miss"

    def test_capacity_validation():
        try:
            LRUCache(0)
        except ValueError:
            return
        assert False, "LRUCache(0) should raise ValueError"
''')

LRU_S2 = code('''
    import time
    from collections import OrderedDict


    class LRUCache:
        def __init__(self, capacity, ttl=None, clock=time.monotonic):
            if capacity < 1:
                raise ValueError("capacity must be >= 1")
            self.capacity = capacity
            self.ttl = ttl
            self.clock = clock
            self._data = OrderedDict()  # key -> (value, expires_at or None)

        def _expired(self, expires_at):
            return expires_at is not None and self.clock() >= expires_at

        def get(self, key, default=None):
            entry = self._data.get(key)
            if entry is None:
                return default
            value, expires_at = entry
            if self._expired(expires_at):
                del self._data[key]
                return default
            self._data.move_to_end(key)
            return value

        def put(self, key, value, ttl=None):
            ttl = self.ttl if ttl is None else ttl
            expires_at = None if ttl is None else self.clock() + ttl
            self._data[key] = (value, expires_at)
            self._data.move_to_end(key)
            if len(self._data) > self.capacity:
                self._data.popitem(last=False)

        def _purge_expired(self):
            dead = [k for k, (_, exp) in self._data.items() if self._expired(exp)]
            for key in dead:
                del self._data[key]

        def __len__(self):
            self._purge_expired()
            return len(self._data)
''')

LRU_S2_TESTS = CLOCK + LRU_S1_TESTS + code('''
    def test_ttl_expiry_boundary():
        clock = FakeClock()
        c = LRUCache(3, ttl=10, clock=clock)
        c.put("a", 1)
        clock.advance(9.99)
        assert c.get("a") == 1, "entry should still be live just before ttl"
        clock.advance(0.01)
        assert c.get("a") is None, "entry should expire exactly at put_time + ttl"

    def test_no_ttl_never_expires():
        clock = FakeClock()
        c = LRUCache(2, clock=clock)
        c.put("a", 1)
        clock.advance(10**9)
        assert c.get("a") == 1, "without a ttl entries never expire"

    def test_per_put_ttl_override():
        clock = FakeClock()
        c = LRUCache(3, ttl=100, clock=clock)
        c.put("short", 1, ttl=5)
        c.put("long", 2)
        clock.advance(6)
        assert c.get("short") is None, "put(..., ttl=5) should override the default ttl"
        assert c.get("long") == 2, "default ttl=100 entry should still be live"

    def test_put_resets_ttl():
        clock = FakeClock()
        c = LRUCache(3, ttl=10, clock=clock)
        c.put("a", 1)
        clock.advance(8)
        c.put("a", 2)
        clock.advance(8)
        assert c.get("a") == 2, "re-putting a key should restart its ttl"

    def test_len_ignores_expired():
        clock = FakeClock()
        c = LRUCache(5, ttl=10, clock=clock)
        c.put("a", 1)
        clock.advance(5)
        c.put("b", 2)
        clock.advance(5)
        assert len(c) == 1, f"only b is live at t=10, len should be 1, got {len(c)}"
''')

LRU_S3 = code('''
    import time
    from collections import OrderedDict


    class LRUCache:
        def __init__(self, capacity, ttl=None, clock=time.monotonic, on_evict=None):
            if capacity < 1:
                raise ValueError("capacity must be >= 1")
            self.capacity = capacity
            self.ttl = ttl
            self.clock = clock
            self.on_evict = on_evict
            self._data = OrderedDict()  # key -> (value, expires_at or None)
            self._counts = {"hits": 0, "misses": 0, "evictions": 0, "expirations": 0}

        def _expired(self, expires_at):
            return expires_at is not None and self.clock() >= expires_at

        def _remove(self, key, reason):
            """Single exit point for entries: counts it and fires the callback."""
            value, _ = self._data.pop(key)
            self._counts["evictions" if reason == "capacity" else "expirations"] += 1
            if self.on_evict is not None:
                self.on_evict(key, value, reason)

        def get(self, key, default=None):
            entry = self._data.get(key)
            if entry is not None and self._expired(entry[1]):
                self._remove(key, "expired")
                entry = None
            if entry is None:
                self._counts["misses"] += 1
                return default
            self._counts["hits"] += 1
            self._data.move_to_end(key)
            return entry[0]

        def put(self, key, value, ttl=None):
            ttl = self.ttl if ttl is None else ttl
            expires_at = None if ttl is None else self.clock() + ttl
            self._data[key] = (value, expires_at)
            self._data.move_to_end(key)
            if len(self._data) > self.capacity:
                oldest = next(iter(self._data))
                self._remove(oldest, "capacity")

        def _purge_expired(self):
            dead = [k for k, (_, exp) in self._data.items() if self._expired(exp)]
            for key in dead:
                self._remove(key, "expired")

        def __len__(self):
            self._purge_expired()
            return len(self._data)

        def stats(self):
            lookups = self._counts["hits"] + self._counts["misses"]
            hit_rate = self._counts["hits"] / lookups if lookups else 0.0
            return {**self._counts, "hit_rate": hit_rate}
''')

LRU_S3_TESTS = LRU_S2_TESTS + code('''
    def test_stats_hit_rate():
        c = LRUCache(2)
        assert c.stats()["hit_rate"] == 0.0, "hit_rate with no lookups should be 0.0, not a ZeroDivisionError"
        c.put("a", 1)
        c.get("a"); c.get("a"); c.get("a"); c.get("nope")
        s = c.stats()
        assert (s["hits"], s["misses"]) == (3, 1), f"expected 3 hits / 1 miss, got {s}"
        assert abs(s["hit_rate"] - 0.75) < 1e-9, f"hit_rate should be 0.75, got {s['hit_rate']}"

    def test_on_evict_capacity():
        events = []
        c = LRUCache(2, on_evict=lambda k, v, reason: events.append((k, v, reason)))
        c.put("a", 1); c.put("b", 2); c.put("c", 3)
        assert events == [("a", 1, "capacity")], f"expected a evicted for capacity, got {events}"
        assert c.stats()["evictions"] == 1, "evictions counter should be 1"

    def test_overwrite_is_not_eviction():
        events = []
        c = LRUCache(2, on_evict=lambda *e: events.append(e))
        c.put("a", 1); c.put("a", 2)
        assert events == [], "overwriting a key is not an eviction"

    def test_on_evict_expired_counts_as_miss():
        clock = FakeClock()
        events = []
        c = LRUCache(2, ttl=5, clock=clock, on_evict=lambda k, v, r: events.append((k, r)))
        c.put("a", 1)
        clock.advance(5)
        assert c.get("a") is None
        s = c.stats()
        assert events == [("a", "expired")], f"expired get should fire on_evict(..., 'expired'), got {events}"
        assert s["misses"] == 1 and s["expirations"] == 1 and s["evictions"] == 0, f"bad stats {s}"
''')

LRU_S4 = LRU_S3.replace("import time\n", "import functools\nimport time\n", 1).rstrip("\n") + "\n\n\n" + code('''
    _MISSING = object()  # sentinel: lets us cache functions that return None


    def _make_key(args, kwargs):
        # Positional and keyword parts stay in separate slots, so f(("a", 1))
        # and f(a=1) never collide; sorting makes kwarg order irrelevant.
        return (args, tuple(sorted(kwargs.items())))


    def memoize(maxsize=128, ttl=None, clock=time.monotonic):
        def decorator(func):
            cache = LRUCache(maxsize, ttl=ttl, clock=clock)

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                key = _make_key(args, kwargs)
                try:
                    hash(key)
                except TypeError:          # unhashable argument: just call through
                    return func(*args, **kwargs)
                value = cache.get(key, _MISSING)
                if value is _MISSING:
                    value = func(*args, **kwargs)
                    cache.put(key, value)
                return value

            wrapper.cache = cache
            return wrapper
        return decorator
''')

LRU_S4_TESTS = LRU_S3_TESTS + code('''
    def test_memoize_basic_and_wraps():
        calls = []
        @memoize(maxsize=4)
        def square(x):
            """docstring"""
            calls.append(x)
            return x * x
        assert square(3) == 9 and square(3) == 9
        assert calls == [3], f"second call should hit the cache, calls={calls}"
        assert square.__name__ == "square", "use functools.wraps to keep the function's name"
        assert square.cache.stats()["hits"] == 1, "wrapper.cache should be the LRUCache"

    def test_memoize_kwarg_order_irrelevant():
        calls = []
        @memoize()
        def f(a, b):
            calls.append((a, b))
            return a - b
        assert f(a=5, b=2) == 3 and f(b=2, a=5) == 3
        assert len(calls) == 1, "f(a=5, b=2) and f(b=2, a=5) are the same call"

    def test_memoize_args_and_kwargs_do_not_collide():
        @memoize()
        def g(*args, **kwargs):
            return (args, kwargs)
        assert g(("x", 1)) == ((("x", 1),), {}), "positional tuple arg"
        assert g(x=1) == ((), {"x": 1}), "g(x=1) must not reuse the cached result of g(('x', 1))"

    def test_memoize_caches_none():
        calls = []
        @memoize()
        def nothing(x):
            calls.append(x)
            return None
        nothing(1); nothing(1)
        assert calls == [1], "a function returning None should still be cached (use a sentinel)"

    def test_memoize_unhashable_falls_through():
        @memoize()
        def total(xs):
            return sum(xs)
        assert total([1, 2, 3]) == 6, "unhashable args should call the function, not raise"
        assert total([1, 2, 3]) == 6

    def test_memoize_maxsize_and_ttl():
        clock = FakeClock()
        calls = []
        @memoize(maxsize=2, ttl=10, clock=clock)
        def h(x):
            calls.append(x)
            return x
        h(1); h(2); h(3)        # 1 evicted
        h(1)
        assert calls == [1, 2, 3, 1], f"maxsize=2 should evict the LRU entry, calls={calls}"
        clock.advance(10)
        h(1)
        assert calls[-1] == 1 and len(calls) == 5, "entries should expire after ttl"
''')

LRU = {
    "id": "fde-ch-lru-cache", "type": "challenge", "stage": "coding", "difficulty": 2,
    "tags": ["lru", "ordereddict", "ttl", "decorator", "caching"], "pattern": "LRU cache",
    "source": "S16",
    "title": "LRU cache → TTL → stats → memoize",
    "summary": "Build an LRU cache, then add expiry with an injected clock, observability "
               "(hit rate, eviction callback), and finally a memoize decorator whose cache "
               "key handles *args/**kwargs correctly: the reported bug area.",
    "talkPrompts": [
        "State the complexity: get and put are O(1) because OrderedDict is a hash map plus a doubly linked list.",
        "Say why you inject the clock: deterministic tests, no sleeping.",
        "Name the expiry policy: lazy on access vs. a background sweeper, and the memory tradeoff.",
        "Explain why every removal goes through one _remove method before adding the callback.",
        "Walk through the cache-key collision: f(('a', 1)) vs f(a=1), and why None needs a sentinel.",
    ],
    "steps": [
        {
            "title": "LRU get/put",
            "minutes": 8,
            "prompt": code('''
                Implement `LRUCache(capacity)`:

                - `get(key, default=None)` returns the value (marking it most recently used) or `default`.
                - `put(key, value)` inserts/overwrites; if over capacity, evict the **least recently used** key.
                - `len(cache)` is the number of entries.
                - `capacity < 1` raises `ValueError`.

                ```python
                c = LRUCache(2)
                c.put("a", 1); c.put("b", 2)
                c.get("a")          # 1, a is now most recent
                c.put("c", 3)       # evicts "b"
                c.get("b")          # None
                ```
            '''),
            "starter": code('''
                class LRUCache:
                    def __init__(self, capacity):
                        pass

                    def get(self, key, default=None):
                        pass

                    def put(self, key, value):
                        pass

                    def __len__(self):
                        return 0
            '''),
            "tests": LRU_S1_TESTS,
            "hints": [
                "You need O(1) lookup AND O(1) 'which key is oldest'. One stdlib type gives both.",
                "collections.OrderedDict keeps insertion order; move_to_end(key) marks a key as recent.",
                "put: self._data[key] = value; self._data.move_to_end(key); if too big: self._data.popitem(last=False).",
            ],
            "solution": LRU_S1,
            "lesson": "Pick the data structure from the operations you need: OrderedDict is a hash map plus "
                      "recency order, so get/put are O(1). Test with `key in d`, not truthiness, so stored "
                      "0 or '' still count as hits.",
            "alternative": "Hand-roll a dict + doubly linked list with sentinel head/tail nodes. It's the same O(1), "
                           "about 40 lines, and what interviewers want if they ban OrderedDict. A plain dict also "
                           "keeps insertion order (pop and re-insert to refresh), but next(iter(d)) is slower to "
                           "explain than popitem(last=False).",
        },
        {
            "title": "TTL with an injected clock",
            "minutes": 10,
            "prompt": code('''
                Add expiry: `LRUCache(capacity, ttl=None, clock=time.monotonic)`.

                - `put(key, value, ttl=None)` stores an expiry of `clock() + ttl` (per-call ttl overrides the default; `None` = never).
                - An entry is expired when `clock() >= expires_at`. `get` on it removes it and returns `default`.
                - Re-putting a key restarts its ttl. `len()` counts only live entries.
                - All earlier behaviour still holds.

                ```python
                clock = FakeClock()          # clock() returns clock.now
                c = LRUCache(3, ttl=10, clock=clock)
                c.put("a", 1); clock.now = 10
                c.get("a")                   # None (expired)
                ```
            '''),
            "tests": LRU_S2_TESTS,
            "hints": [
                "Each entry now needs two things: the value and when it dies. Change what you store, not the structure.",
                "Store (value, expires_at) tuples where expires_at is None for no ttl; check expiry in get.",
                "def _expired(self, exp): return exp is not None and self.clock() >= exp; in get, del + return default if expired.",
            ],
            "solution": LRU_S2,
            "lesson": "Refactor the stored value into a record before adding the feature, and inject time as a "
                      "callable so tests can control it. Lazy expiry (check on read) is O(1) and needs no thread.",
            "alternative": "Keep a min-heap of (expires_at, key) and pop expired entries on every operation. That "
                           "reclaims memory from keys nobody reads, but stale heap entries from re-puts must be "
                           "skipped. A background sweeper thread works too, but it adds locking and is hard to test.",
        },
        {
            "title": "Stats and eviction callback",
            "minutes": 10,
            "prompt": code('''
                Add observability: `LRUCache(capacity, ttl=None, clock=..., on_evict=None)`.

                - `on_evict(key, value, reason)` fires when an entry leaves: `reason` is `"capacity"` or `"expired"`. Overwriting a key is **not** an eviction.
                - `stats()` returns `{"hits", "misses", "evictions", "expirations", "hit_rate"}`.
                - An expired `get` counts as a miss **and** an expiration. `hit_rate = hits / (hits + misses)`, or `0.0` with no lookups.

                ```python
                c = LRUCache(2, on_evict=print)
                c.put("a", 1); c.put("b", 2); c.put("c", 3)   # prints: a 1 capacity
                ```
            '''),
            "tests": LRU_S3_TESTS,
            "hints": [
                "Entries now leave from three places (get, put, len). Give them one exit door first.",
                "Write _remove(key, reason) that pops the entry, bumps the right counter and calls on_evict; use it everywhere.",
                "For capacity eviction: oldest = next(iter(self._data)); self._remove(oldest, 'capacity').",
            ],
            "solution": LRU_S3,
            "lesson": "Before adding a cross-cutting feature (metrics, callbacks), funnel every code path through "
                      "one helper, then add the feature there once. Guard the division in hit_rate.",
            "alternative": "Use a dataclass `Stats` or `collections.Counter` instead of a dict; Counter makes "
                           "increments one-liners. For production you'd emit to a metrics client (Prometheus) instead "
                           "of storing counts, and wrap on_evict in try/except so a bad callback can't corrupt the cache.",
        },
        {
            "title": "memoize decorator (the cache-key bug)",
            "minutes": 12,
            "prompt": code('''
                Add `memoize(maxsize=128, ttl=None, clock=time.monotonic)`, a decorator factory backed by your `LRUCache`.

                - Cache by arguments: `f(a=1, b=2)` and `f(b=2, a=1)` are the same call.
                - `f(("x", 1))` and `f(x=1)` are **different** calls.
                - Functions returning `None` are still cached.
                - Unhashable args (e.g. a list): call the function uncached, don't raise.
                - Keep `__name__` (functools.wraps) and expose `wrapper.cache`.

                ```python
                @memoize(maxsize=2)
                def square(x): return x * x
                square(3); square(3)       # computed once
                ```
            '''),
            "tests": LRU_S4_TESTS,
            "hints": [
                "The buggy version builds key = args + tuple(kwargs.items()). Try it on g(('x', 1)) vs g(x=1).",
                "Keep positional and keyword parts in separate slots and sort kwargs: key = (args, tuple(sorted(kwargs.items()))).",
                "Use a sentinel _MISSING = object(); value = cache.get(key, _MISSING); if value is _MISSING: compute + put. Wrap hash(key) in try/except TypeError.",
            ],
            "solution": LRU_S4,
            "lesson": "A cache key must be unambiguous: keep structurally different inputs in separate tuple slots "
                      "and normalize order-insensitive parts (sorted kwargs). Use a sentinel, not None, to tell a "
                      "miss from a cached None. This is the reported Anthropic LRU bug.",
            "alternative": "Bind arguments with inspect.signature(func).bind(*args, **kwargs) + apply_defaults() so "
                           "f(1) and f(x=1) share an entry too. It's more correct, but slower per call. "
                           "functools.lru_cache uses a flat key with a kwd_mark sentinel separator, which is faster "
                           "but treats f(1) and f(x=1) as different calls.",
        },
    ],
}


# ===========================================================================
# 2. Rate limiter
# ===========================================================================

RL_S1 = code('''
    import time


    class RateLimiter:
        """Fixed window: at most `limit` requests per key per aligned window."""

        def __init__(self, limit, window, clock=time.monotonic):
            self.limit = limit
            self.window = window
            self.clock = clock
            self._windows = {}  # key -> (window_start, count)

        def allow(self, key):
            now = self.clock()
            start = now // self.window * self.window
            win_start, count = self._windows.get(key, (start, 0))
            if win_start != start:
                count = 0  # a new window began
            if count >= self.limit:
                return False
            self._windows[key] = (start, count + 1)
            return True
''')

RL_COMMON_TESTS = CLOCK + code('''
    def test_limit_within_window():
        clock = FakeClock()
        rl = RateLimiter(3, 10, clock=clock)
        assert [rl.allow("u") for _ in range(4)] == [True, True, True, False], \\
            "3 requests allowed, 4th denied"

    def test_keys_are_independent():
        clock = FakeClock()
        rl = RateLimiter(1, 10, clock=clock)
        assert rl.allow("alice") and rl.allow("bob"), "each key has its own limit"
        assert not rl.allow("alice"), "alice is over her limit"
''')

RL_S1_TESTS = RL_COMMON_TESTS + code('''
    def test_resets_on_window_boundary():
        clock = FakeClock()
        rl = RateLimiter(2, 10, clock=clock)
        rl.allow("u"); rl.allow("u")
        clock.now = 9.5
        assert not rl.allow("u"), "still the same window at t=9.5"
        clock.now = 10
        assert rl.allow("u"), "a new window starts at t=10"

    def test_fixed_windows_are_aligned():
        clock = FakeClock(9)
        rl = RateLimiter(2, 10, clock=clock)
        assert rl.allow("u") and rl.allow("u")
        clock.now = 10
        assert rl.allow("u") and rl.allow("u"), \\
            "windows are aligned to multiples of `window` (this burst is the known fixed-window flaw)"
''')

RL_SLIDING = code('''
    class RateLimiter:
        """Sliding log: at most `limit` allowed requests in any `window` seconds."""

        def __init__(self, limit, window, clock=time.monotonic):
            self.limit = limit
            self.window = window
            self.clock = clock
            self._log = defaultdict(deque)  # key -> timestamps of allowed requests

        def allow(self, key):
            now = self.clock()
            log = self._log[key]
            while log and log[0] <= now - self.window:
                log.popleft()  # older than the window
            if len(log) >= self.limit:
                return False
            log.append(now)
            return True
''')

RL_S2 = join("import time\nfrom collections import defaultdict, deque", RL_SLIDING)

RL_S2_TESTS = RL_COMMON_TESTS + code('''
    def test_no_boundary_burst():
        clock = FakeClock(9)
        rl = RateLimiter(2, 10, clock=clock)
        assert rl.allow("u") and rl.allow("u")
        clock.now = 10
        assert not rl.allow("u"), "sliding window: the 2 requests at t=9 still count at t=10"

    def test_slides_one_request_at_a_time():
        clock = FakeClock(0)
        rl = RateLimiter(2, 10, clock=clock)
        assert rl.allow("u")              # t=0
        clock.now = 5
        assert rl.allow("u")              # t=5
        clock.now = 9.9
        assert not rl.allow("u"), "t=9.9: both requests are inside the window"
        clock.now = 10
        assert rl.allow("u"), "t=10: the t=0 request has left the window"
        assert not rl.allow("u"), "t=10: t=5 and t=10 fill the window"
        clock.now = 15
        assert rl.allow("u"), "t=15: the t=5 request has left the window"

    def test_denied_requests_are_not_logged():
        clock = FakeClock(0)
        rl = RateLimiter(1, 10, clock=clock)
        assert rl.allow("u")
        for t in range(1, 10):
            clock.now = t
            assert not rl.allow("u")
        clock.now = 10
        assert rl.allow("u"), "denied requests must not extend the window"
''')

RL_S3 = join("import time\nfrom collections import defaultdict, deque\nfrom dataclasses import dataclass",
              RL_SLIDING, code('''
    @dataclass
    class _Bucket:
        tokens: float
        updated: float


    class TokenBucket:
        """Each key's bucket holds up to `capacity` tokens, refilled at
        `refill_rate` tokens/second. Refill is computed lazily on access."""

        def __init__(self, capacity, refill_rate, clock=time.monotonic):
            self.capacity = capacity
            self.refill_rate = refill_rate
            self.clock = clock
            self._buckets = {}

        def _refill(self, key):
            now = self.clock()
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = self._buckets[key] = _Bucket(self.capacity, now)
            else:
                elapsed = now - bucket.updated
                bucket.tokens = min(self.capacity, bucket.tokens + elapsed * self.refill_rate)
                bucket.updated = now
            return bucket

        def allow(self, key, cost=1):
            bucket = self._refill(key)
            if bucket.tokens >= cost:
                bucket.tokens -= cost
                return True
            return False
'''))

RL_TB_TESTS = code('''
    def test_bucket_starts_full_then_denies():
        clock = FakeClock()
        tb = TokenBucket(4, 2, clock=clock)
        assert [tb.allow("u") for _ in range(5)] == [True] * 4 + [False], \\
            "a full bucket of 4 allows 4 requests, then denies"

    def test_bucket_refills_over_time():
        clock = FakeClock()
        tb = TokenBucket(4, 2, clock=clock)
        for _ in range(4):
            tb.allow("u")
        clock.now = 0.5                   # +1 token at 2 tokens/s
        assert tb.allow("u"), "0.5 s at 2 tokens/s refills 1 token"
        assert not tb.allow("u"), "only 1 token was refilled"

    def test_bucket_caps_at_capacity():
        clock = FakeClock()
        tb = TokenBucket(4, 2, clock=clock)
        tb.allow("u", cost=4)
        clock.now = 100
        assert tb.allow("u", cost=4), "bucket refills to capacity"
        assert not tb.allow("u"), "refill is capped at capacity, not 200 tokens"

    def test_bucket_cost_and_denials_are_free():
        clock = FakeClock()
        tb = TokenBucket(4, 2, clock=clock)
        assert not tb.allow("u", cost=5), "cost above capacity can never pass"
        assert tb.allow("u", cost=4)
        clock.now = 0.25                  # 0.5 tokens
        assert not tb.allow("u"), "0.5 tokens is not enough for cost 1"
        clock.now = 0.5                   # 1.0 tokens (the denial cost nothing)
        assert tb.allow("u"), "a denied request must not consume tokens"

    def test_bucket_keys_independent():
        clock = FakeClock()
        tb = TokenBucket(1, 1, clock=clock)
        assert tb.allow("a") and tb.allow("b"), "each key has its own bucket"
        assert not tb.allow("a")
''')

RL_S3_TESTS = RL_S2_TESTS + RL_TB_TESTS

RL_S4 = join("import math\nimport time\nfrom collections import defaultdict, deque\n"
              "from dataclasses import dataclass\nfrom typing import NamedTuple",
              RL_SLIDING, code('''
    class Decision(NamedTuple):
        allowed: bool
        retry_after: float  # seconds; 0.0 if allowed, math.inf if it can never pass


    @dataclass
    class _Bucket:
        tokens: float
        updated: float


    class TokenBucket:
        def __init__(self, capacity, refill_rate, clock=time.monotonic, overrides=None):
            self.default = (capacity, refill_rate)
            self.overrides = dict(overrides or {})  # key -> (capacity, refill_rate)
            self.clock = clock
            self._buckets = {}

        def limits_for(self, key):
            return self.overrides.get(key, self.default)

        def _refill(self, key, capacity, rate):
            now = self.clock()
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = self._buckets[key] = _Bucket(capacity, now)
            else:
                elapsed = now - bucket.updated
                bucket.tokens = min(capacity, bucket.tokens + elapsed * rate)
                bucket.updated = now
            return bucket

        def check(self, key, cost=1):
            capacity, rate = self.limits_for(key)
            bucket = self._refill(key, capacity, rate)
            if bucket.tokens >= cost:
                bucket.tokens -= cost
                return Decision(True, 0.0)
            if cost > capacity or rate <= 0:
                return Decision(False, math.inf)
            return Decision(False, (cost - bucket.tokens) / rate)

        def allow(self, key, cost=1):
            return self.check(key, cost).allowed
'''))

RL_S4_TESTS = RL_S3_TESTS + code('''
    import math

    def test_check_returns_decision():
        clock = FakeClock()
        tb = TokenBucket(2, 1, clock=clock)
        d = tb.check("u")
        assert d.allowed is True and d.retry_after == 0.0, f"first request allowed, retry_after 0.0; got {d}"

    def test_retry_after_seconds():
        clock = FakeClock()
        tb = TokenBucket(2, 1, clock=clock)
        tb.check("u"); tb.check("u")
        d = tb.check("u")
        assert d.allowed is False, "bucket is empty"
        assert abs(d.retry_after - 1.0) < 1e-9, f"1 token at 1/s -> retry_after 1.0, got {d.retry_after}"
        clock.now = 0.5
        d = tb.check("u")
        assert abs(d.retry_after - 0.5) < 1e-9, f"half refilled -> retry_after 0.5, got {d.retry_after}"
        clock.now = 1.0
        assert tb.check("u").allowed, "after retry_after the request passes"

    def test_retry_after_inf_when_impossible():
        tb = TokenBucket(2, 1, clock=FakeClock())
        d = tb.check("u", cost=3)
        assert d.allowed is False and d.retry_after == math.inf, "cost > capacity can never pass: inf"

    def test_per_key_overrides():
        clock = FakeClock()
        tb = TokenBucket(2, 1, clock=clock, overrides={"vip": (5, 5)})
        assert [tb.allow("vip") for _ in range(6)] == [True] * 5 + [False], "vip gets capacity 5"
        assert [tb.allow("free") for _ in range(3)] == [True, True, False], "others get the default 2"
        d = tb.check("vip")
        assert abs(d.retry_after - 0.2) < 1e-9, f"vip refills at 5/s -> retry_after 0.2, got {d.retry_after}"
''')

RATE = {
    "id": "fde-ch-rate-limiter", "type": "challenge", "stage": "coding", "difficulty": 2,
    "tags": ["rate-limiting", "deque", "token-bucket", "dataclass", "clock-injection"],
    "pattern": "rate limiter", "source": "S15",
    "title": "Rate limiter: fixed → sliding → token bucket → retry_after",
    "summary": "Per-key request limiting that evolves the way real API gateways did: a fixed "
               "window, a sliding log that fixes the boundary burst, a token bucket with lazy "
               "refill, then per-key tiers and a Retry-After value.",
    "talkPrompts": [
        "Name the fixed-window flaw out loud: 2x the limit can pass across a window boundary.",
        "State memory per key: fixed O(1), sliding log O(limit), token bucket O(1).",
        "Explain lazy refill: compute tokens from elapsed time on access, no timer thread.",
        "Say how this goes distributed: Redis INCR+EXPIRE or a Lua script for atomic check-and-decrement.",
        "Mention what the HTTP layer does with it: 429 plus a Retry-After header.",
    ],
    "steps": [
        {
            "title": "Fixed window per key",
            "minutes": 8,
            "prompt": code('''
                Implement `RateLimiter(limit, window, clock=time.monotonic)` with `allow(key) -> bool`.

                - Each key may make `limit` requests per window of `window` seconds.
                - Windows are aligned: `[0, 10)`, `[10, 20)`, ... (start = `now // window * window`).
                - Keys are independent. `clock()` returns the current time (tests inject a fake).

                ```python
                rl = RateLimiter(3, 10, clock=clock)
                [rl.allow("u") for _ in range(4)]  # [True, True, True, False]
                clock.now = 10; rl.allow("u")      # True (new window)
                ```
            '''),
            "starter": code('''
                import time


                class RateLimiter:
                    def __init__(self, limit, window, clock=time.monotonic):
                        pass

                    def allow(self, key):
                        pass
            '''),
            "tests": RL_S1_TESTS,
            "hints": [
                "Per key you only need two numbers: which window you're in and how many requests it has seen.",
                "Store self._windows[key] = (window_start, count); compute window_start from clock().",
                "start = now // self.window * self.window; if the stored start differs, reset count to 0; deny if count >= limit.",
            ],
            "solution": RL_S1,
            "lesson": "Start with a dict keyed by the client and the smallest per-key state that works. Inject the "
                      "clock from level 1 so every later level stays testable without sleeping.",
            "alternative": "Key a dict by (key, window_start) and increment counts. It's simpler to write, but old "
                           "windows pile up unless you clean them. This is how Redis INCR + EXPIRE does it.",
        },
        {
            "title": "Sliding window log",
            "minutes": 10,
            "prompt": code('''
                Customers abuse the boundary: 2 requests at t=9 and 2 more at t=10 all pass.
                Change `RateLimiter` (same API) so that **any** `window`-second span holds at most `limit` allowed requests.

                - A request at time `t` stops counting once `now - t >= window`.
                - Denied requests are not recorded.

                ```python
                rl = RateLimiter(2, 10, clock=clock)  # clock.now = 9
                rl.allow("u"); rl.allow("u")          # True, True
                clock.now = 10; rl.allow("u")         # False
                clock.now = 19; rl.allow("u")         # True
                ```
            '''),
            "tests": RL_S2_TESTS,
            "hints": [
                "Remember when each allowed request happened, per key.",
                "A collections.deque per key: drop timestamps from the left while they're older than the window.",
                "while log and log[0] <= now - self.window: log.popleft(); then deny if len(log) >= limit, else append(now).",
            ],
            "solution": RL_S2,
            "lesson": "When a requirement changes the algorithm, keep the public API and swap the per-key state "
                      "(a counter becomes a deque of timestamps). The old tests that still apply prove the refactor.",
            "alternative": "Sliding window counter: keep the current and previous fixed-window counts and weight the "
                           "previous by overlap (prev * (1 - elapsed/window) + curr). That's O(1) memory per key, but "
                           "approximate. Cloudflare uses it at scale.",
        },
        {
            "title": "Token bucket with refill",
            "minutes": 10,
            "prompt": code('''
                Bursty clients need smoothing. Keep `RateLimiter` and add `TokenBucket(capacity, refill_rate, clock=time.monotonic)` with `allow(key, cost=1) -> bool`.

                - Each key's bucket starts **full** (`capacity` tokens) and refills at `refill_rate` tokens/second, never above `capacity`.
                - Allowed: subtract `cost`. Denied: nothing is consumed.

                ```python
                tb = TokenBucket(4, 2, clock=clock)
                [tb.allow("u") for _ in range(5)]   # [T, T, T, T, False]
                clock.now = 0.5; tb.allow("u")      # True (+1 token)
                ```
            '''),
            "tests": RL_S3_TESTS,
            "hints": [
                "Don't run a timer. Work out how many tokens there should be from the time since the last access.",
                "Per key store tokens and last-updated time (a small @dataclass); on each call add elapsed * refill_rate, cap at capacity.",
                "bucket.tokens = min(capacity, bucket.tokens + (now - bucket.updated) * rate); bucket.updated = now; then compare to cost.",
            ],
            "solution": RL_S3,
            "lesson": "Lazy refill turns a time-driven process into arithmetic on access: O(1) and no threads. "
                      "Once per-key state has more than one field, give it a named dataclass.",
            "alternative": "Leaky bucket (a queue drained at a fixed rate) smooths output instead of allowing bursts. "
                           "GCRA stores a single 'theoretical arrival time' per key, so it's one number in Redis.",
        },
        {
            "title": "Per-key limits and retry_after",
            "minutes": 10,
            "prompt": code('''
                Add pricing tiers and a Retry-After value to `TokenBucket`:

                - `TokenBucket(capacity, refill_rate, clock=..., overrides=None)`, where `overrides = {key: (capacity, refill_rate)}`.
                - `check(key, cost=1) -> Decision` with fields `allowed: bool` and `retry_after: float` (seconds until it would pass; `0.0` if allowed; `math.inf` if `cost > capacity`).
                - `allow(key, cost=1)` still returns a bool.

                ```python
                tb = TokenBucket(2, 1, clock=clock, overrides={"vip": (5, 5)})
                tb.check("u"); tb.check("u")
                tb.check("u")     # Decision(allowed=False, retry_after=1.0)
                ```
            '''),
            "tests": RL_S4_TESTS,
            "hints": [
                "Limits are no longer one pair on self. Look them up per key, then pass them into the refill.",
                "limits_for(key) -> self.overrides.get(key, self.default); return a NamedTuple Decision(allowed, retry_after).",
                "If denied: retry_after = (cost - bucket.tokens) / rate; if cost > capacity: math.inf. allow() = check().allowed.",
            ],
            "solution": RL_S4,
            "lesson": "Make the config a lookup (key → limits) instead of fixed attributes, and return a small "
                      "result type instead of a bool once callers need more than yes/no. Keep the bool method as a "
                      "thin wrapper so old callers don't break.",
            "alternative": "Store capacity and rate on each _Bucket at creation. It's faster, but changing a "
                           "customer's tier means rebuilding their bucket. A @dataclass(frozen=True) Decision also "
                           "works; NamedTuple gives tuple unpacking for free.",
        },
    ],
}


# ===========================================================================
# 3. Token-budget allocator
# ===========================================================================

TB_COUNT = code('''
    def count_tokens(text):
        """Provided: a stand-in tokenizer (one token per word)."""
        return len(text.split())
''')

TB_S1 = join(TB_COUNT, code('''
    def fit_messages(messages, budget):
        kept, used = [], 0
        for message in reversed(messages):          # newest first
            cost = count_tokens(message["content"])
            if used + cost > budget:
                break
            kept.append(message)
            used += cost
        kept.reverse()
        return kept
'''))

TB_S1_TESTS = TOKENS + code('''
    def test_everything_fits():
        msgs = [_msg("user", 2, "a"), _msg("assistant", 2, "b"), _msg("user", 2, "c")]
        assert fit_messages(msgs, 100) == msgs, "under budget: return all messages in order"

    def test_keeps_newest_suffix():
        msgs = [_msg("user", 3, "a"), _msg("assistant", 3, "b"), _msg("user", 3, "c")]
        assert _tags(fit_messages(msgs, 7)) == ["b", "c"], "drop oldest first, keep order"

    def test_no_gaps_in_history():
        msgs = [_msg("user", 1, "a"), _msg("assistant", 5, "b"), _msg("user", 1, "c")]
        out = fit_messages(msgs, 3)
        assert _tags(out) == ["c"], f"history stays contiguous: once b is dropped, a goes too. got {_tags(out)}"

    def test_does_not_mutate_input():
        msgs = [_msg("user", 3, "a"), _msg("user", 3, "b")]
        before = [dict(m) for m in msgs]
        fit_messages(msgs, 3)
        assert msgs == before and len(msgs) == 2, "don't modify the caller's list"
''')

TB_S2 = join(TB_COUNT, code('''
    def fit_messages(messages, budget):
        costs = [count_tokens(m["content"]) for m in messages]
        required = {i for i, m in enumerate(messages) if m["role"] == "system"}
        users = [i for i, m in enumerate(messages) if m["role"] == "user"]
        if users:
            required.add(users[-1])                 # latest user message
        if sum(costs[i] for i in required) > budget:
            raise ValueError("system prompt + latest user message exceed the budget")

        kept = set(range(len(messages)))
        total = sum(costs)
        for i in range(len(messages)):              # drop oldest optional first
            if total <= budget:
                break
            if i not in required:
                kept.discard(i)
                total -= costs[i]
        return [messages[i] for i in sorted(kept)]
'''))

TB_S2_TESTS = TB_S1_TESTS + code('''
    def test_keeps_system_and_latest_user():
        msgs = [_msg("system", 2, "sys"), _msg("user", 3, "u1"),
                _msg("assistant", 3, "a1"), _msg("user", 2, "u2")]
        assert _tags(fit_messages(msgs, 6)) == ["sys", "u2"], \\
            "system and the latest user message are always kept"
        assert _tags(fit_messages(msgs, 7)) == ["sys", "a1", "u2"], \\
            "fill the rest with the newest other messages"

    def test_latest_user_not_last():
        msgs = [_msg("system", 1, "sys"), _msg("user", 2, "u1"),
                _msg("user", 2, "u2"), _msg("assistant", 4, "a2")]
        assert _tags(fit_messages(msgs, 5)) == ["sys", "u2"], \\
            "the latest USER message is kept even if an assistant message follows it"

    def test_required_over_budget_raises():
        msgs = [_msg("system", 5, "sys"), _msg("user", 5, "u")]
        try:
            fit_messages(msgs, 8)
        except ValueError:
            return
        assert False, "should raise ValueError when system + latest user can't fit"
''')

TB_S3 = join(TB_COUNT, code('''
    def fit_messages(messages, budget):
        costs = [count_tokens(m["content"]) for m in messages]
        required = {i for i, m in enumerate(messages)
                    if m["role"] == "system" or m.get("pinned")}
        users = [i for i, m in enumerate(messages) if m["role"] == "user"]
        if users:
            required.add(users[-1])
        if sum(costs[i] for i in required) > budget:
            raise ValueError("required messages exceed the budget")

        # Drop order: lowest priority first, then oldest first.
        drop_order = sorted((i for i in range(len(messages)) if i not in required),
                            key=lambda i: (messages[i].get("priority", 0), i))
        kept = set(range(len(messages)))
        total = sum(costs)
        for i in drop_order:
            if total <= budget:
                break
            kept.discard(i)
            total -= costs[i]
        return [messages[i] for i in sorted(kept)]
'''))

TB_S3_TESTS = TB_S2_TESTS + code('''
    def test_pinned_is_always_kept():
        msgs = [_msg("system", 1, "sys"), _msg("user", 2, "facts", pinned=True),
                _msg("assistant", 2, "a1"), _msg("user", 2, "u2")]
        assert _tags(fit_messages(msgs, 5)) == ["sys", "facts", "u2"], \\
            "a pinned message survives even though it is the oldest"

    def test_low_priority_dropped_first():
        msgs = [_msg("system", 1, "sys"), _msg("user", 2, "old", priority=5),
                _msg("assistant", 2, "chit", priority=-1), _msg("assistant", 2, "mid"),
                _msg("user", 2, "u2")]
        assert _tags(fit_messages(msgs, 7)) == ["sys", "old", "mid", "u2"], \\
            "drop the priority -1 message first"
        assert _tags(fit_messages(msgs, 5)) == ["sys", "old", "u2"], \\
            "drop priority -1 then priority 0 before the older priority-5 message"

    def test_priority_ties_drop_oldest():
        msgs = [_msg("user", 2, "a", priority=1), _msg("assistant", 2, "b", priority=1),
                _msg("user", 2, "c")]
        assert _tags(fit_messages(msgs, 4)) == ["b", "c"], "equal priority: oldest goes first"

    def test_pinned_over_budget_raises():
        msgs = [_msg("system", 2, "sys"), _msg("user", 5, "doc", pinned=True), _msg("user", 2, "u")]
        try:
            fit_messages(msgs, 8)
        except ValueError:
            return
        assert False, "pinned messages count as required: raise ValueError if they can't fit"
''')

TB_S4 = join(TB_S3, code('''
    MARKER = "[truncated]"


    def truncate(text, max_tokens, marker=MARKER):
        words = text.split()
        if len(words) <= max_tokens:
            return text
        keep = max_tokens - count_tokens(marker)
        if keep < 0:
            return ""
        return " ".join(words[:keep] + [marker])


    def allocate_docs(docs, budget):
        costs = [count_tokens(d) for d in docs]
        total = sum(costs)
        if total <= budget:
            return list(docs)
        out = []
        for doc, cost in zip(docs, costs):
            share = budget * cost // total          # proportional, rounded down
            if share > 0:
                out.append(truncate(doc, share))
        return out
'''))

TB_S4_TESTS = TB_S3_TESTS + code('''
    def _words(n, w="w"):
        return " ".join(f"{w}{i}" for i in range(n))

    def test_truncate_fits_unchanged():
        assert truncate("a b c", 3) == "a b c", "text that fits is returned unchanged"

    def test_truncate_adds_marker_within_limit():
        out = truncate("a b c d e", 3)
        assert out == "a b [truncated]", f"keep max_tokens-1 words + marker, got {out!r}"
        assert count_tokens(out) <= 3, "the marker counts toward max_tokens"

    def test_truncate_tiny_limit():
        assert truncate("a b c", 1) == "[truncated]", "max_tokens=1 leaves room only for the marker"
        assert truncate("a b c", 0) == "", "max_tokens=0 gives an empty string"

    def test_allocate_under_budget_unchanged():
        docs = [_words(3), _words(4)]
        assert allocate_docs(docs, 10) == docs, "docs that fit are returned as-is"

    def test_allocate_proportionally():
        docs = [_words(10, "a"), _words(30, "b")]
        out = allocate_docs(docs, 20)
        assert len(out) == 2
        assert [count_tokens(d) for d in out] == [5, 15], \\
            f"10:30 split of 20 tokens should be 5 and 15, got {[count_tokens(d) for d in out]}"
        assert out[0].endswith("[truncated]") and out[0].startswith("a0 a1 a2 a3"), out[0]
        assert sum(count_tokens(d) for d in out) <= 20, "never exceed the budget"

    def test_allocate_drops_zero_share():
        docs = [_words(1, "tiny"), _words(99, "big")]
        out = allocate_docs(docs, 50)
        assert len(out) == 1 and out[0].startswith("big0"), \\
            "a doc whose share rounds down to 0 is dropped"
        assert count_tokens(out[0]) <= 50
''')

TOKEN_BUDGET = {
    "id": "fde-ch-token-budget", "type": "challenge", "stage": "coding", "difficulty": 3,
    "tags": ["llm", "context-window", "greedy", "sorting", "truncation"],
    "pattern": "token budget allocation", "source": "S13",
    "title": "Token-budget allocator for an LLM prompt",
    "summary": "Fit a chat history into a context budget, then keep what must survive (system, "
               "latest user, pinned), drop by priority, and split leftover budget across "
               "retrieved documents with truncation markers. This is the everyday context "
               "engineering an FDE does for customers.",
    "talkPrompts": [
        "Clarify first: is the budget for input only, and does the system prompt count?",
        "Say why history must stay contiguous at level 1: gaps confuse the model about who said what.",
        "Name the invariant: required messages are never dropped; raise rather than silently send a broken prompt.",
        "Explain the drop-order key (priority, index) and why a sort key beats nested if/else.",
        "Mention real tokenizers: use the API's count_tokens endpoint; word count is only a stand-in.",
    ],
    "steps": [
        {
            "title": "Fit the newest messages",
            "minutes": 7,
            "prompt": code('''
                `count_tokens(text)` is provided (one token per word). Messages look like `{"role": "user", "content": "..."}`.

                Write `fit_messages(messages, budget) -> list` that keeps the **newest** messages whose total tokens are `<= budget`, in original order. Drop from the oldest end: once a message is dropped, every older one goes too. Don't mutate the input.

                ```python
                msgs = [m("a"*3), m("b"*3), m("c"*3)]  # 3 tokens each
                fit_messages(msgs, 7)    # [b, c]
                ```
            '''),
            "starter": join(TB_COUNT, code('''
                def fit_messages(messages, budget):
                    pass
            ''')),
            "tests": TB_S1_TESTS,
            "hints": [
                "Walk the list from the newest end and keep a running total.",
                "for message in reversed(messages): add while it fits, break as soon as one doesn't.",
                "Collect into a new list, then kept.reverse() before returning so the order is original.",
            ],
            "solution": TB_S1,
            "lesson": "When 'newest wins', iterate in reverse with a running total and stop at the first miss. "
                      "Build a new list rather than deleting from the caller's.",
            "alternative": "Compute suffix sums and binary-search the first index whose suffix fits: O(log n) per "
                           "query after O(n) prep. That's worth it only if you refit the same history many times.",
        },
        {
            "title": "Always keep system + latest user",
            "minutes": 10,
            "prompt": code('''
                Dropping the system prompt or the question breaks the call. Update `fit_messages`:

                - **Required**: every `system` message and the **latest `user`** message. They are always kept.
                - If required messages alone exceed `budget`, raise `ValueError`.
                - Then drop other messages **oldest first** until the total fits. Keep original order.

                ```python
                # sys(2) u1(3) a1(3) u2(2)
                fit_messages(msgs, 6)   # [sys, u2]
                fit_messages(msgs, 7)   # [sys, a1, u2]
                ```
            '''),
            "tests": TB_S2_TESTS,
            "hints": [
                "Flip the approach: start with everything and remove things, instead of adding from the end.",
                "Build a set of required indices; then loop i from 0 upward, discarding non-required i while total > budget.",
                "Return [messages[i] for i in sorted(kept)]; check sum(costs[i] for i in required) > budget first and raise.",
            ],
            "solution": TB_S2,
            "lesson": "Refactor 'keep a suffix' into 'start with everything, remove in a drop order until it fits'. "
                      "Working on indices (a kept set) keeps original order for free and makes the next rule a "
                      "one-line change to the drop order.",
            "alternative": "Split into required + optional lists, fit optional with the level-1 function against "
                           "budget - required_cost, then merge by original index. That reuses code, but the merge step "
                           "is easy to get wrong.",
        },
        {
            "title": "Pinned and priority messages",
            "minutes": 9,
            "prompt": code('''
                Customers attach key facts that must survive. Messages may carry:

                - `"pinned": True`: required, like system.
                - `"priority": int` (default 0): when dropping, remove **lowest priority first**; ties go oldest first.

                Required messages over budget still raise `ValueError`.

                ```python
                # sys(1) old(2,p=5) chit(2,p=-1) mid(2) u2(2)
                fit_messages(msgs, 7)   # [sys, old, mid, u2]
                fit_messages(msgs, 5)   # [sys, old, u2]
                ```
            '''),
            "tests": TB_S3_TESTS,
            "hints": [
                "You already remove in an order. Only the order (and what counts as required) changes.",
                "Required now includes m.get('pinned'); drop candidates are the non-required indices.",
                "drop_order = sorted(candidates, key=lambda i: (messages[i].get('priority', 0), i)), then the same loop.",
            ],
            "solution": TB_S3,
            "lesson": "Express policy as a sort key, not as nested conditions: (priority, index) encodes 'lowest "
                      "priority first, then oldest' in one place, and the next rule just becomes another tuple element.",
            "alternative": "Use heapq with (priority, index) and pop until it fits: O(k log n) when you drop only a "
                           "few messages. Or score messages with recency decay (priority - age * λ) for softer behaviour.",
        },
        {
            "title": "Truncate and split budget across docs",
            "minutes": 12,
            "prompt": code('''
                RAG adds retrieved docs. Add two functions (keep `fit_messages`):

                - `truncate(text, max_tokens, marker="[truncated]")`: unchanged if it fits; else first words + marker so the **result is `<= max_tokens`** tokens (marker counts). `max_tokens=0` gives `""`.
                - `allocate_docs(docs, budget) -> list[str]`: if all docs fit, return them as-is. Else give each doc `budget * tokens_i // total` tokens, truncate to that, and **drop** docs whose share is 0. Keep order.

                ```python
                truncate("a b c d e", 3)          # "a b [truncated]"
                allocate_docs([d10, d30], 20)     # shares 5 and 15
                ```
            '''),
            "tests": TB_S4_TESTS,
            "hints": [
                "Truncation is a word slice plus the marker. Budget for the marker's own tokens.",
                "keep = max_tokens - count_tokens(marker); ' '.join(words[:keep] + [marker]); return '' if keep < 0.",
                "In allocate_docs use integer math share = budget * cost // total, so the shares sum to <= budget; skip share == 0.",
            ],
            "solution": TB_S4,
            "lesson": "Make the truncation marker part of the budget, and use floor division for proportional "
                      "splits so rounding can never push you over. Always leave a visible marker: the model (and "
                      "the reader) should know text was cut.",
            "alternative": "Water-filling: give every doc min(need, fair share) and redistribute the leftovers from "
                           "small docs to big ones. It uses the budget fully but takes several passes. Or rank by "
                           "retrieval score and fill greedily, which keeps whole docs and drops the tail.",
        },
    ],
}


# ===========================================================================
# 4. Tool-call loop
# ===========================================================================

AG_S1 = code('''
    def final_text(response):
        return "".join(b["text"] for b in response["content"] if b["type"] == "text")


    def run_agent(client, user_text, tools):
        messages = [{"role": "user", "content": user_text}]
        while True:
            response = client.create(messages=messages)
            messages.append({"role": "assistant", "content": response["content"]})
            if response["stop_reason"] != "tool_use":
                return {"text": final_text(response),
                        "stop_reason": response["stop_reason"],
                        "messages": messages}
            results = []
            for block in response["content"]:
                if block["type"] == "tool_use":
                    output = tools[block["name"]](**block["input"])
                    results.append({"type": "tool_result",
                                    "tool_use_id": block["id"],
                                    "content": str(output)})
            messages.append({"role": "user", "content": results})
''')

AG_S1_TESTS = AGENT_FAKES + code('''
    def test_no_tools_returns_text():
        client = FakeClient([fake_response("end_turn", fake_text("Hello!"))])
        out = run_agent(client, "hi", {})
        assert out["text"] == "Hello!", f"final text should be 'Hello!', got {out!r}"
        assert out["stop_reason"] == "end_turn"
        assert client.calls[0] == [{"role": "user", "content": "hi"}], \\
            "first call: a single user message with the text"

    def test_runs_tool_and_sends_result():
        seen = []
        def get_weather(city):
            seen.append(city)
            return 18
        client = FakeClient([
            fake_response("tool_use", fake_text("Checking."),
                          fake_tool_use("tu_1", "get_weather", {"city": "Paris"})),
            fake_response("end_turn", fake_text("It's 18C.")),
        ])
        out = run_agent(client, "weather?", {"get_weather": get_weather})
        assert seen == ["Paris"], "tool should be called with **input"
        assert len(client.calls) == 2, "call the model again after running tools"
        second = client.calls[1]
        assert second[1]["role"] == "assistant" and second[1]["content"][1]["type"] == "tool_use", \\
            "append the assistant's full content (including tool_use) before the results"
        [r] = last_tool_results(client)
        assert r == {"type": "tool_result", "tool_use_id": "tu_1", "content": "18"}, \\
            f"tool_result block should echo the id and str(output), got {r}"
        assert out["text"] == "It's 18C."
        assert out["messages"][-1]["role"] == "assistant", "returned messages include the final reply"

    def test_multiple_rounds():
        client = FakeClient([
            fake_response("tool_use", fake_tool_use("a", "add", {"x": 1, "y": 2})),
            fake_response("tool_use", fake_tool_use("b", "add", {"x": 3, "y": 4})),
            fake_response("end_turn", fake_text("done")),
        ])
        out = run_agent(client, "go", {"add": lambda x, y: x + y})
        assert len(client.calls) == 3 and out["text"] == "done"
        assert last_tool_results(client, 2)[0]["content"] == "7", "second round result should be '7'"

    def test_max_tokens_stops():
        client = FakeClient([fake_response("max_tokens", fake_text("partial"))])
        out = run_agent(client, "long", {})
        assert out["stop_reason"] == "max_tokens" and out["text"] == "partial", \\
            "any stop_reason other than tool_use ends the loop and is reported"
''')

AG_S2 = code('''
    def final_text(response):
        return "".join(b["text"] for b in response["content"] if b["type"] == "text")


    def run_agent(client, user_text, tools, max_iterations=10):
        messages = [{"role": "user", "content": user_text}]
        for call in range(1, max_iterations + 1):
            response = client.create(messages=messages)
            messages.append({"role": "assistant", "content": response["content"]})
            if response["stop_reason"] != "tool_use":
                return {"text": final_text(response),
                        "stop_reason": response["stop_reason"],
                        "messages": messages}
            if call == max_iterations:
                break  # out of model calls: don't run tools nobody will read
            results = []
            for block in response["content"]:
                if block["type"] == "tool_use":
                    output = tools[block["name"]](**block["input"])
                    results.append({"type": "tool_result",
                                    "tool_use_id": block["id"],
                                    "content": str(output)})
            messages.append({"role": "user", "content": results})
        return {"text": final_text(response), "stop_reason": "max_iterations",
                "messages": messages}
''')

AG_S2_TESTS = AG_S1_TESTS + code('''
    def test_max_iterations_guard():
        pings = []
        client = LoopingClient()
        out = run_agent(client, "hi", {"ping": lambda: pings.append(1) or "pong"}, max_iterations=3)
        assert client.calls == 3, f"exactly 3 model calls allowed, got {client.calls}"
        assert out["stop_reason"] == "max_iterations", f"stop_reason should be 'max_iterations', got {out['stop_reason']!r}"
        assert len(pings) == 2, f"tools from the final, cut-off turn should not run; ran {len(pings)}"
        assert out["text"] == "again", "return the last response's text"

    def test_default_max_iterations_is_10():
        client = LoopingClient()
        out = run_agent(client, "hi", {"ping": lambda: "pong"})
        assert client.calls == 10 and out["stop_reason"] == "max_iterations", \\
            f"default max_iterations=10, got {client.calls} calls"

    def test_finishing_on_last_allowed_call_is_end_turn():
        client = FakeClient([
            fake_response("tool_use", fake_tool_use("a", "ping", {})),
            fake_response("end_turn", fake_text("ok")),
        ])
        out = run_agent(client, "hi", {"ping": lambda: "pong"}, max_iterations=2)
        assert out["stop_reason"] == "end_turn", "finishing within the limit is a normal end_turn"
''')

AG_RUN_TOOL_S3 = code('''
    def tool_result(block, content, is_error=False):
        result = {"type": "tool_result", "tool_use_id": block["id"], "content": content}
        if is_error:
            result["is_error"] = True
        return result


    def run_tool(tools, block):
        tool = tools.get(block["name"])
        if tool is None:
            return tool_result(block, f"Unknown tool: {block['name']}", is_error=True)
        try:
            return tool_result(block, str(tool(**block["input"])))
        except Exception as exc:  # the model sees the error and can recover
            return tool_result(block, f"{type(exc).__name__}: {exc}", is_error=True)
''')

AG_S3 = join(code('''
    def final_text(response):
        return "".join(b["text"] for b in response["content"] if b["type"] == "text")
'''), AG_RUN_TOOL_S3, code('''
    def run_agent(client, user_text, tools, max_iterations=10):
        messages = [{"role": "user", "content": user_text}]
        for call in range(1, max_iterations + 1):
            response = client.create(messages=messages)
            messages.append({"role": "assistant", "content": response["content"]})
            if response["stop_reason"] != "tool_use":
                return {"text": final_text(response),
                        "stop_reason": response["stop_reason"],
                        "messages": messages}
            if call == max_iterations:
                break
            results = [run_tool(tools, b) for b in response["content"] if b["type"] == "tool_use"]
            messages.append({"role": "user", "content": results})
        return {"text": final_text(response), "stop_reason": "max_iterations",
                "messages": messages}
'''))

AG_S3_TESTS = AG_S2_TESTS + code('''
    def test_unknown_tool_is_error_result():
        client = FakeClient([
            fake_response("tool_use", fake_tool_use("x1", "launch_rocket", {})),
            fake_response("end_turn", fake_text("Sorry, I can't.")),
        ])
        out = run_agent(client, "go", {})
        [r] = last_tool_results(client)
        assert r["tool_use_id"] == "x1" and r.get("is_error") is True, \\
            f"unknown tool -> tool_result with is_error=True, got {r}"
        assert "launch_rocket" in r["content"], "name the unknown tool so the model can correct itself"
        assert out["text"] == "Sorry, I can't.", "the loop continues after a tool error"

    def test_tool_exception_is_error_result():
        def divide(a, b):
            return a / b
        client = FakeClient([
            fake_response("tool_use", fake_tool_use("d1", "divide", {"a": 1, "b": 0})),
            fake_response("end_turn", fake_text("Can't divide by zero.")),
        ])
        run_agent(client, "1/0?", {"divide": divide})
        [r] = last_tool_results(client)
        assert r.get("is_error") is True, f"an exception inside a tool -> is_error=True, got {r}"
        assert "ZeroDivisionError" in r["content"] or "division" in r["content"], \\
            f"include the exception in content, got {r['content']!r}"

    def test_success_has_no_error_flag():
        client = FakeClient([
            fake_response("tool_use", fake_tool_use("e1", "echo", {"s": "hi"})),
            fake_response("end_turn", fake_text("ok")),
        ])
        run_agent(client, "x", {"echo": lambda s: s})
        [r] = last_tool_results(client)
        assert not r.get("is_error"), "successful results must not be flagged as errors"
''')

AG_S4 = code('''
    def final_text(response):
        return "".join(b["text"] for b in response["content"] if b["type"] == "text")


    def tool_result(block, content, is_error=False):
        result = {"type": "tool_result", "tool_use_id": block["id"], "content": content}
        if is_error:
            result["is_error"] = True
        return result


    def run_tool(tools, block, dangerous=(), approve=None):
        name, args = block["name"], block["input"]
        tool = tools.get(name)
        if tool is None:
            return tool_result(block, f"Unknown tool: {name}", is_error=True)
        if name in dangerous and not (approve is not None and approve(name, args)):
            return tool_result(block, f"Tool call denied by user: {name}", is_error=True)
        try:
            return tool_result(block, str(tool(**args)))
        except Exception as exc:
            return tool_result(block, f"{type(exc).__name__}: {exc}", is_error=True)


    def run_agent(client, user_text, tools, max_iterations=10, dangerous=(), approve=None):
        messages = [{"role": "user", "content": user_text}]
        for call in range(1, max_iterations + 1):
            response = client.create(messages=messages)
            messages.append({"role": "assistant", "content": response["content"]})
            if response["stop_reason"] != "tool_use":
                return {"text": final_text(response),
                        "stop_reason": response["stop_reason"],
                        "messages": messages}
            if call == max_iterations:
                break
            # Every tool_use block in this turn -> one tool_result each, same order,
            # all in ONE user message (the API rejects split or missing results).
            results = [run_tool(tools, b, dangerous, approve)
                       for b in response["content"] if b["type"] == "tool_use"]
            messages.append({"role": "user", "content": results})
        return {"text": final_text(response), "stop_reason": "max_iterations",
                "messages": messages}
''')

AG_S4_TESTS = AG_S3_TESTS + code('''
    def test_parallel_tool_uses_one_message_in_order():
        client = FakeClient([
            fake_response("tool_use", fake_text("Looking up both."),
                          fake_tool_use("p1", "price", {"sku": "A"}),
                          fake_tool_use("p2", "price", {"sku": "B"}),
                          fake_tool_use("p3", "nope", {})),
            fake_response("end_turn", fake_text("A=1, B=2")),
        ])
        run_agent(client, "prices", {"price": lambda sku: {"A": 1, "B": 2}[sku]})
        results = last_tool_results(client)
        assert [r["tool_use_id"] for r in results] == ["p1", "p2", "p3"], \\
            "one tool_result per tool_use, same order, all in a single user message"
        assert [r["content"] for r in results[:2]] == ["1", "2"]
        assert results[2].get("is_error") is True, "a bad call in a batch doesn't sink the others"

    def test_dangerous_tool_needs_approval():
        deleted, asked = [], []
        def approve(name, args):
            asked.append((name, args))
            return False
        client = FakeClient([
            fake_response("tool_use", fake_tool_use("d1", "delete_file", {"path": "/etc"})),
            fake_response("end_turn", fake_text("I wasn't allowed.")),
        ])
        run_agent(client, "clean up", {"delete_file": lambda path: deleted.append(path)},
                  dangerous={"delete_file"}, approve=approve)
        assert asked == [("delete_file", {"path": "/etc"})], f"approve(name, input) should be called, got {asked}"
        assert deleted == [], "a denied tool must NOT run"
        [r] = last_tool_results(client)
        assert r.get("is_error") is True and "denied" in r["content"].lower(), \\
            f"denial goes back as an is_error tool_result mentioning 'denied', got {r}"

    def test_approved_and_safe_tools_run():
        asked, ran = [], []
        client = FakeClient([
            fake_response("tool_use", fake_tool_use("s1", "send_email", {"to": "cfo"}),
                          fake_tool_use("s2", "lookup", {"q": "x"})),
            fake_response("end_turn", fake_text("sent")),
        ])
        tools = {"send_email": lambda to: ran.append(to) or "ok", "lookup": lambda q: "found"}
        run_agent(client, "email", tools, dangerous={"send_email"},
                  approve=lambda n, a: asked.append(n) or True)
        assert ran == ["cfo"], "an approved dangerous tool runs"
        assert asked == ["send_email"], f"only dangerous tools ask for approval, asked={asked}"
        assert [r["content"] for r in last_tool_results(client)] == ["ok", "found"]

    def test_dangerous_without_callback_is_denied():
        ran = []
        client = FakeClient([
            fake_response("tool_use", fake_tool_use("w1", "wire_money", {"amount": 10})),
            fake_response("end_turn", fake_text("blocked")),
        ])
        run_agent(client, "pay", {"wire_money": lambda amount: ran.append(amount)},
                  dangerous={"wire_money"})
        assert ran == [], "no approve callback -> fail closed: deny dangerous tools"
''')

AGENT = {
    "id": "fde-ch-tool-loop", "type": "challenge", "stage": "coding", "difficulty": 3,
    "tags": ["llm", "agents", "tool-use", "error-handling", "human-in-the-loop"],
    "pattern": "agent tool-use loop", "source": "S13",
    "title": "Tool-call loop for an LLM agent",
    "summary": "Write the core agent loop against a fake Messages-API client: run tool_use "
               "blocks and send tool_result blocks back until end_turn, then add an "
               "iteration guard, error results the model can recover from, parallel tool "
               "calls, and human approval for dangerous tools.",
    "talkPrompts": [
        "Name the message protocol: assistant content (with tool_use) first, then ONE user message of tool_results matching every id.",
        "Explain why tool errors go back to the model as is_error results instead of raising.",
        "Say why the loop needs max_iterations: cost, latency, and a model stuck in a loop.",
        "Explain fail-closed approval: no callback means deny, and the denial is reported to the model.",
        "Mention what you'd add for production: logging each tool call for audit, timeouts, running independent tools concurrently.",
    ],
    "steps": [
        {
            "title": "Run tools until end_turn",
            "minutes": 10,
            "prompt": code('''
                `client.create(messages=...)` returns a Messages-API-shaped dict:
                `{"stop_reason": "tool_use"|"end_turn"|"max_tokens", "content": [{"type": "text", "text": ...}, {"type": "tool_use", "id", "name", "input"}]}`.

                Write `run_agent(client, user_text, tools) -> dict`. `tools` maps name → function, called as `fn(**input)`.

                1. Start with `[{"role": "user", "content": user_text}]`.
                2. Call the model; append `{"role": "assistant", "content": response["content"]}`.
                3. If `stop_reason == "tool_use"`: run each tool_use block, then append one user message whose content is `[{"type": "tool_result", "tool_use_id": id, "content": str(output)}, ...]`. Repeat.
                4. Otherwise return `{"text": <joined text blocks>, "stop_reason": ..., "messages": messages}`.
            '''),
            "starter": code('''
                def run_agent(client, user_text, tools):
                    pass
            '''),
            "tests": AG_S1_TESTS,
            "hints": [
                "It's a while loop whose exit condition is the stop_reason.",
                "Always append the assistant message first; then build a list of tool_result blocks for the tool_use blocks.",
                "results.append({'type': 'tool_result', 'tool_use_id': block['id'], 'content': str(tools[block['name']](**block['input']))}).",
            ],
            "solution": AG_S1,
            "lesson": "The agent loop is a small state machine driven by stop_reason. Keep the transcript exactly "
                      "as the API expects: the assistant turn verbatim, then tool results that echo each tool_use id.",
            "alternative": "The Anthropic SDK's tool runner (or an agent framework) runs this loop for you. Writing it "
                           "by hand is what lets you add guards, approvals and logging. A generator that yields each "
                           "step lets a UI stream progress.",
        },
        {
            "title": "max_iterations guard",
            "minutes": 6,
            "prompt": code('''
                A confused model can call tools forever. Add `max_iterations=10`:

                - Make **at most** `max_iterations` model calls.
                - If the last allowed call still returns `tool_use`, **don't run** its tools; return `stop_reason: "max_iterations"` with that response's text.
                - Finishing within the limit returns its real stop_reason.

                ```python
                run_agent(looping_client, "hi", tools, max_iterations=3)
                # 3 model calls, tools ran twice, stop_reason "max_iterations"
                ```
            '''),
            "tests": AG_S2_TESTS,
            "hints": [
                "Replace while True with a bounded loop and handle the fall-through.",
                "for call in range(1, max_iterations + 1): ...; after the loop return stop_reason 'max_iterations'.",
                "Before running tools: if call == max_iterations: break, so the cut-off turn's tools don't run.",
            ],
            "solution": AG_S2,
            "lesson": "Every loop driven by an external system needs an explicit bound, and hitting it should give "
                      "a distinguishable result, not an exception or a silent hang. Don't do side-effecting work "
                      "whose result nobody will consume.",
            "alternative": "Bound by a token or cost budget (sum usage.output_tokens) or wall-clock deadline instead of "
                           "a call count; production agents often use several. Raising a custom exception is fine "
                           "too if callers prefer try/except.",
        },
        {
            "title": "Errors as tool results",
            "minutes": 8,
            "prompt": code('''
                Don't crash on bad tool calls. Send the error back so the model can recover:

                - Unknown tool name → `{"type": "tool_result", "tool_use_id": id, "content": "Unknown tool: <name>", "is_error": True}`.
                - Tool raises → same shape, `is_error: True`, content like `"ZeroDivisionError: division by zero"`.
                - Successful results have no `is_error` flag (or `False`).

                The loop then continues normally.
            '''),
            "tests": AG_S3_TESTS,
            "hints": [
                "Pull 'run one tool_use block' into its own function. That's where all the new rules live.",
                "run_tool(tools, block): tools.get(name) is None → error result; else try/except Exception around the call.",
                "Return f'{type(exc).__name__}: {exc}' with is_error=True; a tool_result(block, content, is_error=False) helper avoids repeating the dict.",
            ],
            "solution": AG_S3,
            "lesson": "Extract the per-item work (run_tool) before adding error handling, so the loop stays readable. "
                      "In agents, errors are data: an is_error result lets the model retry or apologise instead of "
                      "the whole request failing.",
            "alternative": "Validate input against each tool's JSON schema before calling (e.g. jsonschema) to return "
                           "precise 'missing field x' errors. Catching Exception (not BaseException) keeps Ctrl-C and "
                           "SystemExit working.",
        },
        {
            "title": "Parallel calls + approval for dangerous tools",
            "minutes": 10,
            "prompt": code('''
                The model may emit several `tool_use` blocks in one turn, and some tools need a human's OK.

                - Return **one** tool_result per tool_use, **same order**, all in a single user message. One failure doesn't affect the others.
                - `run_agent(..., dangerous=(), approve=None)`: for a tool whose name is in `dangerous`, call `approve(name, input)`. If it returns falsy (or `approve` is None), **don't run** the tool. Reply with an `is_error` result whose content contains `"denied"`.
                - Non-dangerous tools never ask.
            '''),
            "tests": AG_S4_TESTS,
            "hints": [
                "The approval check belongs in run_tool, between 'does the tool exist' and 'call it'.",
                "Pass dangerous and approve through run_agent to run_tool; denial returns tool_result(block, 'Tool call denied by user: ...', is_error=True).",
                "Fail closed: if name in dangerous and not (approve is not None and approve(name, args)): deny. Keep a list comprehension over tool_use blocks so order is preserved.",
            ],
            "solution": AG_S4,
            "lesson": "Put guardrails at the narrowest choke point (run_tool) and make them fail closed. Return "
                      "denials to the model as results so it can explain or choose another path. That's the "
                      "human-checkpoint pattern customers ask FDEs for.",
            "alternative": "Run independent tool calls concurrently with ThreadPoolExecutor.map or asyncio.gather. "
                           "Both preserve input order, so results still line up with tool_use ids. Approval can also "
                           "be a policy object (allowlist per user, or approve once per session) instead of a bare callback.",
        },
    ],
}


ITEMS = [LRU, RATE, TOKEN_BUDGET, AGENT]
