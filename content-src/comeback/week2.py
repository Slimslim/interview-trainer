"""Comeback week 2: standard library and data structures."""
from _helpers import code, lines

W = {"stage": "week2", "week": 2}


def C(id, pattern, tags, title, prompt, starter, tests, hints, solution, lesson,
      ts=None, difficulty=1, alternative=None):
    it = {"id": "cb-w2-" + id, "type": "code", **W, "difficulty": difficulty,
          "tags": tags, "pattern": pattern, "title": title, "prompt": prompt,
          "starter": code(starter), "tests": code(tests), "hints": hints,
          "solution": code(solution), "lesson": lesson}
    if ts:
        it["ts"] = ts
    if alternative:
        it["alternative"] = code(alternative)
    return it


def P(id, pattern, tags, src, choices, answer, explanation, question="What does this print?",
      kind="output", ts=None, difficulty=1):
    it = {"id": "cb-w2-" + id, "type": "predict", "kind": kind, **W, "difficulty": difficulty,
          "tags": tags, "pattern": pattern, "question": question, "choices": choices,
          "answer": answer, "explanation": explanation}
    if src:
        it["code"] = code(src)
    if ts:
        it["ts"] = ts
    return it


ITEMS = [
    # ---------------------------------------------------------------- collections
    C("counter", "Counter", ["collections", "counting"], "Top k words with Counter",
      "Write `top_k(words, k)` returning the `k` most common words, most common first.",
      '''
      def top_k(words, k):
          pass
      ''',
      '''
      def test_basic():
          got = top_k(["a", "b", "a", "c", "b", "a"], 2)
          assert got == ["a", "b"], f"got {got!r}"
      def test_k1():
          assert top_k(["x", "y", "y"], 1) == ["y"], "y appears twice"
      ''',
      ["collections has a dict subclass made for counting.",
       "Counter(words).most_common(k) returns [(word, count), ...] sorted by count.",
       "return [w for w, _ in Counter(words).most_common(k)]  (after from collections import Counter)"],
      '''
      from collections import Counter

      def top_k(words, k):
          return [w for w, _ in Counter(words).most_common(k)]
      ''',
      "`Counter(iterable)` counts in one call; `.most_common(k)` gives the top k pairs. Missing keys read as 0, and Counters support `+`, `-`, `&`, `|`.",
      ts="const c = new Map(); for (const w of words) c.set(w, (c.get(w) ?? 0) + 1); [...c].sort((a, b) => b[1] - a[1]).slice(0, k)"),

    C("defaultdict", "defaultdict", ["collections", "grouping"], "Group by first letter",
      "Write `group_by_initial(words)` returning a dict letter → list of words (in input order).",
      '''
      def group_by_initial(words):
          pass
      ''',
      '''
      def test_basic():
          got = group_by_initial(["apple", "bob", "avocado"])
          assert dict(got) == {"a": ["apple", "avocado"], "b": ["bob"]}, f"got {dict(got or {})!r}"
      def test_empty():
          assert group_by_initial([]) is not None and dict(group_by_initial([])) == {}, "empty in, empty out"
      ''',
      ["A dict whose missing keys start as an empty list would make this a two-liner.",
       "defaultdict(list) calls list() for a missing key, so you can .append right away.",
       "groups = defaultdict(list); for w in words: groups[w[0]].append(w); return groups"],
      '''
      from collections import defaultdict

      def group_by_initial(words):
          groups = defaultdict(list)
          for w in words:
              groups[w[0]].append(w)
          return groups
      ''',
      "`defaultdict(factory)` calls the factory for missing keys: `list` for grouping, `int` for counting, `set` for unique members.",
      ts="(groups[w[0]] ??= []).push(w)",
      alternative='''
      def group_by_initial(words):
          groups = {}
          for w in words:
              groups.setdefault(w[0], []).append(w)
          return groups
      '''),

    C("deque-maxlen", "deque", ["collections", "deque"], "Keep the last n items",
      "Write `last_n(iterable, n)` returning a list of the final `n` items. Must work on huge iterables without storing them all.",
      '''
      def last_n(iterable, n):
          pass
      ''',
      '''
      def test_basic():
          assert last_n(range(10), 3) == [7, 8, 9], f"got {last_n(range(10), 3)!r}"
      def test_short():
          assert last_n("ab", 5) == ["a", "b"], "fewer items than n"
      def test_generator():
          assert last_n((x * x for x in range(5)), 2) == [9, 16], "works on generators"
      ''',
      ["A double-ended queue can be bounded: old items fall off the other end.",
       "deque(iterable, maxlen=n) keeps only the last n items.",
       "return list(deque(iterable, maxlen=n))"],
      '''
      from collections import deque

      def last_n(iterable, n):
          return list(deque(iterable, maxlen=n))
      ''',
      "`deque` has O(1) `append`/`appendleft`/`pop`/`popleft` (a list's `pop(0)` is O(n)). `maxlen=` makes it a ring buffer.",
      ts="// no built-in deque in JS; arr.slice(-n) needs the whole array in memory"),

    C("deque-queue", "deque", ["collections", "deque", "queue"], "Recent request counter",
      "Write `class RecentCounter` with `ping(t)` (t in ms, always increasing) returning how many pings happened in `[t - 3000, t]`.",
      '''
      class RecentCounter:
          def ping(self, t):
              pass
      ''',
      '''
      def test_sequence():
          rc = RecentCounter()
          got = [rc.ping(t) for t in (1, 100, 3001, 3002)]
          assert got == [1, 2, 3, 3], f"got {got}"
      def test_separate_instances():
          a, b = RecentCounter(), RecentCounter()
          a.ping(1)
          assert b.ping(2) == 1, "each counter keeps its own queue"
      ''',
      ["Store the ping times in a queue created in __init__; drop old ones from the front.",
       "self.q = deque(); in ping: append t, then while self.q[0] < t - 3000: popleft().",
       "self.q.append(t); while self.q[0] < t - 3000: self.q.popleft(); return len(self.q)"],
      '''
      from collections import deque

      class RecentCounter:
          def __init__(self):
              self.q = deque()

          def ping(self, t):
              self.q.append(t)
              while self.q[0] < t - 3000:
                  self.q.popleft()
              return len(self.q)
      ''',
      "Use `deque` whenever you take from the front (queues, BFS, sliding windows): `popleft()` is O(1).",
      ts="class RecentCounter { q: number[] = []; ping(t: number) { ... } }",
      difficulty=2),

    C("ordereddict-lru", "OrderedDict", ["collections", "OrderedDict", "design"], "LRU cache",
      "Write `LRUCache(capacity)` with `get(key)` (→ value or -1) and `put(key, value)`. Over capacity, evict the least recently used key.",
      '''
      class LRUCache:
          def __init__(self, capacity):
              pass

          def get(self, key):
              pass

          def put(self, key, value):
              pass
      ''',
      '''
      def test_evicts_lru():
          c = LRUCache(2)
          c.put(1, "a"); c.put(2, "b")
          assert c.get(1) == "a", "1 was just put"
          c.put(3, "c")  # evicts 2 (1 was used more recently)
          assert c.get(2) == -1, "2 should have been evicted"
          assert c.get(3) == "c" and c.get(1) == "a", "1 and 3 remain"
      def test_update_refreshes():
          c = LRUCache(2)
          c.put(1, "a"); c.put(2, "b"); c.put(1, "A")
          c.put(3, "c")  # evicts 2
          assert c.get(1) == "A" and c.get(2) == -1, "updating 1 makes it recent"
      ''',
      ["OrderedDict remembers order and can move a key to one end in O(1).",
       "On get/put: self.d.move_to_end(key). When too big: self.d.popitem(last=False) removes the oldest.",
       "put: self.d[key] = value; self.d.move_to_end(key); if len(self.d) > self.cap: self.d.popitem(last=False)"],
      '''
      from collections import OrderedDict

      class LRUCache:
          def __init__(self, capacity):
              self.cap = capacity
              self.d = OrderedDict()

          def get(self, key):
              if key not in self.d:
                  return -1
              self.d.move_to_end(key)
              return self.d[key]

          def put(self, key, value):
              self.d[key] = value
              self.d.move_to_end(key)
              if len(self.d) > self.cap:
                  self.d.popitem(last=False)
      ''',
      "`OrderedDict.move_to_end(k)` marks k as newest; `popitem(last=False)` pops the oldest (FIFO). Both O(1). (Or just use `functools.lru_cache` for functions.)",
      ts="Map keeps insertion order: map.delete(k); map.set(k, v); map.delete(map.keys().next().value)",
      difficulty=2),

    # ---------------------------------------------------------------- heapq
    C("heap-kth", "heapq", ["heapq", "heap"], "Kth largest with a min-heap",
      "Write `kth_largest(nums, k)` using `heapq` and a heap of size k (no full sort).",
      '''
      def kth_largest(nums, k):
          pass
      ''',
      '''
      def test_basic():
          assert kth_largest([3, 2, 1, 5, 6, 4], 2) == 5, f"got {kth_largest([3, 2, 1, 5, 6, 4], 2)!r}"
      def test_dupes():
          assert kth_largest([3, 3, 3, 1], 3) == 3, "duplicates count"
      def test_k1():
          assert kth_largest([7], 1) == 7, "single element"
      ''',
      ["heapq is a MIN-heap on a plain list: h[0] is the smallest.",
       "Push each number; whenever len(h) > k, heappop removes the smallest. The k largest remain.",
       "for n in nums: heapq.heappush(h, n); if len(h) > k: heapq.heappop(h)  …  return h[0]"],
      '''
      import heapq

      def kth_largest(nums, k):
          h = []
          for n in nums:
              heapq.heappush(h, n)
              if len(h) > k:
                  heapq.heappop(h)
          return h[0]
      ''',
      "`heapq` functions work on a list you own: `heappush`, `heappop`, `heapify` (O(n)). `h[0]` is the min. For a max-heap push `-x`.",
      ts="// no built-in heap in JS/TS — you'd write a PriorityQueue class",
      alternative='''
      import heapq

      def kth_largest(nums, k):
          return heapq.nlargest(k, nums)[-1]
      ''',
      difficulty=2),

    C("nlargest", "heapq.nlargest", ["heapq"], "Top scorers",
      "`players` is a list of `(name, score)` tuples. Write `top_scorers(players, n)` returning the names of the n highest scores, best first.",
      '''
      def top_scorers(players, n):
          pass
      ''',
      '''
      PLAYERS = [("ann", 50), ("bo", 90), ("cy", 70), ("di", 10)]
      def test_top2():
          assert top_scorers(PLAYERS, 2) == ["bo", "cy"], f"got {top_scorers(PLAYERS, 2)!r}"
      def test_more_than_len():
          assert len(top_scorers(PLAYERS, 10)) == 4, "n bigger than the list returns everyone"
      ''',
      ["heapq has a one-liner for 'the n biggest' that accepts key=.",
       "heapq.nlargest(n, players, key=lambda p: p[1]) returns the tuples.",
       "return [name for name, _ in heapq.nlargest(n, players, key=lambda p: p[1])]"],
      '''
      import heapq

      def top_scorers(players, n):
          return [name for name, _ in heapq.nlargest(n, players, key=lambda p: p[1])]
      ''',
      "`heapq.nlargest(n, xs, key=)` / `nsmallest` are O(len · log n) — better than sorting when n is small.",
      ts="[...players].sort((a, b) => b[1] - a[1]).slice(0, n).map(p => p[0])"),

    C("heap-tuples", "heap of tuples", ["heapq", "tuples"], "Process by priority",
      "`tasks` is a list of `(priority, name)`; lower priority runs first. Write `run_order(tasks)` returning names in run order using `heapify`/`heappop`.",
      '''
      def run_order(tasks):
          pass
      ''',
      '''
      def test_basic():
          got = run_order([(3, "deploy"), (1, "test"), (2, "build")])
          assert got == ["test", "build", "deploy"], f"got {got!r}"
      def test_no_mutation():
          t = [(2, "b"), (1, "a")]
          run_order(t)
          assert t == [(2, "b"), (1, "a")], "copy the list before heapify (it works in place)"
      ''',
      ["Tuples compare element by element, so a heap of (priority, name) orders by priority.",
       "h = list(tasks); heapq.heapify(h); then pop until empty.",
       "return [heapq.heappop(h)[1] for _ in range(len(h))]"],
      '''
      import heapq

      def run_order(tasks):
          h = list(tasks)
          heapq.heapify(h)
          return [heapq.heappop(h)[1] for _ in range(len(h))]
      ''',
      "Heap entries are often tuples `(priority, tiebreak, item)` — the tiebreak (a counter) avoids comparing items that can't be compared.",
      ts="tasks.slice().sort((a, b) => a[0] - b[0]).map(t => t[1])"),

    # ---------------------------------------------------------------- itertools
    C("groupby", "itertools.groupby", ["itertools", "strings"], "Run-length encode",
      "Write `rle(s)`: `'aaabbc'` → `'a3b2c1'`, using `itertools.groupby`.",
      '''
      def rle(s):
          pass
      ''',
      '''
      def test_basic():
          assert rle("aaabbc") == "a3b2c1", f"got {rle('aaabbc')!r}"
      def test_runs_repeat():
          assert rle("aabaa") == "a2b1a2", "groupby groups CONSECUTIVE runs"
      def test_empty():
          assert rle("") == "", "empty string"
      ''',
      ["groupby(s) yields (key, group_iterator) for each run of equal consecutive items.",
       "The group is an iterator — use len(list(g)) or sum(1 for _ in g) to count it.",
       "return \"\".join(f\"{ch}{len(list(g))}\" for ch, g in groupby(s))"],
      '''
      from itertools import groupby

      def rle(s):
          return "".join(f"{ch}{len(list(g))}" for ch, g in groupby(s))
      ''',
      "`groupby` only groups ADJACENT equal items — sort by the same key first if you want SQL-style grouping.",
      ts="s.match(/(.)\\1*/g)?.map(r => r[0] + r.length).join('') ?? ''"),

    C("chain", "itertools.chain", ["itertools"], "Chain iterables",
      "Write `merge_all(lists)` returning one list with every item from each inner iterable, in order, using `itertools`.",
      '''
      def merge_all(lists):
          pass
      ''',
      '''
      def test_basic():
          assert merge_all([[1, 2], (3,), range(4, 6)]) == [1, 2, 3, 4, 5], "mixed iterables"
      def test_empty():
          assert merge_all([]) == [], "nothing to merge"
      ''',
      ["itertools.chain(a, b, c) iterates a, then b, then c.",
       "You have a list OF iterables, so use the alternate constructor that takes one iterable of iterables.",
       "return list(chain.from_iterable(lists))"],
      '''
      from itertools import chain

      def merge_all(lists):
          return list(chain.from_iterable(lists))
      ''',
      "`chain(*its)` / `chain.from_iterable(its)` concatenate lazily, without building intermediate lists.",
      ts="lists.flatMap(l => [...l])"),

    C("islice", "itertools.islice", ["itertools", "generators"], "First n of an infinite stream",
      "Write `first_n(iterable, n)` returning a list of the first `n` items. It must work on infinite iterators like `itertools.count()`.",
      '''
      def first_n(iterable, n):
          pass
      ''',
      '''
      import itertools
      def test_infinite():
          assert first_n(itertools.count(10), 3) == [10, 11, 12], "count(10) is infinite"
      def test_list():
          assert first_n([1, 2], 5) == [1, 2], "shorter than n"
      ''',
      ["You can't slice a generator with [:n].",
       "itertools.islice(iterable, n) is the lazy slice.",
       "return list(islice(iterable, n))"],
      '''
      from itertools import islice

      def first_n(iterable, n):
          return list(islice(iterable, n))
      ''',
      "`islice(it, stop)` or `islice(it, start, stop, step)` slices any iterator lazily — it only pulls the items it needs.",
      ts="const out = []; for (const x of it) { if (out.length >= n) break; out.push(x) }"),

    C("accumulate", "itertools.accumulate", ["itertools", "prefix sums"], "Running totals and max",
      "Write `running(nums)` returning `(totals, maxes)`: the running sum and running max as lists.\n\n`[3, 1, 4]` → `([3, 4, 8], [3, 3, 4])`",
      '''
      def running(nums):
          pass
      ''',
      '''
      def test_basic():
          assert running([3, 1, 4]) == ([3, 4, 8], [3, 3, 4]), f"got {running([3, 1, 4])!r}"
      def test_empty():
          assert running([]) == ([], []), "empty input"
      ''',
      ["itertools.accumulate yields running results; by default it adds.",
       "accumulate(nums, max) uses max instead of +.",
       "return list(accumulate(nums)), list(accumulate(nums, max))"],
      '''
      from itertools import accumulate

      def running(nums):
          return list(accumulate(nums)), list(accumulate(nums, max))
      ''',
      "`accumulate(xs)` = prefix sums; pass any 2-arg function (`max`, `operator.mul`) for other running values. Use `initial=0` to prepend a 0.",
      ts="let s = 0; nums.map(x => (s += x))"),

    C("combinations", "itertools.combinations", ["itertools", "combinatorics"], "Pairs that sum to target",
      "Write `pairs_to(nums, target)` returning every pair `(a, b)` (in input order, a before b) whose sum is `target`.",
      '''
      def pairs_to(nums, target):
          pass
      ''',
      '''
      def test_basic():
          got = pairs_to([1, 2, 3, 4], 5)
          assert got == [(1, 4), (2, 3)], f"got {got!r}"
      def test_none():
          assert pairs_to([1, 1], 5) == [], "no pair sums to 5"
      ''',
      ["itertools has a function for all unordered pairs (no repeats, no reversed duplicates).",
       "combinations(nums, 2) yields (a, b) tuples with a earlier than b.",
       "return [p for p in combinations(nums, 2) if sum(p) == target]"],
      '''
      from itertools import combinations

      def pairs_to(nums, target):
          return [p for p in combinations(nums, 2) if sum(p) == target]
      ''',
      "`combinations(xs, r)` = unordered picks (n choose r); `permutations(xs, r)` = ordered; `product(a, b)` = nested loops. All lazy.",
      ts="nums.flatMap((a, i) => nums.slice(i + 1).map(b => [a, b])).filter(([a, b]) => a + b === target)"),

    C("permutations", "itertools.permutations", ["itertools", "combinatorics"], "All anagrams",
      "Write `anagrams(word)` returning every distinct rearrangement of `word`, sorted.",
      '''
      def anagrams(word):
          pass
      ''',
      '''
      def test_abc():
          got = anagrams("abc")
          assert got == ["abc", "acb", "bac", "bca", "cab", "cba"], f"got {got!r}"
      def test_dupes():
          assert anagrams("aab") == ["aab", "aba", "baa"], "repeated letters give fewer distinct results"
      ''',
      ["permutations(word) yields tuples of characters.",
       "\"\".join(p) turns a tuple back into a string; a set removes duplicates.",
       "return sorted({\"\".join(p) for p in permutations(word)})"],
      '''
      from itertools import permutations

      def anagrams(word):
          return sorted({"".join(p) for p in permutations(word)})
      ''',
      "`permutations` treats positions as distinct, so repeated letters produce duplicates — dedupe with a set comprehension.",
      ts="// no built-in; you'd write a recursive generator"),

    C("pairwise", "itertools.pairwise", ["itertools"], "Differences between neighbours",
      "Write `diffs(nums)`: `[1, 4, 9, 16]` → `[3, 5, 7]` using `itertools.pairwise`.",
      '''
      def diffs(nums):
          pass
      ''',
      '''
      def test_basic():
          assert diffs([1, 4, 9, 16]) == [3, 5, 7], f"got {diffs([1, 4, 9, 16])!r}"
      def test_short():
          assert diffs([5]) == [], "one element has no neighbours"
      ''',
      ["pairwise(xs) yields (xs[0], xs[1]), (xs[1], xs[2]), ...",
       "Unpack each pair in the comprehension: for a, b in pairwise(nums).",
       "return [b - a for a, b in pairwise(nums)]"],
      '''
      from itertools import pairwise

      def diffs(nums):
          return [b - a for a, b in pairwise(nums)]
      ''',
      "`pairwise` (3.10+) replaces `zip(xs, xs[1:])` and works on any iterator, not just lists.",
      ts="nums.slice(1).map((b, i) => b - nums[i])",
      alternative='''
      def diffs(nums):
          return [b - a for a, b in zip(nums, nums[1:])]
      '''),

    # ---------------------------------------------------------------- dataclasses
    C("dataclass-factory", "field(default_factory)", ["dataclasses"], "Dataclass with a list field",
      "Make `Cart` a dataclass with `owner: str` and `items: list[str]` defaulting to an empty list, plus `add(item)`. Two carts must not share items.",
      '''
      class Cart:
          pass
      ''',
      '''
      def test_independent():
          a, b = Cart("ann"), Cart("bo")
          a.add("apple")
          assert a.items == ["apple"], f"a.items is {a.items!r}"
          assert b.items == [], "b must not see a's items"
      def test_repr_and_eq():
          assert Cart("x") == Cart("x", []), "dataclasses generate __eq__"
          assert repr(Cart("x")) == "Cart(owner='x', items=[])", f"repr was {Cart('x')!r}"
      ''',
      ["@dataclass generates __init__, __repr__ and __eq__ from annotated fields.",
       "A mutable default needs field(default_factory=list) — `= []` is rejected.",
       "items: list[str] = field(default_factory=list); def add(self, item): self.items.append(item)"],
      '''
      from dataclasses import dataclass, field

      @dataclass
      class Cart:
          owner: str
          items: list[str] = field(default_factory=list)

          def add(self, item):
              self.items.append(item)
      ''',
      "`field(default_factory=list)` builds a fresh list per instance — the dataclass fix for the mutable-default-argument trap.",
      ts="class Cart { items: string[] = []; constructor(public owner: string) {} }"),

    C("dataclass-frozen", "frozen dataclass", ["dataclasses", "hashing"], "Immutable, hashable point",
      "Make `Point(x, y)` a FROZEN dataclass so points can go in a set and assignment raises an error. Add `moved(dx, dy)` returning a new Point.",
      '''
      class Point:
          pass
      ''',
      '''
      import dataclasses
      def test_hashable():
          assert len({Point(1, 2), Point(1, 2), Point(0, 0)}) == 2, "equal points should dedupe in a set"
      def test_frozen():
          p = Point(1, 2)
          try:
              p.x = 5
          except dataclasses.FrozenInstanceError:
              return
          assert False, "assigning p.x should raise FrozenInstanceError"
      def test_moved():
          assert Point(1, 2).moved(3, 4) == Point(4, 6), "moved returns a new shifted point"
      ''',
      ["Pass an option to the decorator: @dataclass(...).",
       "@dataclass(frozen=True) makes fields read-only and generates __hash__.",
       "def moved(self, dx, dy): return Point(self.x + dx, self.y + dy)"],
      '''
      from dataclasses import dataclass

      @dataclass(frozen=True)
      class Point:
          x: int
          y: int

          def moved(self, dx, dy):
              return Point(self.x + dx, self.y + dy)
      ''',
      "`frozen=True` = immutable + hashable, so instances work as dict keys and set members. Use `dataclasses.replace(p, x=5)` to copy with changes.",
      ts="type Point = Readonly<{ x: number; y: number }>  // but no value-equality in a Set"),

    C("dataclass-order", "dataclass order", ["dataclasses", "sorting"], "Sortable versions",
      "Make `Version(major, minor, patch)` a dataclass that supports `<`, `sorted()` and `max()` by (major, minor, patch).",
      '''
      class Version:
          pass
      ''',
      '''
      def test_compare():
          assert Version(1, 10, 0) > Version(1, 9, 9), "1.10.0 > 1.9.9 (numeric, not string)"
      def test_max():
          vs = [Version(1, 2, 3), Version(2, 0, 0), Version(1, 9, 0)]
          assert max(vs) == Version(2, 0, 0), f"max was {max(vs)!r}"
      ''',
      ["The dataclass decorator can generate comparison methods too.",
       "@dataclass(order=True) compares instances like tuples of their fields, in declaration order.",
       "@dataclass(order=True) class Version: major: int; minor: int; patch: int"],
      '''
      from dataclasses import dataclass

      @dataclass(order=True)
      class Version:
          major: int
          minor: int
          patch: int
      ''',
      "`order=True` adds `<, <=, >, >=` comparing fields as a tuple in declaration order. Put the sort key fields first (or use `field(compare=False)` to skip one).",
      ts="versions.sort((a, b) => a.major - b.major || a.minor - b.minor || a.patch - b.patch)"),

    # ---------------------------------------------------------------- classes
    C("class-repr-eq", "__repr__/__eq__", ["classes", "dunder"], "Plain class with __repr__ and __eq__",
      "Without dataclasses, write `Money(amount, currency)` so that `repr(Money(5, 'USD'))` is `\"Money(5, 'USD')\"` and equal amounts+currencies compare equal.",
      '''
      class Money:
          pass
      ''',
      '''
      def test_repr():
          assert repr(Money(5, "USD")) == "Money(5, 'USD')", f"repr was {Money(5, 'USD')!r}"
      def test_eq():
          assert Money(5, "USD") == Money(5, "USD"), "same values should be equal"
          assert Money(5, "USD") != Money(5, "EUR"), "different currency"
      def test_eq_other_type():
          assert Money(5, "USD") != 5, "comparing with a non-Money should be False, not crash"
      ''',
      ["__init__(self, ...) stores attributes on self. __repr__ returns a string; use !r to get quotes.",
       "__eq__(self, other): return NotImplemented if other isn't a Money, else compare the fields.",
       "def __eq__(self, other): if not isinstance(other, Money): return NotImplemented; return (self.amount, self.currency) == (other.amount, other.currency)"],
      '''
      class Money:
          def __init__(self, amount, currency):
              self.amount = amount
              self.currency = currency

          def __repr__(self):
              return f"Money({self.amount!r}, {self.currency!r})"

          def __eq__(self, other):
              if not isinstance(other, Money):
                  return NotImplemented
              return (self.amount, self.currency) == (other.amount, other.currency)
      ''',
      "`self` is explicit. `f\"{x!r}\"` uses repr (adds quotes to strings). Return `NotImplemented` from `__eq__` for foreign types so Python can try the other side.",
      ts="class Money { constructor(public amount: number, public currency: string) {} toString() {...} }",
      difficulty=2),

    C("property", "@property", ["classes", "property"], "Computed property with a setter",
      "Write `Temperature(celsius)` with a `fahrenheit` property (`c * 9 / 5 + 32`) that can also be SET (updating celsius).",
      '''
      class Temperature:
          def __init__(self, celsius):
              self.celsius = celsius
      ''',
      '''
      def test_get():
          assert Temperature(100).fahrenheit == 212, f"got {Temperature(100).fahrenheit!r}"
      def test_set():
          t = Temperature(0)
          t.fahrenheit = 50
          assert t.celsius == 10, f"setting 50F should give 10C, got {t.celsius!r}"
      def test_live():
          t = Temperature(0)
          t.celsius = 37
          assert round(t.fahrenheit, 1) == 98.6, "property recomputes from celsius"
      ''',
      ["@property turns a method into a read-only attribute (no parentheses when used).",
       "Add a setter with @fahrenheit.setter on a second method of the same name.",
       "@fahrenheit.setter / def fahrenheit(self, f): self.celsius = (f - 32) * 5 / 9"],
      '''
      class Temperature:
          def __init__(self, celsius):
              self.celsius = celsius

          @property
          def fahrenheit(self):
              return self.celsius * 9 / 5 + 32

          @fahrenheit.setter
          def fahrenheit(self, f):
              self.celsius = (f - 32) * 5 / 9
      ''',
      "Start with plain attributes; switch to `@property` later without changing callers. That's why Python doesn't write getters/setters up front.",
      ts="get fahrenheit() { return this.celsius * 9 / 5 + 32 }  set fahrenheit(f) { ... }",
      difficulty=2),

    # ---------------------------------------------------------------- type hints
    C("hints-callable", "type hints", ["typing", "functions"], "Type-hinted higher-order function",
      "Write `apply_n(f, x, n)` that applies `f` to `x` n times. Annotate it: `f` takes an int and returns an int, `x` and `n` are ints, and it returns an int.",
      '''
      def apply_n(f, x, n):
          pass
      ''',
      '''
      def test_behaviour():
          assert apply_n(lambda v: v * 2, 1, 3) == 8, "1 doubled 3 times is 8"
          assert apply_n(lambda v: v + 1, 5, 0) == 5, "n=0 returns x unchanged"
      def test_annotated():
          ann = apply_n.__annotations__
          for name in ("f", "x", "n", "return"):
              assert name in ann, f"missing annotation for {name!r}"
          assert "Callable" in str(ann["f"]), f"f should be a Callable, got {ann['f']!r}"
      ''',
      ["Annotations go after a colon for params and after -> for the return type.",
       "Callable[[int], int] means 'takes one int, returns int'. Import Callable from collections.abc (or typing).",
       "def apply_n(f: Callable[[int], int], x: int, n: int) -> int:"],
      '''
      from collections.abc import Callable

      def apply_n(f: Callable[[int], int], x: int, n: int) -> int:
          for _ in range(n):
              x = f(x)
          return x
      ''',
      "Hints are not enforced at runtime — they're for readers and checkers (mypy/pyright). `Callable[[Arg1, Arg2], Ret]` mirrors TS `(a: Arg1, b: Arg2) => Ret`.",
      ts="function applyN(f: (v: number) => number, x: number, n: number): number"),

    C("hints-optional", "Optional", ["typing"], "Optional return type",
      "Write `find_user(users, name)`: `users` is a `dict[str, int]` (name → age). Return the age or `None`. Annotate params and return (`Optional[int]` or `int | None`).",
      '''
      def find_user(users, name):
          pass
      ''',
      '''
      def test_found():
          assert find_user({"ann": 30}, "ann") == 30, "ann is 30"
      def test_missing():
          assert find_user({"ann": 30}, "bo") is None, "missing user returns None"
      def test_annotated():
          ann = find_user.__annotations__
          assert "return" in ann and "users" in ann, f"annotate users and the return type, got {ann}"
          assert "None" in str(ann["return"]) or "Optional" in str(ann["return"]), "return type should allow None"
      ''',
      ["dict.get already returns None for a missing key.",
       "Write the hints inline: users: dict[str, int], name: str, -> Optional[int].",
       "def find_user(users: dict[str, int], name: str) -> Optional[int]: return users.get(name)"],
      '''
      from typing import Optional

      def find_user(users: dict[str, int], name: str) -> Optional[int]:
          return users.get(name)
      ''',
      "Built-in generics work directly as hints: `list[int]`, `dict[str, int]`, `tuple[int, ...]`. `Optional[X]` == `X | None` (3.10+ syntax).",
      ts="function findUser(users: Record<string, number>, name: string): number | undefined"),

    # ---------------------------------------------------------------- files
    C("files-rw", "with open()", ["files", "io"], "Write then read a file",
      "Write `save_lines(path, items)` (one item per line) and `load_lines(path)` (returns the lines without newlines). Use `with open(...)`.",
      '''
      def save_lines(path, items):
          pass

      def load_lines(path):
          pass
      ''',
      '''
      import os, tempfile
      def test_roundtrip():
          with tempfile.TemporaryDirectory() as d:
              p = os.path.join(d, "notes.txt")
              save_lines(p, ["alpha", "beta"])
              with open(p) as f:
                  raw = f.read()
              assert raw == "alpha\\nbeta\\n", f"file content was {raw!r}"
              assert load_lines(p) == ["alpha", "beta"], f"load_lines gave {load_lines(p)!r}"
      ''',
      ["open(path, \"w\") to write, open(path) to read; `with` closes the file for you.",
       "Write each item followed by \"\\n\". Reading: f.read().splitlines() drops the newlines.",
       "with open(path, \"w\") as f: for x in items: f.write(x + \"\\n\")  …  with open(path) as f: return f.read().splitlines()"],
      '''
      def save_lines(path, items):
          with open(path, "w", encoding="utf-8") as f:
              for x in items:
                  f.write(x + "\\n")

      def load_lines(path):
          with open(path, encoding="utf-8") as f:
              return f.read().splitlines()
      ''',
      "Always `with open(...) as f:` — it closes the file even on errors. Pass `encoding=\"utf-8\"`. `splitlines()` strips the line endings for you.",
      ts="fs.writeFileSync(path, items.join('\\n') + '\\n'); fs.readFileSync(path, 'utf8').split('\\n')"),

    C("stringio", "file-like objects", ["files", "io"], "Count non-blank lines in a file object",
      "Write `count_nonblank(f)` where `f` is any open text file (tests pass an `io.StringIO`). Iterate it line by line.",
      '''
      def count_nonblank(f):
          pass
      ''',
      '''
      import io
      def test_basic():
          f = io.StringIO("a\\n\\n  \\nb\\n")
          assert count_nonblank(f) == 2, "only 'a' and 'b' are non-blank"
      def test_empty():
          assert count_nonblank(io.StringIO("")) == 0, "empty file"
      ''',
      ["Iterating a file yields one line at a time (with its trailing newline).",
       "line.strip() is falsy for blank and whitespace-only lines.",
       "return sum(1 for line in f if line.strip())"],
      '''
      def count_nonblank(f):
          return sum(1 for line in f if line.strip())
      ''',
      "Write functions that take a file OBJECT, not a path — then tests can pass `io.StringIO(...)` and nothing touches disk. `for line in f` streams the file.",
      ts="text.split('\\n').filter(l => l.trim()).length"),

    # ---------------------------------------------------------------- json
    C("json-dumps", "json.dumps", ["json"], "Pretty, stable JSON",
      "Write `pretty(obj)` returning JSON with 2-space indentation and keys sorted alphabetically.",
      '''
      def pretty(obj):
          pass
      ''',
      '''
      def test_pretty():
          got = pretty({"b": 1, "a": [1, 2]})
          want = '{\\n  "a": [\\n    1,\\n    2\\n  ],\\n  "b": 1\\n}'
          assert got == want, f"got {got!r}"
      ''',
      ["json.dumps turns Python objects into a JSON string; keyword options control the layout.",
       "indent=2 for indentation, sort_keys=True for stable key order.",
       "return json.dumps(obj, indent=2, sort_keys=True)"],
      '''
      import json

      def pretty(obj):
          return json.dumps(obj, indent=2, sort_keys=True)
      ''',
      "`dumps`/`loads` work with strings; `dump`/`load` with files. `sort_keys=True` makes output diff-friendly.",
      ts="JSON.stringify(obj, Object.keys(obj).sort(), 2)  // sorting is awkward in JS"),

    C("json-default", "json default=", ["json", "datetime"], "Serialize dates with default=",
      "Write `to_json(obj)` so that `datetime.date` values become ISO strings: `{'d': date(2024, 1, 2)}` → `'{\"d\": \"2024-01-02\"}'`.",
      '''
      def to_json(obj):
          pass
      ''',
      '''
      from datetime import date
      def test_date():
          assert to_json({"d": date(2024, 1, 2)}) == '{"d": "2024-01-02"}', f"got {to_json({'d': date(2024, 1, 2)})!r}"
      def test_plain():
          assert to_json([1, "a"]) == '[1, "a"]', "plain values unchanged"
      ''',
      ["json.dumps raises TypeError for types it doesn't know — unless you give it a fallback.",
       "default= is a function called with each unknown object; return something JSON can handle.",
       "return json.dumps(obj, default=lambda o: o.isoformat())"],
      '''
      import json
      from datetime import date

      def _encode(o):
          if isinstance(o, date):
              return o.isoformat()
          raise TypeError(f"not serializable: {type(o).__name__}")

      def to_json(obj):
          return json.dumps(obj, default=_encode)
      ''',
      "`default=fn` is called only for unknown types. Raise TypeError for anything you don't handle, so real bugs still surface. (`default=str` is the quick-and-dirty version.)",
      ts="JSON.stringify(obj)  // Date has toJSON(), so JS does this automatically",
      difficulty=2),

    C("json-decode-error", "JSONDecodeError", ["json", "exceptions"], "Parse JSON or return None",
      "Write `parse_or_none(s)` returning the parsed value, or `None` if `s` isn't valid JSON.",
      '''
      def parse_or_none(s):
          pass
      ''',
      '''
      def test_ok():
          assert parse_or_none('{"a": [1, true, null]}') == {"a": [1, True, None]}, "valid JSON"
      def test_bad():
          assert parse_or_none("{'a': 1}") is None, "single quotes aren't valid JSON"
          assert parse_or_none("") is None, "empty string isn't valid JSON"
      def test_falsy_value():
          assert parse_or_none("0") == 0, "0 is valid JSON"
      ''',
      ["json.loads raises a specific exception class on bad input.",
       "Catch json.JSONDecodeError (a subclass of ValueError).",
       "try: return json.loads(s) / except json.JSONDecodeError: return None"],
      '''
      import json

      def parse_or_none(s):
          try:
              return json.loads(s)
          except json.JSONDecodeError:
              return None
      ''',
      "`json.JSONDecodeError` has `.msg`, `.lineno`, `.colno` — log them when parsing LLM or API output. JSON `true/null` become `True/None`.",
      ts="try { return JSON.parse(s) } catch { return null }"),

    # ---------------------------------------------------------------- predict
    P("counter-most", "Counter", ["collections"],
      '''
      from collections import Counter
      c = Counter("banana")
      print(c.most_common(2), c["z"])
      ''',
      ["[('a', 3), ('n', 2)] 0", "[('a', 3), ('n', 2)] KeyError", "{'a': 3, 'n': 2} 0", "[('a', 3), ('b', 1)] 0"], 0,
      "most_common returns a list of (item, count) tuples. A missing key in a Counter reads as 0 — no KeyError, and it isn't inserted."),
    P("defaultdict-insert", "defaultdict", ["collections"],
      '''
      from collections import defaultdict
      d = defaultdict(int)
      if d["x"] == 0:
          pass
      print(len(d), "y" in d)
      ''',
      ["1 False", "0 False", "KeyError", "1 True"], 0,
      "READING a missing key on a defaultdict inserts it (calls int() → 0). `in` does not insert. Use `d.get(k)` when you only want to peek."),
    P("deque-maxlen-p", "deque", ["collections", "deque"],
      '''
      from collections import deque
      d = deque([1, 2, 3], maxlen=3)
      d.append(4)
      d.appendleft(0)
      print(list(d))
      ''',
      ["[0, 2, 3]", "[0, 1, 2, 3, 4]", "[2, 3, 4]", "[0, 1, 2]"], 0,
      "With maxlen, append drops from the left ([2, 3, 4]); appendleft drops from the right ([0, 2, 3])."),
    P("heap-min", "heapq", ["heapq"],
      '''
      import heapq
      h = []
      for x in [5, 1, 4]:
          heapq.heappush(h, x)
      print(h[0], heapq.heappop(h), h[0])
      ''',
      ["1 1 4", "5 5 4", "1 1 1", "5 1 4"], 0,
      "heapq is a min-heap: h[0] is always the smallest. heappop removes it, so the new h[0] is 4."),
    P("groupby-adjacent", "itertools.groupby", ["itertools"],
      '''
      from itertools import groupby
      print([k for k, _ in groupby("aabaa")])
      ''',
      ["['a', 'b', 'a']", "['a', 'b']", "['aa', 'b', 'aa']", "[('a', 4), ('b', 1)]"], 0,
      "groupby only merges CONSECUTIVE equal items, so the two runs of 'a' stay separate. Sort first for one group per key."),
    P("perm-vs-comb", "itertools.combinations", ["itertools", "combinatorics"],
      '''
      from itertools import combinations, permutations
      print(len(list(permutations("abc", 2))), len(list(combinations("abc", 2))))
      ''',
      ["6 3", "3 6", "6 6", "9 3"], 0,
      "permutations counts order (ab and ba): 3·2 = 6. combinations doesn't: C(3, 2) = 3."),
    P("class-eq", "__repr__/__eq__", ["classes", "dataclasses"],
      '''
      from dataclasses import dataclass
      class A:
          def __init__(self, x):
              self.x = x
      @dataclass
      class B:
          x: int
      print(A(1) == A(1), B(1) == B(1))
      ''',
      ["False True", "True True", "False False", "True False"], 0,
      "A plain class inherits identity-based __eq__, so two separate instances differ. @dataclass generates a field-by-field __eq__."),
    P("dataclass-order-p", "dataclass order", ["dataclasses", "sorting"],
      '''
      from dataclasses import dataclass
      @dataclass(order=True)
      class V:
          major: int
          minor: int
      print(V(1, 10) > V(1, 9), sorted([V(2, 0), V(1, 5)])[0])
      ''',
      ["True V(major=1, minor=5)", "False V(major=1, minor=5)", "True V(major=2, minor=0)", "TypeError"], 0,
      "order=True compares like the tuple (major, minor): (1, 10) > (1, 9) numerically. The generated __repr__ shows field names."),
    P("json-types", "json.dumps", ["json"],
      '''
      import json
      print(json.dumps({"a": (1, 2), "b": None, "c": True}))
      ''',
      ['{"a": [1, 2], "b": null, "c": true}', '{"a": (1, 2), "b": None, "c": True}',
       "{'a': [1, 2], 'b': null, 'c': true}", "TypeError"], 0,
      "Tuples become JSON arrays, None → null, True → true, and keys/strings use double quotes. Round-tripping turns the tuple into a list."),
    P("deque-complexity", "deque", ["collections", "big-o"], None,
      ["list.pop(0) O(n), deque.popleft() O(1)", "both O(1)", "both O(n)", "list.pop(0) O(1), deque.popleft() O(n)"], 0,
      "Removing from the front of a list shifts every remaining element. deque is a linked block structure with O(1) ops at both ends. Use deque for BFS queues.",
      question="Cost of removing the FIRST element: `list.pop(0)` vs `deque.popleft()`?",
      kind="complexity", ts="arr.shift() is also O(n) in JS"),

    # ---------------------------------------------------------------- parsons
    {
        "id": "cb-w2-parsons-jsonl", "type": "parsons", **W, "difficulty": 2,
        "tags": ["json", "files", "exceptions"], "pattern": "JSONDecodeError",
        "title": "Load JSON Lines, skip bad rows",
        "prompt": "Arrange the lines so `load_jsonl(f)` returns the parsed objects from a file of one-JSON-per-line, skipping blank and invalid lines.",
        "lines": lines('''
            import json
            def load_jsonl(f):
                rows = []
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
                return rows
        '''),
        "tests": code('''
            import io
            def test_mixed():
                f = io.StringIO('{"a": 1}\\n\\nnot json\\n[2]\\n')
                got = load_jsonl(f)
                assert got == [{"a": 1}, [2]], f"got {got!r}"
        '''),
        "lesson": "JSON Lines is parsed line by line; wrap only `json.loads` in the try so one bad row doesn't sink the whole file.",
    },
    {
        "id": "cb-w2-parsons-rect", "type": "parsons", **W, "difficulty": 1,
        "tags": ["dataclasses", "property"], "pattern": "@property",
        "title": "Dataclass with a computed property",
        "prompt": "Arrange the lines so `Rect(w, h)` is a dataclass with an `area` property.",
        "lines": lines('''
            from dataclasses import dataclass
            @dataclass
            class Rect:
                w: float
                h: float
                @property
                def area(self):
                    return self.w * self.h
        '''),
        "tests": code('''
            def test_area():
                r = Rect(2, 3)
                assert r.area == 6, f"area was {r.area!r}"
                assert r == Rect(2, 3), "dataclass eq"
        '''),
        "lesson": "Decorators sit directly above what they wrap. A @property is not a dataclass field, so it isn't in __init__ or __repr__.",
    },

    # ---------------------------------------------------------------- bugs
    {
        "id": "cb-w2-bug-max-heap", "type": "bug", **W, "difficulty": 2,
        "tags": ["heapq"], "pattern": "heapq",
        "title": "Max-heap that returns the wrong sign",
        "code": code('''
            import heapq

            def largest_first(nums):
                h = [-n for n in nums]
                heapq.heapify(h)
                out = []
                while h:
                    out.append(heapq.heappop(h))
                return out
        '''),
        "bugLine": 8,
        "fixed": code('''
            import heapq

            def largest_first(nums):
                h = [-n for n in nums]
                heapq.heapify(h)
                out = []
                while h:
                    out.append(-heapq.heappop(h))
                return out
        '''),
        "tests": code('''
            def test_order():
                assert largest_first([3, 1, 2]) == [3, 2, 1], f"got {largest_first([3, 1, 2])!r}"
        '''),
        "choices": [
            "Negate the popped value back: `out.append(-heapq.heappop(h))`",
            "Use `heapq.heapify(h, reverse=True)`",
            "Remove the negation in line 4",
            "Return `out[::-1]`",
        ],
        "answer": 0,
        "explanation": "heapq is min-only, so the max-heap trick stores `-n`. You must negate again when popping, otherwise you return the negated values.",
    },
    {
        "id": "cb-w2-bug-groupby-unsorted", "type": "bug", **W, "difficulty": 2,
        "tags": ["itertools", "grouping"], "pattern": "itertools.groupby",
        "title": "Grouping words by length",
        "code": code('''
            from itertools import groupby

            def by_length(words):
                result = {}
                for n, group in groupby(words, key=len):
                    result[n] = list(group)
                return result
        '''),
        "bugLine": 5,
        "fixed": code('''
            from itertools import groupby

            def by_length(words):
                result = {}
                for n, group in groupby(sorted(words, key=len), key=len):
                    result[n] = list(group)
                return result
        '''),
        "tests": code('''
            def test_groups():
                got = by_length(["a", "bb", "c", "dd"])
                assert got == {1: ["a", "c"], 2: ["bb", "dd"]}, f"got {got!r}"
        '''),
        "choices": [
            "Sort by the same key first: `groupby(sorted(words, key=len), key=len)`",
            "Use `result[n] += list(group)`",
            "Replace `key=len` with `key=lambda w: w`",
            "Convert `group` with `tuple(group)` instead of `list(group)`",
        ],
        "answer": 0,
        "explanation": "groupby only groups adjacent items, so unsorted input yields the same key several times and later groups overwrite earlier ones. Sort by the grouping key first (or use defaultdict(list)).",
    },
]
