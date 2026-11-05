from _helpers import code


def out(id_, pattern, tags, src, choices, answer, explanation, difficulty=1, ts=None,
        question="What does this print?"):
    it = {
        "id": f"fde-pr-{id_}", "type": "predict", "kind": "output", "stage": "coding",
        "difficulty": difficulty, "tags": tags, "pattern": pattern,
        "code": code(src), "question": question,
        "choices": choices, "answer": answer, "explanation": explanation,
    }
    if ts:
        it["ts"] = ts
    return it


def cx(id_, pattern, tags, src, choices, answer, explanation, difficulty=1,
       question="What is the time complexity?", ts=None):
    it = {
        "id": f"fde-pr-{id_}", "type": "predict", "kind": "complexity", "stage": "coding",
        "difficulty": difficulty, "tags": tags + ["big-o"], "pattern": pattern,
        "code": code(src), "question": question,
        "choices": choices, "answer": answer, "explanation": explanation,
    }
    if ts:
        it["ts"] = ts
    return it


def concept(id_, pattern, tags, question, choices, answer, explanation, stage="design",
            difficulty=1, src=None):
    it = {
        "id": f"fde-pr-{id_}", "type": "predict", "kind": "concept", "stage": stage,
        "difficulty": difficulty, "tags": tags, "pattern": pattern,
        "question": question, "choices": choices, "answer": answer,
        "explanation": explanation,
    }
    if src:
        it["code"] = code(src)
    return it


