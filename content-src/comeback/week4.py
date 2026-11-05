from _helpers import code, lines

W = {"stage": "week4", "week": 4}

# Shared hidden-test scaffold for "write the test yourself" items: the learner's
# test function is run against a correct and several broken implementations.
def _test_your_test(fn_name, test_name, good, bads):
    """bads: list of (impl_name, message)."""
    checks = "\n".join(
        f"def test_catches_{name}():\n"
        f"    assert _run({name}) is False, {msg!r}\n"
        for name, msg in bads
    )
    return good + code(f'''
        {fn_name} = _good

        def _run(impl):
            """True if the learner's test passes with impl plugged in."""
            g = globals()
            assert "{test_name}" in g, "define a function called {test_name}()"
            g["{fn_name}"] = impl
            try:
                g["{test_name}"]()
                return True
            except Exception:
                return False
            finally:
                g["{fn_name}"] = _good

        def test_passes_on_correct_code():
            assert _run(_good) is True, "your test fails on a CORRECT implementation"
    ''') + checks


ITEMS = [
    # -------------------------------------------------------- small classes
    {
        **W, "id": "cb-w4-stack-class", "type": "code", "difficulty": 1,
        "tags": ["class", "dunder"], "pattern": "small class with invariants",
        "title": "A Stack class",
        "prompt": "Write class `Stack` with `push(x)`, `pop()`, `peek()`, `len(s)` support, and "
                  "make `pop()`/`peek()` on an empty stack raise `IndexError`.",
        "starter": code('''
            class Stack:
                pass
        '''),
        "tests": code('''
            def test_lifo():
                s = Stack()
                s.push(1); s.push(2)
                assert s.peek() == 2, "peek shows the top"
                assert s.pop() == 2 and s.pop() == 1, "LIFO order"
            def test_len():
                s = Stack()
                s.push("a")
                assert len(s) == 1, "implement __len__"
            def test_empty_raises():
                s = Stack()
                for op in (s.pop, s.peek):
                    try:
                        op()
                    except IndexError:
                        continue
                    assert False, f"{op.__name__}() on empty stack should raise IndexError"
            def test_instances_independent():
                a, b = Stack(), Stack()
                a.push(1)
                assert len(b) == 0, "each Stack needs its own list (set it in __init__)"
        '''),
        "hints": ["Store items in a list created in __init__ (not as a class attribute).",
                  "len(s) calls s.__len__(); list.pop() on empty already raises IndexError.",
                  "def peek(self): if not self._items: raise IndexError('peek from empty stack'); return self._items[-1]"],
        "solution": code('''
            class Stack:
                def __init__(self):
                    self._items = []

                def push(self, x):
                    self._items.append(x)

                def pop(self):
                    return self._items.pop()

                def peek(self):
                    if not self._items:
                        raise IndexError("peek from empty stack")
                    return self._items[-1]

                def __len__(self):
                    return len(self._items)
        '''),
        "lesson": "Per-instance state goes in __init__; a class-level `items = []` is shared by "
                  "every instance. Dunder methods (__len__) plug your class into built-ins.",
        "ts": "class Stack<T> { private items: T[] = []; get length() { return this.items.length; } }",
    },
    {
        **W, "id": "cb-w4-inventory", "type": "code", "difficulty": 2,
        "tags": ["class", "dict", "exceptions"], "pattern": "small class with invariants",
        "title": "Inventory",
        "prompt": "Write class `Inventory` with `add(item, qty)`, `remove(item, qty)` and "
                  "`count(item)` (0 if unknown). `remove` raises `ValueError` if there isn't enough "
                  "stock (and changes nothing); `qty` must be positive or `ValueError`.",
        "starter": code('''
            class Inventory:
                def __init__(self):
                    pass
        '''),
        "tests": code('''
            def test_add_count():
                inv = Inventory()
                inv.add("apple", 3); inv.add("apple", 2)
                assert inv.count("apple") == 5
                assert inv.count("pear") == 0, "unknown item -> 0"
            def test_remove():
                inv = Inventory()
                inv.add("apple", 3)
                inv.remove("apple", 3)
                assert inv.count("apple") == 0
            def test_not_enough():
                inv = Inventory()
                inv.add("apple", 1)
                try:
                    inv.remove("apple", 2)
                except ValueError:
                    assert inv.count("apple") == 1, "a failed remove must not change stock"
                    return
                assert False, "removing more than you have should raise ValueError"
            def test_bad_qty():
                inv = Inventory()
                try:
                    inv.add("apple", 0)
                except ValueError:
                    return
                assert False, "qty <= 0 should raise ValueError"
        '''),
        "hints": ["A dict item -> qty is all the state you need.",
                  "Validate first, mutate second — that's how 'changes nothing' stays true.",
                  "if qty <= 0: raise ValueError(...); if self._stock.get(item, 0) < qty: raise ValueError(...)"],
        "solution": code('''
            class Inventory:
                def __init__(self):
                    self._stock = {}

                def add(self, item, qty):
                    if qty <= 0:
                        raise ValueError("qty must be positive")
                    self._stock[item] = self._stock.get(item, 0) + qty

                def remove(self, item, qty):
                    if qty <= 0 or self.count(item) < qty:
                        raise ValueError(f"cannot remove {qty} {item}")
                    self._stock[item] -= qty

                def count(self, item):
                    return self._stock.get(item, 0)
        '''),
        "lesson": "Guard clauses at the top of a method (validate, raise) keep the object's "
                  "invariants intact: either the whole operation happens or nothing does.",
        "alternative": "collections.Counter as the store gives count() for free (missing keys → 0), "
                       "but it happily goes negative, so you still need the guard.",
    },
    {
        **W, "id": "cb-w4-custom-exception", "type": "code", "difficulty": 2,
        "tags": ["class", "exceptions"], "pattern": "custom exceptions",
        "title": "A custom exception with data",
        "prompt": "Define `InsufficientFunds(Exception)` carrying a `.shortfall` attribute, and class "
                  "`Account(balance)` whose `withdraw(amount)` raises it when `amount > balance` and "
                  "otherwise returns the new balance.",
        "starter": code('''
            class InsufficientFunds(Exception):
                pass

            class Account:
                def __init__(self, balance):
                    self.balance = balance
        '''),
        "tests": code('''
            def test_withdraw():
                a = Account(100)
                assert a.withdraw(30) == 70 and a.balance == 70
            def test_raises_with_shortfall():
                a = Account(10)
                try:
                    a.withdraw(25)
                except InsufficientFunds as e:
                    assert e.shortfall == 15, f"shortfall should be 15, got {e.shortfall}"
                    assert a.balance == 10, "balance unchanged on failure"
                    return
                assert False, "should raise InsufficientFunds"
            def test_is_exception():
                assert issubclass(InsufficientFunds, Exception)
            def test_message():
                try:
                    Account(0).withdraw(5)
                except InsufficientFunds as e:
                    assert "5" in str(e), "include the shortfall in the message"
        '''),
        "hints": ["Give the exception an __init__(self, shortfall).",
                  "Call super().__init__(message) so str(e) is useful.",
                  "self.shortfall = shortfall; super().__init__(f'short by {shortfall}')"],
        "solution": code('''
            class InsufficientFunds(Exception):
                def __init__(self, shortfall):
                    self.shortfall = shortfall
                    super().__init__(f"short by {shortfall}")

            class Account:
                def __init__(self, balance):
                    self.balance = balance

                def withdraw(self, amount):
                    if amount > self.balance:
                        raise InsufficientFunds(amount - self.balance)
                    self.balance -= amount
                    return self.balance
        '''),
        "lesson": "Domain exceptions let callers `except InsufficientFunds` precisely and read "
                  "structured data off the error instead of parsing a message string.",
        "ts": "class InsufficientFunds extends Error { constructor(public shortfall: number) { super(`short by ${shortfall}`); } }",
    },
    {
        **W, "id": "cb-w4-ttl-cache", "type": "code", "difficulty": 3,
        "tags": ["class", "dependency-injection", "time"], "pattern": "inject the clock",
        "title": "TTL dict with an injected clock",
        "prompt": "Write `TTLCache(ttl, clock=time.monotonic)` with `set(key, value)` and "
                  "`get(key, default=None)`. An entry expires once `ttl` seconds have passed "
                  "(at exactly `ttl` it's expired). Always read time via `self.clock()`.",
        "starter": code('''
            import time

            class TTLCache:
                def __init__(self, ttl, clock=time.monotonic):
                    pass
        '''),
        "tests": code('''
            class FakeClock:
                def __init__(self): self.now = 0.0
                def __call__(self): return self.now

            def test_fresh():
                clk = FakeClock()
                c = TTLCache(10, clock=clk)
                c.set("a", 1)
                clk.now = 9.9
                assert c.get("a") == 1, "still fresh at 9.9s"
            def test_expired():
                clk = FakeClock()
                c = TTLCache(10, clock=clk)
                c.set("a", 1)
                clk.now = 10
                assert c.get("a") is None, "expired at exactly ttl"
                assert c.get("a", "x") == "x", "default when expired"
            def test_reset_on_set():
                clk = FakeClock()
                c = TTLCache(5, clock=clk)
                c.set("a", 1); clk.now = 4; c.set("a", 2); clk.now = 8
                assert c.get("a") == 2, "set() restarts the timer"
            def test_missing():
                assert TTLCache(1, clock=FakeClock()).get("nope", 0) == 0
        '''),
        "hints": ["Store (value, expires_at) per key.",
                  "expires_at = self.clock() + self.ttl at set time.",
                  "in get: if key not in data or self.clock() >= expires_at: return default"],
        "solution": code('''
            import time

            class TTLCache:
                def __init__(self, ttl, clock=time.monotonic):
                    self.ttl, self.clock, self._data = ttl, clock, {}

                def set(self, key, value):
                    self._data[key] = (value, self.clock() + self.ttl)

                def get(self, key, default=None):
                    if key not in self._data:
                        return default
                    value, expires = self._data[key]
                    if self.clock() >= expires:
                        del self._data[key]
                        return default
                    return value
        '''),
        "lesson": "Anything time-dependent takes a `clock` parameter defaulting to the real one. "
                  "Tests pass a fake and move time instantly — no sleeps, no flakiness. Use "
                  "time.monotonic for durations, never time.time.",
        "alternative": "Store the insertion time and compare `now - t >= ttl`; equivalent, but "
                       "storing expires_at makes per-key TTLs trivial later.",
    },
    # ---------------------------------------------------- write your own tests
    {
        **W, "id": "cb-w4-write-test-slugify", "type": "code", "difficulty": 2,
        "tags": ["testing", "asserts"], "pattern": "write the test",
        "title": "Write the test: slugify",
        "prompt": "A function `slugify(title)` already exists (hidden). It should lowercase, trim "
                  "surrounding spaces, and join words with single hyphens: "
                  "`'  Hello   World '` → `'hello-world'`.\n\nWrite `test_slugify()` with plain "
                  "`assert`s. We'll run it against a correct version and some broken ones — it must "
                  "pass on the first and fail on every broken one.",
        "starter": code('''
            def test_slugify():
                pass
        '''),
        "tests": _test_your_test("slugify", "test_slugify", code('''
            def _good(s):
                return "-".join(s.lower().split())
            def _no_lower(s):
                return "-".join(s.split())
            def _no_collapse(s):
                return s.strip().lower().replace(" ", "-")
            def _no_trim(s):
                return s.lower().replace(" ", "-") if s.startswith(" ") or s.endswith(" ") else _good(s)
        '''), [("_no_lower", "a version that forgets to lowercase passed your test"),
               ("_no_collapse", "a version that turns '  ' into '--' passed your test"),
               ("_no_trim", "a version that keeps leading/trailing spaces passed your test")]),
        "hints": ["One assert per behaviour: lowercase, multiple spaces, leading/trailing spaces.",
                  "Give each assert a message so a failure tells you which behaviour broke.",
                  "assert slugify('Hello World') == 'hello-world', 'lowercases'; assert slugify('a   b') == 'a-b'; assert slugify('  a ') == 'a'"],
        "solution": code('''
            def test_slugify():
                assert slugify("Hello World") == "hello-world", "lowercases"
                assert slugify("a   b") == "a-b", "collapses runs of spaces"
                assert slugify("  a b ") == "a-b", "trims the ends"
        '''),
        "lesson": "A good test has one assert per behaviour from the spec, each with a message. "
                  "Ask 'what bug would slip through?' for every line of the spec.",
        "alternative": "pytest.mark.parametrize over (input, expected) pairs scales better; with plain "
                       "Python, loop over a list of cases and include the case in the message.",
    },
    {
        **W, "id": "cb-w4-write-test-raises", "type": "code", "difficulty": 2,
        "tags": ["testing", "exceptions"], "pattern": "write the test",
        "title": "Write the test: it must raise",
        "prompt": "`parse_price(s)` (hidden) turns `'$4.50'` into `4.5` and must raise `ValueError` "
                  "for junk like `'abc'` or `''`.\n\nWrite `test_parse_price()` — without pytest, so "
                  "check the exception with try/except. It must fail against versions that return "
                  "0 instead of raising.",
        "starter": code('''
            def test_parse_price():
                assert parse_price("$4.50") == 4.5
        '''),
        "tests": _test_your_test("parse_price", "test_parse_price", code('''
            def _good(s):
                s = s.strip().removeprefix("$")
                if not s:
                    raise ValueError("empty price")
                return float(s)
            def _zero_on_junk(s):
                try:
                    return _good(s)
                except ValueError:
                    return 0.0
            def _zero_on_empty(s):
                return 0.0 if not s.strip() else _good(s)
        '''), [("_zero_on_junk", "a version returning 0.0 for 'abc' passed your test"),
               ("_zero_on_empty", "a version returning 0.0 for '' passed your test")]),
        "hints": ["Call it inside try; if it returns normally, that's a failure.",
                  "After the call (still inside try), put `assert False, 'should have raised'`… but "
                  "careful: AssertionError isn't a ValueError, so it won't be swallowed.",
                  "for bad in ['abc', '']: try: parse_price(bad) except ValueError: continue; raise AssertionError(f'{bad!r} should raise')"],
        "solution": code('''
            def test_parse_price():
                assert parse_price("$4.50") == 4.5
                for bad in ["abc", ""]:
                    try:
                        parse_price(bad)
                    except ValueError:
                        continue
                    raise AssertionError(f"{bad!r} should raise ValueError")
        '''),
        "lesson": "Testing for an exception = try the call, `except` the expected type, and fail "
                  "loudly if no exception happened. Testing only the happy path misses half the spec.",
        "alternative": "With pytest: `with pytest.raises(ValueError): parse_price('abc')` — say it "
                       "out loud in an interview even if you write the manual version.",
        "ts": "expect(() => parsePrice('abc')).toThrow(RangeError)",
    },
    {
        **W, "id": "cb-w4-write-test-chunk", "type": "code", "difficulty": 2,
        "tags": ["testing", "edge-cases"], "pattern": "write the test",
        "title": "Write the test: edge cases for chunk",
        "prompt": "`chunk(xs, n)` (hidden) splits a list into lists of length `n`; the last one may "
                  "be shorter: `chunk([1,2,3,4,5], 2)` → `[[1,2],[3,4],[5]]`.\n\nWrite "
                  "`test_chunk()`. Broken versions mishandle the edges — think empty input, an exact "
                  "multiple, and a remainder.",
        "starter": code('''
            def test_chunk():
                pass
        '''),
        "tests": _test_your_test("chunk", "test_chunk", code('''
            def _good(xs, n):
                return [xs[i:i + n] for i in range(0, len(xs), n)]
            def _drops_tail(xs, n):
                return [xs[i:i + n] for i in range(0, len(xs) - n + 1, n)]
            def _empty_wrong(xs, n):
                return _good(xs, n) or [[]]
            def _extra_empty(xs, n):
                out = _good(xs, n)
                return out + [[]] if xs and len(xs) % n == 0 else out
        '''), [("_drops_tail", "a version that drops the short last chunk passed your test"),
               ("_empty_wrong", "a version returning [[]] for [] passed your test"),
               ("_extra_empty", "a version that appends an empty chunk on exact multiples passed your test")]),
        "hints": ["Bugs live at the boundaries. List them before writing asserts.",
                  "Three cases: [] -> [], [1,2,3,4] with n=2 (exact), [1,2,3] with n=2 (remainder).",
                  "assert chunk([], 3) == []; assert chunk([1,2,3,4], 2) == [[1,2],[3,4]]; assert chunk([1,2,3], 2) == [[1,2],[3]]"],
        "solution": code('''
            def test_chunk():
                assert chunk([], 3) == [], "empty input"
                assert chunk([1, 2, 3, 4], 2) == [[1, 2], [3, 4]], "exact multiple"
                assert chunk([1, 2, 3], 2) == [[1, 2], [3]], "remainder kept"
        '''),
        "lesson": "Edge-case checklist: empty, one element, exact fit, remainder, n bigger than the "
                  "input. Interviewers watch whether you test these unprompted.",
    },
    # ------------------------------------------------------- tracebacks
    {
        **W, "id": "cb-w4-tb-keyerror", "type": "code", "difficulty": 1,
        "tags": ["traceback", "dict"], "pattern": "read the traceback",
        "title": "Traceback: KeyError",
        "prompt": code('''
            Calling `tally(["a", "b", "a"])` crashes:

            ```
            Traceback (most recent call last):
              File "app.py", line 9, in <module>
                tally(["a", "b", "a"])
              File "app.py", line 4, in tally
                counts[w] += 1
            KeyError: 'a'
            ```
            Fix `tally` so it returns `{"a": 2, "b": 1}`.
        '''),
        "starter": code('''
            def tally(words):
                counts = {}
                for w in words:
                    counts[w] += 1
                return counts
        '''),
        "tests": code('''
            def test_tally():
                assert tally(["a", "b", "a"]) == {"a": 2, "b": 1}
            def test_empty():
                assert tally([]) == {}
        '''),
        "hints": ["Read the last line first: which key is missing, and why?",
                  "The first time you see a word there's nothing to add 1 to.",
                  "counts[w] = counts.get(w, 0) + 1"],
        "solution": code('''
            def tally(words):
                counts = {}
                for w in words:
                    counts[w] = counts.get(w, 0) + 1
                return counts
        '''),
        "lesson": "Read tracebacks bottom-up: exception type + message, then the deepest frame in "
                  "your code. KeyError on `d[k] += 1` means 'first time seeing k'.",
        "alternative": "defaultdict(int) or Counter(words) remove the problem entirely.",
    },
    {
        **W, "id": "cb-w4-tb-typeerror", "type": "code", "difficulty": 1,
        "tags": ["traceback", "strings"], "pattern": "read the traceback",
        "title": "Traceback: TypeError concatenating",
        "prompt": code('''
            ```
            Traceback (most recent call last):
              File "app.py", line 2, in label
                return "Order #" + order_id + " (" + qty + " items)"
            TypeError: can only concatenate str (not "int") to str
            ```
            `label(42, 3)` should return `'Order #42 (3 items)'`. Fix it.
        '''),
        "starter": code('''
            def label(order_id, qty):
                return "Order #" + order_id + " (" + qty + " items)"
        '''),
        "tests": code('''
            def test_label():
                assert label(42, 3) == "Order #42 (3 items)"
            def test_str_id():
                assert label("A7", 1) == "Order #A7 (1 items)"
        '''),
        "hints": ["Python never converts int to str implicitly (unlike JS).",
                  "An f-string converts each value for you.",
                  "return f\"Order #{order_id} ({qty} items)\""],
        "solution": code('''
            def label(order_id, qty):
                return f"Order #{order_id} ({qty} items)"
        '''),
        "lesson": "`str + int` is a TypeError in Python — no implicit coercion. Use f-strings for "
                  "any string built from values.",
        "ts": "In TS `'#' + 42` silently works; Python makes you be explicit.",
    },
    {
        **W, "id": "cb-w4-tb-none", "type": "code", "difficulty": 2,
        "tags": ["traceback", "regex", "None"], "pattern": "read the traceback",
        "title": "Traceback: 'NoneType' has no attribute",
        "prompt": code('''
            ```
            Traceback (most recent call last):
              File "app.py", line 5, in version_of
                return m.group(1)
            AttributeError: 'NoneType' object has no attribute 'group'
            ```
            `version_of("v1.2.3")` → `"1.2.3"` works, but a string with no version crashes.
            Make it return `None` instead.
        '''),
        "starter": code('''
            import re

            def version_of(s):
                m = re.search(r"v(\\d+\\.\\d+\\.\\d+)", s)
                return m.group(1)
        '''),
        "tests": code('''
            def test_found():
                assert version_of("release v1.2.3 final") == "1.2.3"
            def test_missing():
                assert version_of("no version here") is None, "return None when there's no match"
        '''),
        "hints": ["Which variable is None, and which function returned it?",
                  "re.search returns None when nothing matches.",
                  "return m.group(1) if m else None"],
        "solution": code('''
            import re

            def version_of(s):
                m = re.search(r"v(\\d+\\.\\d+\\.\\d+)", s)
                return m.group(1) if m else None
        '''),
        "lesson": "\"'NoneType' object has no attribute X\" means something upstream returned None. "
                  "Find what produced the variable — re.search, dict.get, a function missing a return.",
        "ts": "Like TS's `m?.[1] ?? null` — Python has no optional chaining, so check explicitly.",
    },
    {
        **W, "id": "cb-w4-tb-index", "type": "code", "difficulty": 1,
        "tags": ["traceback", "lists"], "pattern": "read the traceback",
        "title": "Traceback: IndexError in a loop",
        "prompt": code('''
            ```
            Traceback (most recent call last):
              File "app.py", line 4, in deltas
                out.append(xs[i + 1] - xs[i])
            IndexError: list index out of range
            ```
            `deltas([1, 4, 9])` should be `[3, 5]`. Fix it.
        '''),
        "starter": code('''
            def deltas(xs):
                out = []
                for i in range(len(xs)):
                    out.append(xs[i + 1] - xs[i])
                return out
        '''),
        "tests": code('''
            def test_basic():
                assert deltas([1, 4, 9]) == [3, 5]
            def test_short():
                assert deltas([7]) == [] and deltas([]) == []
        '''),
        "hints": ["On the last iteration, what is i + 1?",
                  "You need one fewer iteration — or pair neighbours directly.",
                  "return [b - a for a, b in zip(xs, xs[1:])]"],
        "solution": code('''
            def deltas(xs):
                return [b - a for a, b in zip(xs, xs[1:])]
        '''),
        "lesson": "zip(xs, xs[1:]) pairs neighbours and stops at the shorter list — no index "
                  "arithmetic, no off-by-one.",
        "alternative": "range(len(xs) - 1) fixes the loop with minimal change; itertools.pairwise(xs) "
                       "(3.10+) is the clearest.",
    },
    # ----------------------------------------------------------- async
    {
        **W, "id": "cb-w4-async-basics", "type": "code", "difficulty": 1,
        "tags": ["async"], "pattern": "async/await",
        "title": "Your first async function",
        "prompt": "`fetch(name)` is an async function (passed in). Write `async def greet_both(fetch)` "
                  "that awaits `fetch('a')` then `fetch('b')` and returns `'<a> & <b>'`.",
        "starter": code('''
            async def greet_both(fetch):
                pass
        '''),
        "tests": code('''
            import asyncio
            async def fake_fetch(name):
                await asyncio.sleep(0)
                return name.upper()
            async def test_greet():
                got = await greet_both(fake_fetch)
                assert got == "A & B", f"got {got!r}"
        '''),
        "hints": ["Calling an async function gives you a coroutine; you need its result.",
                  "Use `await` in front of each call.",
                  "a = await fetch('a'); b = await fetch('b'); return f'{a} & {b}'"],
        "solution": code('''
            async def greet_both(fetch):
                a = await fetch("a")
                b = await fetch("b")
                return f"{a} & {b}"
        '''),
        "lesson": "`async def` functions return coroutines; `await` runs one and gives its value. "
                  "Same mental model as TS Promises, but a coroutine does nothing until awaited.",
        "ts": "const a = await fetch('a'); — but in JS the request already started when you called fetch().",
    },
    {
        **W, "id": "cb-w4-async-gather", "type": "code", "difficulty": 2,
        "tags": ["async", "gather"], "pattern": "concurrent await (gather)",
        "title": "Fetch all concurrently",
        "prompt": "Write `async def fetch_all(urls, fetch)` that runs `fetch(url)` for every url "
                  "**concurrently** and returns results in the same order as `urls`.",
        "starter": code('''
            async def fetch_all(urls, fetch):
                return [await fetch(u) for u in urls]
        '''),
        "tests": code('''
            import asyncio
            log = []
            async def fake(u):
                log.append("start " + u)
                await asyncio.sleep(0)
                log.append("end " + u)
                return u * 2
            async def test_order():
                log.clear()
                assert await fetch_all(["a", "b"], fake) == ["aa", "bb"], "results in input order"
            async def test_concurrent():
                log.clear()
                await fetch_all(["a", "b", "c"], fake)
                assert log[:3] == ["start a", "start b", "start c"], \\
                    f"all fetches should start before any finishes; log was {log}"
            async def test_empty():
                assert await fetch_all([], fake) == []
        '''),
        "hints": ["The starter awaits one at a time — each finishes before the next starts.",
                  "asyncio.gather(*coroutines) runs them together and keeps order.",
                  "return list(await asyncio.gather(*(fetch(u) for u in urls)))"],
        "solution": code('''
            import asyncio

            async def fetch_all(urls, fetch):
                return list(await asyncio.gather(*(fetch(u) for u in urls)))
        '''),
        "lesson": "Sequential `await`s in a loop are serial. asyncio.gather starts them all and "
                  "returns results in argument order — Python's Promise.all.",
        "alternative": "asyncio.TaskGroup (3.11+) cancels siblings on the first error; gather with "
                       "return_exceptions=True collects errors instead of raising.",
        "ts": "await Promise.all(urls.map(fetch))",
    },
    {
        **W, "id": "cb-w4-async-timeout", "type": "code", "difficulty": 2,
        "tags": ["async", "timeouts"], "pattern": "timeouts",
        "title": "Give up after a timeout",
        "prompt": "Write `async def with_timeout(coro, seconds, default)` that returns the coroutine's "
                  "result, or `default` if it takes longer than `seconds`.",
        "starter": code('''
            async def with_timeout(coro, seconds, default):
                return await coro
        '''),
        "tests": code('''
            import asyncio
            async def slow():
                await asyncio.sleep(0.03)
                return "slow"
            async def fast():
                return "fast"
            async def test_fast():
                assert await with_timeout(fast(), 1, "x") == "fast"
            async def test_slow():
                got = await with_timeout(slow(), 0.001, "fallback")
                assert got == "fallback", f"should time out, got {got!r}"
        '''),
        "hints": ["asyncio has a helper that wraps an awaitable with a deadline.",
                  "asyncio.wait_for(coro, timeout) raises asyncio.TimeoutError when time runs out.",
                  "try: return await asyncio.wait_for(coro, seconds) except asyncio.TimeoutError: return default"],
        "solution": code('''
            import asyncio

            async def with_timeout(coro, seconds, default):
                try:
                    return await asyncio.wait_for(coro, seconds)
                except asyncio.TimeoutError:
                    return default
        '''),
        "lesson": "Every network call needs a timeout. asyncio.wait_for cancels the inner task and "
                  "raises TimeoutError (asyncio.TimeoutError is an alias in 3.11+).",
        "alternative": "`async with asyncio.timeout(seconds):` (3.11+) scopes a deadline over several awaits.",
    },
    {
        **W, "id": "cb-w4-async-semaphore", "type": "code", "difficulty": 3,
        "tags": ["async", "semaphore", "rate-limit"], "pattern": "bounded concurrency",
        "title": "At most N at a time",
        "prompt": "`jobs` is a list of zero-argument async functions. Write "
                  "`async def run_limited(jobs, limit)` that runs them concurrently but never more "
                  "than `limit` at once, returning results in order.",
        "starter": code('''
            import asyncio

            async def run_limited(jobs, limit):
                return await asyncio.gather(*(job() for job in jobs))
        '''),
        "tests": code('''
            import asyncio
            state = {"now": 0, "peak": 0}
            def make(i):
                async def job():
                    state["now"] += 1
                    state["peak"] = max(state["peak"], state["now"])
                    for _ in range(3):
                        await asyncio.sleep(0)
                    state["now"] -= 1
                    return i
                return job
            async def test_limit():
                state.update(now=0, peak=0)
                got = await run_limited([make(i) for i in range(6)], 2)
                assert got == [0, 1, 2, 3, 4, 5], f"results in order, got {got}"
                assert state["peak"] == 2, f"peak concurrency should be 2, was {state['peak']}"
        '''),
        "hints": ["asyncio.Semaphore(limit) lets only `limit` holders in at once.",
                  "Wrap each job in a helper that does `async with sem:` before awaiting it.",
                  "async def one(job): async with sem: return await job()  — then gather(*(one(j) for j in jobs))"],
        "solution": code('''
            import asyncio

            async def run_limited(jobs, limit):
                sem = asyncio.Semaphore(limit)

                async def one(job):
                    async with sem:
                        return await job()

                return list(await asyncio.gather(*(one(j) for j in jobs)))
        '''),
        "lesson": "Unbounded gather over 1,000 API calls will hit rate limits. A Semaphore inside "
                  "a small wrapper caps concurrency while gather still preserves order.",
        "alternative": "A fixed pool of `limit` worker coroutines pulling from an asyncio.Queue — "
                       "better for streaming work of unknown length.",
    },
    # --------------------------------------------------------------- HTTP
    {
        **W, "id": "cb-w4-http-status", "type": "code", "difficulty": 1,
        "tags": ["http", "dependency-injection"], "pattern": "check the status code",
        "title": "GET JSON and check the status",
        "prompt": "`get(url)` (injected) returns a response with `.status` and `.json()`. Write "
                  "`get_user(get, user_id)` that requests `https://api.example.com/users/<id>` and "
                  "returns the JSON on 200, `None` on 404, and raises `RuntimeError` otherwise.",
        "starter": code('''
            def get_user(get, user_id):
                return get(f"https://api.example.com/users/{user_id}").json()
        '''),
        "tests": code('''
            class Resp:
                def __init__(self, status, body=None):
                    self.status, self._body = status, body
                def json(self):
                    return self._body
            calls = []
            def make_get(status, body=None):
                def get(url):
                    calls.append(url)
                    return Resp(status, body)
                return get
            def test_ok():
                calls.clear()
                assert get_user(make_get(200, {"id": 7}), 7) == {"id": 7}
                assert calls == ["https://api.example.com/users/7"], f"wrong URL: {calls}"
            def test_404():
                assert get_user(make_get(404), 1) is None, "404 -> None"
            def test_500():
                try:
                    get_user(make_get(500), 1)
                except RuntimeError:
                    return
                assert False, "500 should raise RuntimeError"
        '''),
        "hints": ["Look at resp.status before touching resp.json().",
                  "Three branches: 200, 404, everything else.",
                  "if resp.status == 404: return None; if resp.status != 200: raise RuntimeError(f'HTTP {resp.status}')"],
        "solution": code('''
            def get_user(get, user_id):
                resp = get(f"https://api.example.com/users/{user_id}")
                if resp.status == 404:
                    return None
                if resp.status != 200:
                    raise RuntimeError(f"HTTP {resp.status}")
                return resp.json()
        '''),
        "lesson": "Inject the HTTP function so tests can hand in a fake — no network, instant, "
                  "deterministic. Always branch on status before parsing the body.",
        "ts": "const r = await fetch(url); if (r.status === 404) return null; if (!r.ok) throw new Error(...);",
    },
    {
        **W, "id": "cb-w4-http-query", "type": "code", "difficulty": 1,
        "tags": ["http", "urllib"], "pattern": "build URLs safely",
        "title": "Query params with urllib.parse",
        "prompt": "Write `build_url(base, params)` returning `base?query` with params URL-encoded "
                  "in order, skipping any whose value is `None`. No params left → just `base`.",
        "starter": code('''
            def build_url(base, params):
                return base + "?" + "&".join(f"{k}={v}" for k, v in params.items())
        '''),
        "tests": code('''
            def test_encoding():
                got = build_url("https://x.io/search", {"q": "a b&c", "limit": 10})
                assert got == "https://x.io/search?q=a+b%26c&limit=10", f"got {got}"
            def test_skip_none():
                got = build_url("https://x.io/s", {"q": "hi", "cursor": None})
                assert got == "https://x.io/s?q=hi", f"got {got}"
            def test_no_params():
                assert build_url("https://x.io/s", {"cursor": None}) == "https://x.io/s"
        '''),
        "hints": ["Spaces and & must be escaped, or the server mis-parses the query.",
                  "urllib.parse.urlencode(dict) does the escaping.",
                  "clean = {k: v for k, v in params.items() if v is not None}; return f'{base}?{urlencode(clean)}' if clean else base"],
        "solution": code('''
            from urllib.parse import urlencode

            def build_url(base, params):
                clean = {k: v for k, v in params.items() if v is not None}
                return f"{base}?{urlencode(clean)}" if clean else base
        '''),
        "lesson": "Never glue query strings by hand: urlencode escapes spaces, &, = and unicode. "
                  "Filtering None first is the usual 'optional param' idiom.",
        "ts": "new URLSearchParams(params).toString()",
    },
    {
        **W, "id": "cb-w4-http-retry", "type": "code", "difficulty": 3,
        "tags": ["http", "retry", "backoff"], "pattern": "retry with backoff",
        "title": "Retry 429/5xx with exponential backoff",
        "prompt": "Write `fetch(get, url, attempts=3, sleep=time.sleep)`. Retry when status is 429 or "
                  "≥ 500, sleeping `0.5, 1, 2, …` seconds between tries. Return the response for any "
                  "other status. Raise `RuntimeError` when attempts run out.",
        "starter": code('''
            import time

            def fetch(get, url, attempts=3, sleep=time.sleep):
                return get(url)
        '''),
        "tests": code('''
            class Resp:
                def __init__(self, status): self.status = status
            def scripted(*statuses):
                seq = list(statuses)
                return lambda url: Resp(seq.pop(0))
            def test_retries_then_ok():
                naps = []
                r = fetch(scripted(503, 429, 200), "u", sleep=naps.append)
                assert r.status == 200
                assert naps == [0.5, 1.0], f"backoff should be 0.5 then 1.0, got {naps}"
            def test_no_retry_on_4xx():
                naps = []
                assert fetch(scripted(404), "u", sleep=naps.append).status == 404
                assert naps == [], "404 is not retryable"
            def test_gives_up():
                naps = []
                try:
                    fetch(scripted(500, 500, 500), "u", sleep=naps.append)
                except RuntimeError:
                    assert naps == [0.5, 1.0], f"no sleep after the last attempt, got {naps}"
                    return
                assert False, "should raise after 3 failed attempts"
        '''),
        "hints": ["Loop `for i in range(attempts)`; decide per response: return, or retry.",
                  "Delay is 0.5 * 2 ** i; skip the sleep after the final attempt.",
                  "if not (r.status == 429 or r.status >= 500): return r; if i < attempts - 1: sleep(0.5 * 2 ** i)"],
        "solution": code('''
            import time

            def fetch(get, url, attempts=3, sleep=time.sleep):
                for i in range(attempts):
                    r = get(url)
                    if not (r.status == 429 or r.status >= 500):
                        return r
                    if i < attempts - 1:
                        sleep(0.5 * 2 ** i)
                raise RuntimeError(f"gave up after {attempts} attempts: {r.status}")
        '''),
        "lesson": "Retry only what can succeed later (429, 5xx, timeouts) — never 4xx client errors. "
                  "Exponential backoff + injected sleep makes the policy testable in microseconds.",
        "alternative": "Add jitter (random.uniform(0, delay)) to avoid thundering herds, and honour a "
                       "Retry-After header on 429 when present.",
    },
    {
        **W, "id": "cb-w4-http-timeout", "type": "code", "difficulty": 2,
        "tags": ["http", "timeouts"], "pattern": "timeouts",
        "title": "Always pass a timeout",
        "prompt": "`get(url, timeout)` may raise `TimeoutError`. Write `get_or_none(get, url)`: call it "
                  "with `timeout=2`, retry once on `TimeoutError`, and return `None` if the second "
                  "try also times out. Other errors should propagate.",
        "starter": code('''
            def get_or_none(get, url):
                return get(url)
        '''),
        "tests": code('''
            def flaky(*outcomes):
                seq, seen = list(outcomes), []
                def get(url, timeout=None):
                    seen.append(timeout)
                    o = seq.pop(0)
                    if isinstance(o, Exception):
                        raise o
                    return o
                get.seen = seen
                return get
            def test_ok():
                g = flaky("body")
                assert get_or_none(g, "u") == "body"
                assert g.seen == [2], "pass timeout=2"
            def test_retry_once():
                g = flaky(TimeoutError(), "body")
                assert get_or_none(g, "u") == "body"
            def test_gives_up():
                assert get_or_none(flaky(TimeoutError(), TimeoutError()), "u") is None
            def test_other_errors():
                try:
                    get_or_none(flaky(ValueError("bad")), "u")
                except ValueError:
                    return
                assert False, "only TimeoutError should be caught"
        '''),
        "hints": ["Two attempts → a tiny loop.",
                  "Catch only TimeoutError; anything else should bubble up.",
                  "for _ in range(2): try: return get(url, timeout=2) except TimeoutError: pass; return None"],
        "solution": code('''
            def get_or_none(get, url):
                for _ in range(2):
                    try:
                        return get(url, timeout=2)
                    except TimeoutError:
                        pass
                return None
        '''),
        "lesson": "Default HTTP clients often wait forever; always set a timeout. Catch the narrowest "
                  "exception you can handle — a bare `except` would hide real bugs.",
        "ts": "fetch(url, { signal: AbortSignal.timeout(2000) })",
    },
    {
        **W, "id": "cb-w4-http-paginate", "type": "code", "difficulty": 2,
        "tags": ["http", "pagination", "generators"], "pattern": "pagination",
        "title": "Follow the next cursor",
        "prompt": "Each page from `get(url).json()` looks like `{\"items\": [...], \"next\": url_or_None}`. "
                  "Write `collect(get, url, max_pages=10)` returning all items across pages, "
                  "stopping at `next is None` or after `max_pages` pages.",
        "starter": code('''
            def collect(get, url, max_pages=10):
                return get(url).json()["items"]
        '''),
        "tests": code('''
            class Resp:
                def __init__(self, body): self.body = body
                def json(self): return self.body
            PAGES = {"p1": {"items": [1, 2], "next": "p2"},
                     "p2": {"items": [3], "next": "p3"},
                     "p3": {"items": [], "next": None}}
            def test_all():
                assert collect(lambda u: Resp(PAGES[u]), "p1") == [1, 2, 3]
            def test_cap():
                loop = lambda u: Resp({"items": [u], "next": u})
                assert collect(loop, "x", max_pages=3) == ["x", "x", "x"], "stop after max_pages"
        '''),
        "hints": ["Loop while you have a URL and haven't hit the page cap.",
                  "items.extend(page['items']); url = page['next']",
                  "for _ in range(max_pages): if url is None: break; page = get(url).json(); ..."],
        "solution": code('''
            def collect(get, url, max_pages=10):
                items = []
                for _ in range(max_pages):
                    if url is None:
                        break
                    page = get(url).json()
                    items.extend(page["items"])
                    url = page["next"]
                return items
        '''),
        "lesson": "Cursor pagination: loop on the 'next' pointer. Always cap pages — a buggy API "
                  "that returns the same cursor would otherwise loop forever.",
        "alternative": "Make it a generator (`yield from page['items']`) so callers can stop early "
                       "and memory stays flat.",
    },
    # ------------------------------------------------------- LLM JSON
    {
        **W, "id": "cb-w4-json-fences", "type": "code", "difficulty": 1,
        "tags": ["llm", "json", "strings"], "pattern": "parse LLM output",
        "title": "Strip ```json fences",
        "prompt": "Models often wrap JSON in markdown fences. Write `strip_fences(text)` that removes "
                  "a leading ```` ``` ```` or ```` ```json ```` line and a trailing ```` ``` ````, plus "
                  "surrounding whitespace. Unfenced text is returned stripped.",
        "starter": code('''
            def strip_fences(text):
                return text
        '''),
        "tests": code('''
            def test_json_fence():
                assert strip_fences('```json\\n{"a": 1}\\n```') == '{"a": 1}'
            def test_plain_fence():
                assert strip_fences('```\\n[1]\\n```\\n') == "[1]"
            def test_no_fence():
                assert strip_fences('  {"a": 1} ') == '{"a": 1}'
            def test_inner_text_kept():
                assert strip_fences('```json\\n{"lang": "json"}\\n```') == '{"lang": "json"}', \\
                    "only remove the fence, not the word json elsewhere"
        '''),
        "hints": ["Strip whitespace first, then look at the start and end.",
                  "str.removeprefix / removesuffix remove an exact string once (3.9+).",
                  "t = text.strip(); if t.startswith('```'): t = t.split('\\n', 1)[1] if '\\n' in t else ''; t = t.removesuffix('```')"],
        "solution": code('''
            def strip_fences(text):
                t = text.strip()
                if t.startswith("```"):
                    t = t.split("\\n", 1)[1] if "\\n" in t else ""
                    t = t.removesuffix("```")
                return t.strip()
        '''),
        "lesson": "Drop the whole first fence line (it may say ```json, ```JSON or ```) rather than "
                  "a fixed prefix. Never use str.strip('```json') — it strips *characters*, not a prefix.",
        "alternative": "re.sub(r'^```\\w*\\n|\\n?```$', '', t.strip()) — compact, harder to read.",
    },
    {
        **W, "id": "cb-w4-json-safe", "type": "code", "difficulty": 1,
        "tags": ["llm", "json", "exceptions"], "pattern": "parse LLM output",
        "title": "json.loads with a fallback",
        "prompt": "Write `safe_loads(text, default=None)` returning the parsed JSON, or `default` if "
                  "the text isn't valid JSON. Catch only the JSON error — passing a non-string should "
                  "still raise.",
        "starter": code('''
            import json

            def safe_loads(text, default=None):
                return json.loads(text)
        '''),
        "tests": code('''
            def test_ok():
                assert safe_loads('{"a": [1, 2]}') == {"a": [1, 2]}
            def test_bad():
                assert safe_loads("{'a': 1}") is None, "single quotes aren't JSON"
                assert safe_loads("Sure! Here you go", {}) == {}, "default"
            def test_narrow_except():
                try:
                    safe_loads(None)
                except TypeError:
                    return
                assert False, "json.loads(None) raises TypeError — don't swallow it"
        '''),
        "hints": ["json has its own exception class for parse errors.",
                  "json.JSONDecodeError is a subclass of ValueError.",
                  "try: return json.loads(text) except json.JSONDecodeError: return default"],
        "solution": code('''
            import json

            def safe_loads(text, default=None):
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return default
        '''),
        "lesson": "LLM output is untrusted input: parse it inside try/except json.JSONDecodeError "
                  "and decide the fallback explicitly. A bare except hides your own bugs (TypeError).",
        "ts": "try { return JSON.parse(text) } catch (e) { if (e instanceof SyntaxError) return fallback; throw e }",
    },
    {
        **W, "id": "cb-w4-json-validate", "type": "code", "difficulty": 2,
        "tags": ["llm", "json", "validation", "isinstance"], "pattern": "validate external data",
        "title": "Validate required keys and types",
        "prompt": "Write `check(obj)` returning a list of error strings (empty = valid). `obj` must be "
                  "a dict with `name` (str) and `age` (int, **not** bool). Report missing keys as "
                  "`'missing name'` and wrong types as `'age must be int'`.",
        "starter": code('''
            def check(obj):
                return []
        '''),
        "tests": code('''
            def test_valid():
                assert check({"name": "Ada", "age": 36}) == []
            def test_missing():
                assert check({"age": 3}) == ["missing name"]
            def test_type():
                assert check({"name": "Bo", "age": "3"}) == ["age must be int"]
            def test_bool_is_not_int():
                assert check({"name": "Bo", "age": True}) == ["age must be int"], \\
                    "isinstance(True, int) is True — exclude bool explicitly"
            def test_not_dict():
                assert check([1]) == ["expected an object"]
        '''),
        "hints": ["Check isinstance(obj, dict) first and bail out early.",
                  "Loop over a schema dict like {'name': str, 'age': int}.",
                  "if k not in obj: errs.append(f'missing {k}') elif not isinstance(v, t) or isinstance(v, bool): errs.append(f'{k} must be {t.__name__}')"],
        "solution": code('''
            SCHEMA = {"name": str, "age": int}

            def check(obj):
                if not isinstance(obj, dict):
                    return ["expected an object"]
                errs = []
                for key, typ in SCHEMA.items():
                    if key not in obj:
                        errs.append(f"missing {key}")
                    elif not isinstance(obj[key], typ) or isinstance(obj[key], bool):
                        errs.append(f"{key} must be {typ.__name__}")
                return errs
        '''),
        "lesson": "Validate model output against a small schema and return *all* errors — you can "
                  "feed them back to the model in a retry prompt. Watch out: bool is a subclass of int.",
        "alternative": "pydantic / jsonschema do this declaratively in production; in an interview, "
                       "a schema dict + isinstance shows you understand what they do.",
    },
    {
        **W, "id": "cb-w4-json-extract", "type": "code", "difficulty": 3,
        "tags": ["llm", "json"], "pattern": "parse LLM output",
        "title": "Extract the first JSON object from prose",
        "prompt": "Write `first_json(text)` returning the first valid JSON object (`{...}`) embedded in "
                  "chatty text, or `None`. Braces in a broken fragment before it shouldn't stop you.",
        "starter": code('''
            import json

            def first_json(text):
                return json.loads(text)
        '''),
        "tests": code('''
            def test_prose():
                t = 'Sure! Here is the result: {"ok": true, "n": 2} Let me know.'
                assert first_json(t) == {"ok": True, "n": 2}
            def test_nested():
                assert first_json('x {"a": {"b": [1, {"c": 2}]}} y') == {"a": {"b": [1, {"c": 2}]}}
            def test_skip_broken():
                assert first_json('use {braces} like {"a": 1}') == {"a": 1}
            def test_none():
                assert first_json("no json here") is None
        '''),
        "hints": ["Regex can't match nested braces. Let the JSON parser find the end for you.",
                  "json.JSONDecoder().raw_decode(text, i) parses from index i and returns (obj, end).",
                  "for i, ch in enumerate(text): if ch == '{': try: return dec.raw_decode(text, i)[0] except json.JSONDecodeError: continue"],
        "solution": code('''
            import json

            def first_json(text):
                dec = json.JSONDecoder()
                for i, ch in enumerate(text):
                    if ch == "{":
                        try:
                            return dec.raw_decode(text, i)[0]
                        except json.JSONDecodeError:
                            continue
                return None
        '''),
        "lesson": "raw_decode parses a JSON value starting at an index and ignores trailing text — "
                  "the robust way to pull JSON out of prose without fragile regexes.",
        "alternative": "text[text.find('{'):text.rfind('}')+1] works for one object with no stray "
                       "braces; better still, ask the API for structured output / tool use.",
    },
    # ------------------------------------------------------------ predict
    {
        **W, "id": "cb-w4-predict-json-quotes", "type": "predict", "kind": "output", "difficulty": 1,
        "tags": ["json", "llm"], "pattern": "parse LLM output",
        "code": code('''
            import json
            try:
                print(json.loads("{'a': 1}")["a"])
            except json.JSONDecodeError:
                print("invalid")
        '''),
        "question": "What does this print?",
        "choices": ["1", "invalid", "KeyError", "{'a': 1}"],
        "answer": 1,
        "explanation": "JSON requires double quotes. Models sometimes emit Python-style dicts — "
                       "json.loads rejects them with JSONDecodeError.",
    },
    {
        **W, "id": "cb-w4-predict-finally", "type": "predict", "kind": "output", "difficulty": 2,
        "tags": ["exceptions"], "pattern": "try/finally",
        "code": code('''
            def f():
                try:
                    return "try"
                finally:
                    print("finally", end=" ")
            print(f())
        '''),
        "question": "What does this print?",
        "choices": ["try", "try finally", "finally try", "finally"],
        "answer": 2,
        "explanation": "finally runs before the function actually returns, so its print happens first; "
                       "then the outer print shows the returned 'try'. That's why cleanup goes in finally.",
    },
    {
        **W, "id": "cb-w4-predict-coroutine", "type": "predict", "kind": "output", "difficulty": 1,
        "tags": ["async"], "pattern": "async/await",
        "code": code('''
            async def get():
                return 42
            x = get()
            print(type(x).__name__)
            x.close()
        '''),
        "question": "What does this print?",
        "choices": ["42", "int", "coroutine", "None"],
        "answer": 2,
        "explanation": "Calling an async function doesn't run it; it returns a coroutine object. Forgetting "
                       "`await` is the #1 async bug (Python warns 'coroutine was never awaited').",
    },
    {
        **W, "id": "cb-w4-predict-bool-int", "type": "predict", "kind": "output", "difficulty": 2,
        "tags": ["isinstance", "validation"], "pattern": "validate external data",
        "code": code('''
            data = {"count": True}
            print(isinstance(data["count"], int))
        '''),
        "question": "What does this print?",
        "choices": ["True", "False", "TypeError"],
        "answer": 0,
        "explanation": "bool is a subclass of int, so a model returning `true` for a count passes an "
                       "isinstance(int) check. Exclude bool explicitly when validating.",
    },
    {
        **W, "id": "cb-w4-predict-serial-await", "type": "predict", "kind": "concept", "difficulty": 2,
        "tags": ["async", "gather"], "pattern": "concurrent await (gather)",
        "code": code('''
            a = await call_api("a")   # takes ~1 s
            b = await call_api("b")   # takes ~1 s
        '''),
        "question": "Roughly how long does this take, and how long with asyncio.gather?",
        "choices": ["1 s; gather 1 s", "2 s; gather 1 s", "2 s; gather 2 s", "1 s; gather 0.5 s"],
        "answer": 1,
        "explanation": "Each await waits for completion before the next line starts: 2 s. "
                       "gather(call_api('a'), call_api('b')) overlaps the waits: ~1 s.",
        "ts": "Same as two sequential awaits vs Promise.all in TS.",
    },
    {
        **W, "id": "cb-w4-predict-traceback-read", "type": "predict", "kind": "concept", "difficulty": 1,
        "tags": ["traceback", "debugging"], "pattern": "read the traceback",
        "question": "A 40-line traceback goes through requests, urllib3 and your code. Where do you look first?",
        "choices": ["The first line — it's where the program started",
                    "The last line (exception + message), then the deepest frame in YOUR code",
                    "The frame inside the library — that's where it crashed",
                    "Ignore it and add print statements"],
        "answer": 1,
        "explanation": "Python prints most-recent-call-last. The bottom line says what went wrong; walk up "
                       "to the last frame in your own files to see what you passed in.",
    },
    # --------------------------------------------------------------- bugs
    {
        **W, "id": "cb-w4-bug-retry-404", "type": "bug", "difficulty": 2,
        "tags": ["http", "retry"], "pattern": "retry with backoff",
        "title": "Retrying a 404",
        "code": code('''
            def fetch(get, url, attempts=3):
                for _ in range(attempts):
                    resp = get(url)
                    if resp.status >= 400:
                        continue
                    return resp
                raise RuntimeError("gave up")
        '''),
        "bugLine": 4,
        "fixed": code('''
            def fetch(get, url, attempts=3):
                for _ in range(attempts):
                    resp = get(url)
                    if resp.status == 429 or resp.status >= 500:
                        continue
                    return resp
                raise RuntimeError("gave up")
        '''),
        "tests": code('''
            class Resp:
                def __init__(self, s): self.status = s
            def test_404_not_retried():
                calls = []
                def get(url):
                    calls.append(url)
                    return Resp(404)
                assert fetch(get, "u").status == 404, "return the 404 to the caller"
                assert len(calls) == 1, f"404 should not be retried, called {len(calls)}x"
            def test_503_retried():
                seq = [503, 200]
                assert fetch(lambda u: Resp(seq.pop(0)), "u").status == 200
        '''),
        "choices": ["Retry only 429 and 5xx",
                    "Increase attempts to 5",
                    "Use `>` instead of `>=`",
                    "Move `return resp` above the if"],
        "answer": 0,
        "explanation": "4xx means the request itself is wrong (not found, bad auth) — repeating it can't "
                       "help and wastes rate limit. Only 429 and 5xx are transient.",
    },
    {
        **W, "id": "cb-w4-bug-missing-await", "type": "bug", "difficulty": 1,
        "tags": ["async"], "pattern": "async/await",
        "title": "Adding coroutines",
        "code": code('''
            import asyncio

            async def double(x):
                await asyncio.sleep(0)
                return x * 2

            async def total(xs):
                s = 0
                for x in xs:
                    s += double(x)
                return s
        '''),
        "bugLine": 10,
        "fixed": code('''
            import asyncio

            async def double(x):
                await asyncio.sleep(0)
                return x * 2

            async def total(xs):
                s = 0
                for x in xs:
                    s += await double(x)
                return s
        '''),
        "tests": code('''
            async def test_total():
                assert await total([1, 2, 3]) == 12
        '''),
        "choices": ["Add `await` before double(x)",
                    "Make total a normal def",
                    "Use asyncio.run(double(x)) inside the loop",
                    "Initialise s = 0.0"],
        "answer": 0,
        "explanation": "double(x) returns a coroutine; `0 + coroutine` is a TypeError. Await it to get "
                       "the number. (asyncio.run can't be called from inside a running loop.)",
    },
    {
        **W, "id": "cb-w4-bug-mutable-default", "type": "bug", "difficulty": 2,
        "tags": ["class", "defaults"], "pattern": "small class with invariants",
        "title": "Carts that share items",
        "code": code('''
            class Cart:
                def __init__(self, items=[]):
                    self.items = items

                def add(self, item):
                    self.items.append(item)
        '''),
        "bugLine": 2,
        "fixed": code('''
            class Cart:
                def __init__(self, items=None):
                    self.items = [] if items is None else items

                def add(self, item):
                    self.items.append(item)
        '''),
        "tests": code('''
            def test_independent():
                a, b = Cart(), Cart()
                a.add("apple")
                assert b.items == [], f"b should be empty, has {b.items}"
            def test_given_items():
                assert Cart(["x"]).items == ["x"]
        '''),
        "choices": ["Default to None and create a new list inside __init__",
                    "Make items a class attribute",
                    "Use self.items += [item] in add",
                    "Call super().__init__()"],
        "answer": 0,
        "explanation": "Default values are evaluated once, when the def runs — every Cart() shares the "
                       "same list. Use None as the sentinel and build a fresh list per call.",
    },
    # ------------------------------------------------------------- parsons
    {
        **W, "id": "cb-w4-parsons-gather", "type": "parsons", "difficulty": 2,
        "tags": ["async", "gather", "timeouts"], "pattern": "concurrent await (gather)",
        "title": "Gather, tolerating timeouts",
        "prompt": "Arrange the lines so `fetch_all` fetches every url concurrently, using `None` for "
                  "any that time out.",
        "lines": lines('''
            import asyncio
            async def fetch_all(urls, fetch):
                async def one(u):
                    try:
                        return await fetch(u)
                    except TimeoutError:
                        return None
                return await asyncio.gather(*(one(u) for u in urls))
        '''),
        "tests": code('''
            import asyncio
            async def fake(u):
                await asyncio.sleep(0)
                if u == "slow":
                    raise TimeoutError()
                return u.upper()
            async def test_mixed():
                got = await fetch_all(["a", "slow", "b"], fake)
                assert list(got) == ["A", None, "B"], f"got {got}"
        '''),
        "lesson": "Wrap each task in a small inner coroutine that handles its own errors; gather "
                  "then never blows up because of one bad url.",
    },
    {
        **W, "id": "cb-w4-parsons-parse", "type": "parsons", "difficulty": 1,
        "tags": ["json", "llm"], "pattern": "parse LLM output",
        "title": "Parse model JSON with a fallback",
        "prompt": "Arrange the lines so `parse` removes a ```json fence and returns the parsed value, "
                  "or `default` on invalid JSON.",
        "lines": lines('''
            import json
            def parse(text, default=None):
                text = text.strip().removeprefix("```json").removesuffix("```")
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return default
        '''),
        "tests": code('''
            def test_fenced():
                assert parse('```json\\n{"a": 1}\\n```') == {"a": 1}
            def test_bad():
                assert parse("nope", {}) == {}
        '''),
        "lesson": "Normalise, then parse inside a narrow try/except — the two-step shape of every "
                  "LLM-output parser.",
    },
    # ------------------------------------------------------------- handoff
    {
        **W, "id": "cb-w4-handoff-lru", "type": "code", "difficulty": 3,
        "tags": ["handoff", "OrderedDict", "class", "cache"], "pattern": "LRU cache",
        "title": "Handoff: tiny LRU cache",
        "prompt": "Write `LRUCache(capacity)` with `get(key)` (returns `-1` if missing) and "
                  "`put(key, value)`. Both count as a 'use'; when over capacity, evict the least "
                  "recently used key. O(1) per operation.",
        "starter": code('''
            class LRUCache:
                def __init__(self, capacity):
                    self.capacity = capacity
        '''),
        "tests": code('''
            def test_evicts_lru():
                c = LRUCache(2)
                c.put("a", 1); c.put("b", 2)
                assert c.get("a") == 1, "a is now most recent"
                c.put("c", 3)
                assert c.get("b") == -1, "b was least recently used -> evicted"
                assert c.get("a") == 1 and c.get("c") == 3
            def test_update_counts_as_use():
                c = LRUCache(2)
                c.put("a", 1); c.put("b", 2); c.put("a", 10); c.put("c", 3)
                assert c.get("a") == 10, "updating a refreshes it"
                assert c.get("b") == -1
            def test_missing():
                assert LRUCache(1).get("x") == -1
        '''),
        "hints": ["collections.OrderedDict remembers order and can move a key to the end in O(1).",
                  "On every use: self.data.move_to_end(key). Oldest is at the front.",
                  "if len(self.data) > self.capacity: self.data.popitem(last=False)"],
        "solution": code('''
            from collections import OrderedDict

            class LRUCache:
                def __init__(self, capacity):
                    self.capacity = capacity
                    self.data = OrderedDict()

                def get(self, key):
                    if key not in self.data:
                        return -1
                    self.data.move_to_end(key)
                    return self.data[key]

                def put(self, key, value):
                    self.data[key] = value
                    self.data.move_to_end(key)
                    if len(self.data) > self.capacity:
                        self.data.popitem(last=False)
        '''),
        "lesson": "OrderedDict = hash map + doubly linked list: move_to_end and popitem(last=False) "
                  "are both O(1). Say that out loud — it's the answer to 'how would you build it by hand?'.",
        "alternative": "A plain dict also keeps insertion order: `self.data[key] = self.data.pop(key)` "
                       "moves to the end and `next(iter(self.data))` is the oldest. functools.lru_cache "
                       "for memoising functions.",
        "ts": "A JS Map keeps insertion order too: map.delete(k); map.set(k, v); map.keys().next().value is oldest.",
    },
    {
        **W, "id": "cb-w4-handoff-token-bucket", "type": "code", "difficulty": 3,
        "tags": ["handoff", "rate-limit", "dependency-injection"], "pattern": "token bucket",
        "title": "Handoff: token bucket rate limiter",
        "prompt": "Write `TokenBucket(capacity, rate, clock=time.monotonic)`. It starts full; tokens "
                  "refill continuously at `rate` per second up to `capacity`. `allow()` consumes one "
                  "token and returns True, or returns False if fewer than 1 token is available.",
        "starter": code('''
            import time

            class TokenBucket:
                def __init__(self, capacity, rate, clock=time.monotonic):
                    pass

                def allow(self):
                    return True
        '''),
        "tests": code('''
            class Clock:
                def __init__(self): self.t = 100.0
                def __call__(self): return self.t
            def test_burst_then_block():
                clk = Clock()
                b = TokenBucket(3, 1, clock=clk)
                assert [b.allow() for _ in range(4)] == [True, True, True, False], "burst of 3"
            def test_refill():
                clk = Clock()
                b = TokenBucket(2, 2, clock=clk)
                b.allow(); b.allow()
                assert b.allow() is False
                clk.t += 0.5
                assert b.allow() is True, "0.5 s at 2/s refills 1 token"
                assert b.allow() is False
            def test_cap():
                clk = Clock()
                b = TokenBucket(2, 10, clock=clk)
                clk.t += 60
                assert [b.allow() for _ in range(3)] == [True, True, False], "never above capacity"
        '''),
        "hints": ["Don't run a timer. Refill lazily inside allow() based on elapsed time.",
                  "tokens = min(capacity, tokens + (now - last) * rate); last = now.",
                  "if self.tokens >= 1: self.tokens -= 1; return True — else return False"],
        "solution": code('''
            import time

            class TokenBucket:
                def __init__(self, capacity, rate, clock=time.monotonic):
                    self.capacity, self.rate, self.clock = capacity, rate, clock
                    self.tokens = capacity
                    self.last = clock()

                def allow(self):
                    now = self.clock()
                    self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
                    self.last = now
                    if self.tokens >= 1:
                        self.tokens -= 1
                        return True
                    return False
        '''),
        "lesson": "Lazy refill: compute tokens from elapsed time on each call — no background thread. "
                  "Injected clock makes bursts and refills testable instantly.",
        "alternative": "Sliding-window log (deque of timestamps) is exact per window but O(n) memory; "
                       "a fixed-window counter is simplest but allows 2× bursts at window edges.",
    },
    {
        **W, "id": "cb-w4-handoff-tool-loop", "type": "code", "difficulty": 3,
        "tags": ["handoff", "llm", "agents", "tool-use"], "pattern": "tool-call loop",
        "title": "Handoff: a minimal tool-call loop",
        "prompt": code('''
            `client.create(messages)` returns either `{"type": "text", "text": ...}` or
            `{"type": "tool_call", "name": ..., "args": {...}}`. Write
            `run_agent(client, tools, prompt, max_turns=5)`:

            - start with `[{"role": "user", "content": prompt}]`
            - on a tool call, run `tools[name](**args)` and append
              `{"role": "assistant", "content": reply}` then `{"role": "tool", "content": str(result)}`
            - unknown tool → tool content `"error: unknown tool <name>"` (don't crash)
            - return the text reply; raise `RuntimeError` after `max_turns` calls
        '''),
        "starter": code('''
            def run_agent(client, tools, prompt, max_turns=5):
                return client.create([{"role": "user", "content": prompt}])["text"]
        '''),
        "tests": code('''
            class FakeClient:
                def __init__(self, *replies):
                    self.replies, self.seen = list(replies), []
                def create(self, messages):
                    self.seen.append([dict(m) for m in messages])
                    return self.replies.pop(0)
            def add(a, b): return a + b
            def test_tool_then_text():
                c = FakeClient({"type": "tool_call", "name": "add", "args": {"a": 2, "b": 3}},
                               {"type": "text", "text": "It's 5"})
                assert run_agent(c, {"add": add}, "2+3?") == "It's 5"
                last = c.seen[1][-1]
                assert last == {"role": "tool", "content": "5"}, f"tool result message wrong: {last}"
                assert c.seen[1][0] == {"role": "user", "content": "2+3?"}
            def test_unknown_tool():
                c = FakeClient({"type": "tool_call", "name": "nope", "args": {}},
                               {"type": "text", "text": "ok"})
                assert run_agent(c, {}, "hi") == "ok"
                assert c.seen[1][-1]["content"] == "error: unknown tool nope"
            def test_max_turns():
                c = FakeClient(*[{"type": "tool_call", "name": "add", "args": {"a": 1, "b": 1}}] * 3)
                try:
                    run_agent(c, {"add": add}, "loop", max_turns=3)
                except RuntimeError:
                    assert len(c.seen) == 3, f"expected 3 model calls, got {len(c.seen)}"
                    return
                assert False, "should raise RuntimeError after max_turns"
        '''),
        "hints": ["It's a `for _ in range(max_turns)` loop around client.create(messages).",
                  "tools.get(name) returns None for unknown tools — branch on that instead of KeyError.",
                  "result = fn(**reply['args']) if fn else f\"error: unknown tool {reply['name']}\"; then append both messages"],
        "solution": code('''
            def run_agent(client, tools, prompt, max_turns=5):
                messages = [{"role": "user", "content": prompt}]
                for _ in range(max_turns):
                    reply = client.create(messages)
                    if reply["type"] == "text":
                        return reply["text"]
                    fn = tools.get(reply["name"])
                    result = fn(**reply["args"]) if fn else f"error: unknown tool {reply['name']}"
                    messages.append({"role": "assistant", "content": reply})
                    messages.append({"role": "tool", "content": str(result)})
                raise RuntimeError(f"no answer after {max_turns} turns")
        '''),
        "lesson": "An agent is a bounded loop: call model → if tool call, execute and append the "
                  "result → repeat. Always cap turns and turn tool errors into messages the model can "
                  "recover from. A fake client makes the loop testable offline.",
        "alternative": "Real APIs (Anthropic Messages) return a list of content blocks with tool_use ids; "
                       "you append a tool_result block per id. Also wrap tool execution in try/except "
                       "and send the exception text back.",
    },
    {
        **W, "id": "cb-w4-handoff-parse-llm", "type": "code", "difficulty": 3,
        "tags": ["handoff", "llm", "json", "validation"], "pattern": "parse LLM output",
        "title": "Handoff: robust LLM JSON parser",
        "prompt": "Write `parse_llm(text, required)` → dict or `None`. Accept fenced JSON, bare JSON, "
                  "or JSON buried in prose (first `{...}`). Return `None` unless the result is a dict "
                  "containing every key in `required`.",
        "starter": code('''
            import json

            def parse_llm(text, required):
                return json.loads(text)
        '''),
        "tests": code('''
            REQ = ["intent", "confidence"]
            def test_bare():
                assert parse_llm('{"intent": "refund", "confidence": 0.9}', REQ)["intent"] == "refund"
            def test_fenced():
                t = '```json\\n{"intent": "x", "confidence": 1}\\n```'
                assert parse_llm(t, REQ) == {"intent": "x", "confidence": 1}
            def test_prose():
                t = 'Here you go: {"intent": "y", "confidence": 0.2}. Anything else?'
                assert parse_llm(t, REQ)["intent"] == "y"
            def test_missing_key():
                assert parse_llm('{"intent": "z"}', REQ) is None, "confidence missing -> None"
            def test_not_object():
                assert parse_llm("[1, 2]", REQ) is None and parse_llm("nope", REQ) is None
        '''),
        "hints": ["You don't need to strip fences if you scan for the first '{' that decodes.",
                  "json.JSONDecoder().raw_decode(text, i) from each '{' position; stop at the first success.",
                  "after decoding: return obj if isinstance(obj, dict) and all(k in obj for k in required) else None"],
        "solution": code('''
            import json

            def parse_llm(text, required):
                dec = json.JSONDecoder()
                for i, ch in enumerate(text):
                    if ch != "{":
                        continue
                    try:
                        obj = dec.raw_decode(text, i)[0]
                    except json.JSONDecodeError:
                        continue
                    ok = isinstance(obj, dict) and all(k in obj for k in required)
                    return obj if ok else None
                return None
        '''),
        "lesson": "Layer the defences: locate JSON, decode narrowly, validate shape, return a clear "
                  "failure value the caller can act on (retry with the errors, or fall back).",
        "alternative": "Ask the model for tool use / structured output so the API guarantees JSON, "
                       "and keep this parser as the safety net. On None, re-prompt once with the error.",
    },
]