OUTPUT = [
    out("dict-order", "dict insertion order", ["dict"], '''
        d = {"b": 1, "a": 2}
        d["c"] = 3
        del d["b"]
        d["b"] = 4
        print(list(d))
    ''', ["['a', 'c', 'b']", "['b', 'a', 'c']", "['a', 'b', 'c']", "['c', 'a', 'b']"], 0,
        "Dicts keep insertion order. Deleting 'b' and re-adding it puts it at the end; "
        "updating an existing key would not move it.",
        ts="A JS Map also keeps insertion order; plain objects put integer-like keys first."),
    out("default-mutable", "mutable default argument", ["functions", "gotcha"], '''
        def add(x, acc=[]):
            acc.append(x)
            return acc

        add(1)
        print(add(2))
    ''', ["[1, 2]", "[2]", "[1]", "TypeError"], 0,
        "Default values are evaluated once, at def time. Every call without `acc` shares the "
        "same list. Use `acc=None` and create the list inside.",
        ts="JS evaluates default parameters on every call, so this gotcha doesn't exist there."),
    out("late-binding", "closure late binding", ["closures", "lambda"], '''
        fs = [lambda: i for i in range(3)]
        print([f() for f in fs])
    ''', ["[2, 2, 2]", "[0, 1, 2]", "[0, 0, 0]", "NameError"], 0,
        "Closures capture the variable, not its value. All lambdas read `i` after the loop "
        "ends (2). Fix: `lambda i=i: i`.",
        difficulty=2,
        ts="In JS, `for (let i...)` creates a fresh binding per iteration, giving [0, 1, 2]."),
    out("gen-exhaust", "generator exhaustion", ["generators"], '''
        g = (x * x for x in range(3))
        print(sum(g), sum(g))
    ''', ["5 0", "5 5", "0 5", "14 0"], 0,
        "A generator can be iterated once. The first sum consumes 0+1+4 = 5; the second sees "
        "nothing and returns 0. Use a list if you need two passes."),
    out("slice-step", "slicing", ["slicing", "lists"], '''
        a = [0, 1, 2, 3, 4, 5]
        print(a[1:5:2], a[-2:])
    ''', ["[1, 3] [4, 5]", "[1, 3, 5] [4, 5]", "[1, 3] [5]", "[2, 4] [4, 5]"], 0,
        "Stop is exclusive: indices 1 and 3 from [1:5:2]. a[-2:] is the last two items."),
    out("sort-key-tuple", "sorted with tuple key", ["sorting", "lambda"], '''
        words = ["bb", "a", "ccc", "dd"]
        print(sorted(words, key=lambda w: (-len(w), w)))
    ''', ["['ccc', 'bb', 'dd', 'a']", "['ccc', 'dd', 'bb', 'a']", "['a', 'bb', 'dd', 'ccc']",
          "['bb', 'dd', 'ccc', 'a']"], 0,
        "Tuples compare element by element: longest first (negated length), then "
        "alphabetical to break ties.",
        difficulty=2,
        ts="JS: words.sort((a, b) => b.length - a.length || a.localeCompare(b))."),
    out("counter-ties", "Counter.most_common ties", ["counter", "hashing"], '''
        from collections import Counter
        c = Counter(["y", "x", "x", "y", "z"])
        print(c.most_common(1))
    ''', ["[('y', 2)]", "[('x', 2)]", "[('x', 2), ('y', 2)]", "('y', 2)"], 0,
        "most_common sorts by count with a stable sort, so ties keep first-seen order. 'y' "
        "was seen first. It returns a list of (item, count) tuples.",
        difficulty=2),
    out("defaultdict-read", "defaultdict", ["defaultdict", "dict"], '''
        from collections import defaultdict
        dd = defaultdict(int)
        dd["a"] += 1
        if dd["b"] == 0:
            pass
        print(dict(dd))
    ''', ["{'a': 1, 'b': 0}", "{'a': 1}", "KeyError", "{'a': 1, 'b': None}"], 0,
        "Reading a missing key with [] on a defaultdict inserts the default. Use `'b' in dd` "
        "or dd.get('b') to check without inserting."),
    out("is-vs-eq", "identity vs equality", ["is", "equality"], '''
        a = [1, 2]
        b = [1, 2]
        c = a
        print(a == b, a is b, a is c)
    ''', ["True False True", "True True True", "False False True", "True False False"], 0,
        "`==` compares values; `is` compares identity. b is a separate list; c is the same "
        "object as a. Use `is` only for None and sentinels.",
        ts="JS `===` on objects is identity, like Python's `is`."),
    out("floor-div", "integer division", ["math", "division"], '''
        print(-7 // 2, -7 % 2, int(-7 / 2))
    ''', ["-4 1 -3", "-3 -1 -3", "-4 -1 -4", "-3 1 -3"], 0,
        "// floors toward negative infinity (-4), and % takes the sign of the divisor (1). "
        "int() truncates toward zero (-3).",
        difficulty=2,
        ts="JS: Math.floor(-7 / 2) is -4, but -7 % 2 is -1 (sign of the dividend)."),
    out("fstring-spec", "f-string format spec", ["f-strings", "strings"], '''
        x = 3.14159
        n = 42
        print(f"{x:.2f}|{n:05d}|{n:>4}|")
    ''', ["3.14|00042|  42|", "3.14|42000|42  |", "3.1|00042|  42|", "3.14|00042|42|"], 0,
        ".2f rounds to two decimals, 05d zero-pads to width 5, >4 right-aligns in width 4.",
        ts="JS: x.toFixed(2), String(n).padStart(5, '0'), String(n).padStart(4)."),
    out("grid-alias", "list aliasing", ["lists", "aliasing", "gotcha"], '''
        grid = [[0] * 2] * 2
        grid[0][0] = 1
        print(grid)
    ''', ["[[1, 0], [1, 0]]", "[[1, 0], [0, 0]]", "[[1, 1], [0, 0]]", "[[1, 1], [1, 1]]"], 0,
        "`* 2` on the outer list copies the reference, so both rows are the same list. Use "
        "`[[0] * 2 for _ in range(2)]`.",
        ts="JS has the same trap: Array(2).fill([0, 0]) shares one inner array."),
    out("set-ops", "set operations", ["sets"], '''
        a = {1, 2, 3}
        b = {2, 3, 4}
        print(sorted(a - b), sorted(a ^ b), sorted(a & b))
    ''', ["[1] [1, 4] [2, 3]", "[1, 4] [1] [2, 3]", "[1] [2, 3] [1, 4]", "[4] [1, 4] [2, 3]"], 0,
        "- is difference (in a, not b), ^ is symmetric difference (in exactly one), & is "
        "intersection."),
    out("zip-shortest", "zip stops at shortest", ["zip", "iteration"], '''
        print(list(zip("ab", [1, 2, 3])))
    ''', ["[('a', 1), ('b', 2)]", "[('a', 1), ('b', 2), (None, 3)]", "ValueError",
          "[('ab', 1)]"], 0,
        "zip stops at the shortest input and silently drops the rest. Use zip(..., "
        "strict=True) (3.10+) to raise, or itertools.zip_longest to pad."),
    out("enumerate-start", "enumerate start", ["enumerate", "iteration"], '''
        for i, c in enumerate("ab", start=1):
            print(i, c, end="; ")
    ''', ["1 a; 2 b;", "0 a; 1 b;", "1 a; 2 b; 3", "a 1; b 2;"], 0,
        "start=1 changes only the counter; the items are unchanged. Handy for 1-based line "
        "numbers."),
    out("finally-return", "try/finally return", ["exceptions", "gotcha"], '''
        def f():
            try:
                return "try"
            finally:
                return "finally"

        print(f())
    ''', ["finally", "try", "try finally", "SyntaxError"], 0,
        "finally always runs, and a return inside it overrides the pending return (it also "
        "swallows exceptions). Avoid return in finally; newer Pythons warn about it.",
        difficulty=2),
    out("json-tuple", "json.dumps types", ["json"], '''
        import json
        print(json.dumps({"k": (1, 2), "ok": True, "n": None}))
    ''', ['{"k": [1, 2], "ok": true, "n": null}', "{'k': (1, 2), 'ok': True, 'n': None}",
          '{"k": (1, 2), "ok": true, "n": null}', "TypeError"], 0,
        "JSON has no tuple, so tuples become arrays. True/None become true/null, and keys "
        "use double quotes. A set would raise TypeError.",
        ts="JSON.stringify behaves the same for arrays, true and null."),
    out("any-all-empty", "any/all on empty", ["builtins", "logic"], '''
        print(all([]), any([]))
    ''', ["True False", "False False", "False True", "True True"], 0,
        "all() of nothing is vacuously True; any() of nothing is False. Watch for this when "
        "validating an empty batch.",
        ts="JS: [].every(f) is true, [].some(f) is false."),
    out("split-strip", "string methods", ["strings"], '''
        print("a,b,,c".split(","), " Hi ".strip().lower())
    ''', ["['a', 'b', '', 'c'] hi", "['a', 'b', 'c'] hi", "['a', 'b', '', 'c'] Hi",
          "['a,b,,c'] hi"], 0,
        "split with an explicit separator keeps empty fields. Only split() with no argument "
        "collapses runs of whitespace."),
    out("star-unpack", "extended unpacking", ["unpacking"], '''
        first, *rest = [1, 2, 3]
        *init, last = "abc"
        print(rest, init, last)
    ''', ["[2, 3] ['a', 'b'] c", "(2, 3) ('a', 'b') c", "[2, 3] ab c", "[2, 3] ['a', 'b'] ['c']"],
        0,
        "A starred target always collects a list, even from a string. The plain targets get "
        "single items.",
        ts="JS: const [first, ...rest] = [1, 2, 3]; rest must come last in JS."),
    out("heap-root", "heapq is a min-heap", ["heap", "heapq"], '''
        import heapq
        h = []
        for x in [5, 1, 4, 2]:
            heapq.heappush(h, x)
        print(heapq.heappop(h), h[0])
    ''', ["1 2", "5 4", "1 4", "1 5"], 0,
        "heapq is a min-heap: pop returns the smallest, and h[0] is always the next smallest. "
        "For a max-heap push -x."),
    out("heap-tuples", "heap of tuples", ["heap", "heapq", "tuples"], '''
        import heapq
        h = []
        for item in [(2, "b"), (1, "z"), (1, "a")]:
            heapq.heappush(h, item)
        print([heapq.heappop(h)[1] for _ in range(3)])
    ''', ["['a', 'z', 'b']", "['z', 'a', 'b']", "['b', 'z', 'a']", "['a', 'b', 'z']"], 0,
        "Tuples compare by priority first, then by the next field to break ties. Add a "
        "counter as the second field when payloads aren't comparable.",
        difficulty=2),
    out("comp-scope", "comprehension scope", ["comprehensions", "scope"], '''
        x = "outer"
        ys = [x for x in range(3)]
        print(x)
    ''', ["outer", "2", "[0, 1, 2]", "NameError"], 0,
        "In Python 3 a comprehension has its own scope, so its loop variable doesn't leak. A "
        "plain for loop would rebind x to 2."),
    out("get-vs-index", "dict.get vs indexing", ["dict", "exceptions"], '''
        d = {"a": 1}
        print(d.get("b", 0))
        print(d["b"])
    ''', ["0, then KeyError", "0 then None", "0 then 0", "None then KeyError"], 0,
        "get returns the default (0) without raising. Indexing a missing key raises "
        "KeyError.",
        ts="JS returns undefined for a missing key instead of throwing."),
    out("mutate-while-iter", "mutating during iteration", ["dict", "exceptions", "gotcha"], '''
        d = {"a": 1, "b": 2}
        for k in d:
            if k == "a":
                d["c"] = 3
        print(d)
    ''', ["RuntimeError", "{'a': 1, 'b': 2, 'c': 3}", "{'a': 1, 'b': 2}", "KeyError"], 0,
        "Adding or removing keys while iterating a dict raises RuntimeError (dictionary "
        "changed size during iteration). Iterate over list(d) instead.",
        difficulty=2),
    out("sort-returns-none", "list.sort returns None", ["sorting", "lists"], '''
        a = [3, 1, 2]
        b = a.sort()
        print(b, a)
    ''', ["None [1, 2, 3]", "[1, 2, 3] [1, 2, 3]", "[1, 2, 3] [3, 1, 2]", "None [3, 1, 2]"], 0,
        "list.sort() sorts in place and returns None. sorted(a) returns a new list.",
        ts="JS arr.sort() sorts in place and also returns the array (and sorts "
           "lexicographically by default)."),
    out("round-bankers", "round half to even", ["math", "rounding"], '''
        print(round(2.5), round(3.5), round(0.125, 2))
    ''', ["2 4 0.12", "3 4 0.13", "2 3 0.12", "3 4 0.12"], 0,
        "round() uses banker's rounding: halves go to the even neighbour. 0.125 is exact in "
        "binary, so it rounds to even, 0.12. Use Decimal for money.",
        difficulty=2,
        ts="JS Math.round(2.5) is 3 (rounds half up)."),
    out("join-ints", "str.join needs strings", ["strings", "exceptions"], '''
        ids = [1, 2, 3]
        print(", ".join(ids))
    ''', ["TypeError", "1, 2, 3", "[1, 2, 3]", "123"], 0,
        "join requires strings and raises TypeError on ints. Use "
        "', '.join(map(str, ids)).",
        ts="JS [1, 2, 3].join(', ') converts numbers for you."),
    out("shallow-copy", "shallow copy", ["lists", "aliasing", "copy"], '''
        a = [[1], [2]]
        b = a.copy()
        b[0].append(9)
        b.append([3])
        print(a)
    ''', ["[[1, 9], [2]]", "[[1], [2]]", "[[1, 9], [2], [3]]", "[[1], [2], [3]]"], 0,
        "copy() is shallow: a new outer list holding the same inner lists. Mutating an inner "
        "list shows through; appending to b doesn't. Use copy.deepcopy for nested data.",
        difficulty=2,
        ts="JS spread [...a] is also shallow; use structuredClone(a) for a deep copy."),
]

COMPLEXITY = [
    cx("cx-set-membership", "set membership is O(1)", ["sets", "hashing"], '''
        seen = set()
        for x in items:          # n items
            if x in seen:
                return True
            seen.add(x)
    ''', ["O(n)", "O(n^2)", "O(n log n)", "O(1)"], 0,
        "Set lookups and inserts are O(1) on average, so one pass costs O(n)."),
    cx("cx-list-membership", "list membership is O(n)", ["lists", "hashing"], '''
        common = []
        for x in a:              # n items
            if x in b:           # b is a list of m items
                common.append(x)
    ''', ["O(n * m)", "O(n + m)", "O(n)", "O(n log m)"], 0,
        "`in` on a list scans it: O(m) each time. Convert b to a set first for O(n + m)."),
    cx("cx-sort-then-scan", "sorting dominates", ["sorting"], '''
        a.sort()                 # n items
        for i in range(1, len(a)):
            if a[i] == a[i - 1]:
                return True
    ''', ["O(n log n)", "O(n)", "O(n^2)", "O(log n)"], 0,
        "Sorting is O(n log n); the linear scan afterwards doesn't change the total."),
    cx("cx-heap-topk", "top-k with a size-k heap", ["heap", "top-k"], '''
        import heapq
        h = []
        for x in nums:           # n items
            heapq.heappush(h, x)
            if len(h) > k:
                heapq.heappop(h)
    ''', ["O(n log k)", "O(n log n)", "O(n * k)", "O(k log n)"], 0,
        "The heap never exceeds k + 1 items, so each push/pop is O(log k). heapq.nlargest "
        "does the same.",
        difficulty=2),
    cx("cx-pairs", "nested loops over pairs", ["loops"], '''
        for i in range(n):
            for j in range(i + 1, n):
                if a[i] + a[j] == target:
                    return (i, j)
    ''', ["O(n^2)", "O(n log n)", "O(n)", "O(2^n)"], 0,
        "n(n-1)/2 pairs is still O(n^2). A dict of seen values (two-sum) solves it in O(n)."),
    cx("cx-bisect-queries", "binary search per query", ["bisect", "binary-search"], '''
        from bisect import bisect_left
        # arr is sorted, length n; queries has q items
        out = [bisect_left(arr, x) for x in queries]
    ''', ["O(q log n)", "O(q * n)", "O(n log q)", "O(q + n)"], 0,
        "Each bisect is O(log n) on the sorted array, done q times."),
    cx("cx-pop0", "list.pop(0) is O(n)", ["lists", "deque", "queue"], '''
        q = list(range(n))
        while q:
            x = q.pop(0)
    ''', ["O(n^2)", "O(n)", "O(n log n)", "O(1)"], 0,
        "pop(0) shifts every remaining item: O(n) each, O(n^2) total. "
        "collections.deque.popleft() is O(1), making the loop O(n).",
        ts="JS arr.shift() has the same linear cost in general."),
    cx("cx-deque", "deque popleft is O(1)", ["deque", "queue", "bfs"], '''
        from collections import deque
        q = deque(range(n))
        while q:
            x = q.popleft()
    ''', ["O(n)", "O(n^2)", "O(n log n)", "O(log n)"], 0,
        "deque supports O(1) appends and pops at both ends. Use it for every BFS queue."),
    cx("cx-str-concat", "string concatenation in a loop", ["strings"], '''
        s = ""
        for part in parts:       # n parts
            s = s + part
    ''', ["O(n^2) worst case; use ''.join(parts) for O(n)", "O(n) always",
          "O(n log n)", "O(1) per step, so O(n) guaranteed"], 0,
        "Strings are immutable, so each + can copy everything so far. CPython sometimes "
        "optimizes this in place, but it isn't guaranteed. ''.join is reliably linear.",
        difficulty=2,
        question="What is the time complexity (total characters ~ n)?"),
    cx("cx-fib-naive", "exponential recursion", ["recursion"], '''
        def fib(n):
            if n < 2:
                return n
            return fib(n - 1) + fib(n - 2)
    ''', ["O(2^n)", "O(n)", "O(n^2)", "O(n log n)"], 0,
        "Each call branches twice and recomputes the same subproblems: exponential "
        "(about 1.6^n, bounded by O(2^n))."),
    cx("cx-fib-memo", "recursion with memo", ["recursion", "memoization", "dp"], '''
        from functools import cache

        @cache
        def fib(n):
            if n < 2:
                return n
            return fib(n - 1) + fib(n - 2)
    ''', ["O(n)", "O(2^n)", "O(n log n)", "O(1)"], 0,
        "With memoization each fib(k) is computed once and later calls are O(1) cache hits, "
        "so the total is O(n) time and O(n) space."),
    cx("cx-halving", "halving loop is O(log n)", ["binary-search", "loops"], '''
        lo, hi = 0, n
        while lo < hi:
            mid = (lo + hi) // 2
            if ok(mid):
                hi = mid
            else:
                lo = mid + 1
    ''', ["O(log n) calls to ok", "O(n) calls to ok", "O(n log n)", "O(sqrt n)"], 0,
        "The range halves each iteration, so it takes about log2(n) steps."),
    cx("cx-index-then-lookup", "build index once", ["dict", "hashing"], '''
        by_id = {u["id"]: u for u in users}     # n users
        for order in orders:                     # m orders
            order["user"] = by_id[order["user_id"]]
    ''', ["O(n + m)", "O(n * m)", "O(m log n)", "O(n^2)"], 0,
        "Building the dict is O(n), and each lookup is O(1) on average. This is the standard "
        "fix for an n*m nested join."),
    cx("cx-dedupe-slice", "hidden O(n) inside a loop", ["lists", "slicing"], '''
        out = [x for i, x in enumerate(a) if x not in a[:i]]   # n items
    ''', ["O(n^2)", "O(n)", "O(n log n)", "O(1)"], 0,
        "a[:i] copies i items and `not in` scans them, inside an n-step loop. "
        "list(dict.fromkeys(a)) dedupes in O(n) and keeps order.",
        difficulty=2),
    cx("cx-bfs", "BFS is O(V + E)", ["bfs", "graphs"], '''
        from collections import deque
        seen, q = {start}, deque([start])
        while q:
            node = q.popleft()
            for nb in graph[node]:      # adjacency lists
                if nb not in seen:
                    seen.add(nb)
                    q.append(nb)
    ''', ["O(V + E)", "O(V * E)", "O(V^2)", "O(E log V)"], 0,
        "Each node is dequeued once and each edge is checked once (twice if undirected)."),
    cx("cx-ordereddict-lru", "LRU ops are O(1)", ["lru", "ordereddict", "caching"], '''
        from collections import OrderedDict
        cache = OrderedDict()
        def get(k):
            if k not in cache:
                return None
            cache.move_to_end(k)
            return cache[k]
    ''', ["O(1) per call", "O(n) per call", "O(log n) per call", "O(n) amortized"], 0,
        "OrderedDict is a hash map plus a doubly linked list, so lookup, move_to_end and "
        "popitem(last=False) are all O(1).",
        question="What is the time complexity of get?"),
]

CONCEPT = [
    concept("stop-tool-use", "tool use loop", ["claude-api", "tool-use", "stop-reason"],
            "A Messages API response comes back with stop_reason \"tool_use\". What should your "
            "code do next?",
            ["Run the requested tool(s), send the results back as tool_result blocks in a new "
             "user message, and call the API again",
             "Show the response to the user; the turn is finished",
             "Retry the same request, because the output was cut off",
             "Raise an error, because the model refused"], 0,
            "tool_use means Claude is asking for a tool call. Your loop executes it and returns a "
            "tool_result matched by tool_use_id, repeating until stop_reason is end_turn."),
    concept("stop-max-tokens", "stop reasons", ["claude-api", "stop-reason"],
            "stop_reason is \"max_tokens\". What happened?",
            ["The output hit the max_tokens limit you set and is probably truncated",
             "The model finished its answer naturally",
             "The prompt exceeded the context window",
             "A stop sequence you provided was generated"], 0,
            "max_tokens means generation was cut off at your limit. Raise the limit or continue "
            "the response. A natural finish is end_turn, and a matched stop sequence is "
            "stop_sequence."),
    concept("prompt-caching", "prompt caching", ["claude-api", "caching", "cost"],
            "What does prompt caching save you?",
            ["Cost and latency on a repeated, identical prompt prefix (e.g. a long system "
             "prompt or document), because cached reads are billed far below normal input",
             "Output tokens, because responses are reused for identical questions",
             "Nothing unless temperature is 0",
             "Rate-limit errors, because cached requests skip the API"], 0,
            "Caching stores the processed prefix up to a cache_control breakpoint. Later "
            "requests with the exact same prefix read it cheaply and faster. Responses are "
            "never cached, and any change before the breakpoint misses the cache.",
            difficulty=2),
    concept("batches", "batch vs real-time", ["claude-api", "batches", "cost"],
            "When is the Message Batches API the right call?",
            ["Large, non-urgent jobs (nightly classification, eval runs, backfills) where about "
             "50% lower cost matters more than latency",
             "A chat UI that needs streaming tokens",
             "An agent loop where each step depends on the previous tool result",
             "Any request over 1,000 tokens"], 0,
            "Batches are asynchronous, at about half the cost, with results within 24 hours "
            "(often much sooner). Interactive or step-dependent work belongs on the regular "
            "Messages API."),
    concept("cache-prefix-order", "prompt caching", ["claude-api", "caching"],
            "Your system prompt starts with today's timestamp, followed by a 20k-token policy "
            "document marked for caching. Why is the cache hit rate near zero?",
            ["The cache matches on an exact prefix, and the timestamp changes it on every "
             "request; move variable content after the cached block",
             "Caching only works on user messages",
             "Documents over 10k tokens can't be cached",
             "Cache hits require streaming to be enabled"], 0,
            "Put stable content first (tools, system, long documents) and per-request content "
            "last. Anything that changes before the breakpoint invalidates the cached prefix.",
            difficulty=2),
]

ITEMS = OUTPUT + COMPLEXITY + CONCEPT

# Spread the correct answer across positions (authored as index 0).
for _i, _it in enumerate(ITEMS):
    _n = len(_it["choices"])
    _k = (_i * 3 + 1) % _n
    _it["choices"] = _it["choices"][_k:] + _it["choices"][:_k]
    _it["answer"] = (_it["answer"] - _k) % _n
