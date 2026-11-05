"""Comeback week 1: Python syntax and reflexes."""
from _helpers import code, lines

W = {"stage": "week1", "week": 1}


def C(id, pattern, tags, title, prompt, starter, tests, hints, solution, lesson,
      ts=None, difficulty=1, alternative=None):
    it = {"id": "cb-w1-" + id, "type": "code", **W, "difficulty": difficulty,
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
    it = {"id": "cb-w1-" + id, "type": "predict", "kind": kind, **W, "difficulty": difficulty,
          "tags": tags, "pattern": pattern, "question": question, "choices": choices,
          "answer": answer, "explanation": explanation}
    if src:
        it["code"] = code(src)
    if ts:
        it["ts"] = ts
    return it


ITEMS = [
    # ---------------------------------------------------------------- strings
    C("fstring", "f-strings", ["strings", "f-strings"], "Greeting with an f-string",
      "Write `greet(name, n)` that returns `'Hi Ada, you have 3 new messages'`.",
      '''
      def greet(name, n):
          pass
      ''',
      '''
      def test_basic():
          assert greet("Ada", 3) == "Hi Ada, you have 3 new messages", f"got {greet('Ada', 3)!r}"
      def test_zero():
          assert greet("Bo", 0) == "Hi Bo, you have 0 new messages", f"got {greet('Bo', 0)!r}"
      ''',
      ["Python's template strings start with f before the quote.",
       "Inside an f-string, put expressions in {curly braces}.",
       "return f\"Hi {name}, you have ... new messages\""],
      '''
      def greet(name, n):
          return f"Hi {name}, you have {n} new messages"
      ''',
      "f-strings are Python's template literals: f\"{expr}\". Format specs go after a colon: f\"{price:.2f}\".",
      ts="`Hi ${name}, you have ${n} new messages`"),

    C("format-spec", "format spec", ["strings", "f-strings", "formatting"], "Money with a format spec",
      "Write `money(x)` that returns e.g. `'$1,234.50'` for `1234.5` (thousands separator, 2 decimals).",
      '''
      def money(x):
          pass
      ''',
      '''
      def test_thousands():
          assert money(1234.5) == "$1,234.50", f"money(1234.5) gave {money(1234.5)!r}"
      def test_small():
          assert money(3) == "$3.00", f"money(3) gave {money(3)!r}"
      def test_rounding():
          assert money(1000000.456) == "$1,000,000.46", f"got {money(1000000.456)!r}"
      ''',
      ["The format spec goes after a colon inside the braces: {x:SPEC}.",
       "'.2f' means two decimals; a comma before it adds thousands separators.",
       "return f\"${x:,.2f}\""],
      '''
      def money(x):
          return f"${x:,.2f}"
      ''',
      "Format specs live after the colon: `:,.2f` (thousands + 2 decimals), `:>8` (right-align), `:02d` (zero-pad), `:.1%` (percent).",
      ts="'$' + x.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })"),

    C("slugify", "str methods", ["strings", "methods"], "Slugify a title",
      "Write `slugify(title)`: trim surrounding whitespace, lowercase, and replace spaces with `-`.\n\n`'  Hello World '` → `'hello-world'`",
      '''
      def slugify(title):
          pass
      ''',
      '''
      def test_basic():
          assert slugify("  Hello World ") == "hello-world", f"got {slugify('  Hello World ')!r}"
      def test_three():
          assert slugify("Fast API Tips") == "fast-api-tips", f"got {slugify('Fast API Tips')!r}"
      ''',
      ["Strings have methods for each step; they return new strings (strings are immutable).",
       "The methods are .strip(), .lower() and .replace(old, new). Chain them.",
       "return title.strip().lower().replace(\" \", \"-\")"],
      '''
      def slugify(title):
          return title.strip().lower().replace(" ", "-")
      ''',
      "`strip` = JS `trim`, `lower` = `toLowerCase`, `replace` replaces ALL occurrences by default (unlike JS `replace` with a string).",
      ts="title.trim().toLowerCase().replaceAll(' ', '-')"),

    C("split-join", "split/join", ["strings", "lists"], "Reverse the words",
      "Write `reverse_words(s)`: `'the quick  fox'` → `'fox quick the'` (collapse extra spaces).",
      '''
      def reverse_words(s):
          pass
      ''',
      '''
      def test_basic():
          assert reverse_words("the quick  fox") == "fox quick the", f"got {reverse_words('the quick  fox')!r}"
      def test_single():
          assert reverse_words("  hi ") == "hi", f"got {reverse_words('  hi ')!r}"
      ''',
      ["split() with no argument splits on any run of whitespace and drops empties.",
       "Reverse the list with a slice, then glue it back with a string's join method.",
       "return \" \".join(s.split()[::-1])"],
      '''
      def reverse_words(s):
          return " ".join(s.split()[::-1])
      ''',
      "In Python `join` is a method on the separator: `\" \".join(parts)`. `s.split()` (no arg) handles any whitespace run.",
      ts="s.trim().split(/\\s+/).reverse().join(' ')",
      alternative='''
      def reverse_words(s):
          return " ".join(reversed(s.split()))
      '''),

    C("palindrome", "slicing", ["strings", "slicing", "comprehension"], "Palindrome check",
      "Write `is_palindrome(s)` that ignores case and anything that is not a letter or digit.\n\n`'A man, a plan, a canal: Panama'` → `True`",
      '''
      def is_palindrome(s):
          pass
      ''',
      '''
      def test_true():
          assert is_palindrome("A man, a plan, a canal: Panama") is True, "classic palindrome should be True"
      def test_false():
          assert is_palindrome("race a car") is False, "'race a car' is not a palindrome"
      def test_empty():
          assert is_palindrome("") is True, "empty string counts as a palindrome"
      ''',
      ["First build a cleaned, lowercased string; then compare it with its reverse.",
       "c.isalnum() tests a character; \"\".join(... for c in s) builds the cleaned string; s[::-1] reverses.",
       "t = \"\".join(c.lower() for c in s if c.isalnum()); return t == t[::-1]"],
      '''
      def is_palindrome(s):
          t = "".join(c.lower() for c in s if c.isalnum())
          return t == t[::-1]
      ''',
      "`s[::-1]` reverses any sequence. A generator inside `\"\".join(...)` is the idiomatic way to filter characters.",
      ts="const t = s.toLowerCase().replace(/[^a-z0-9]/g, ''); return t === [...t].reverse().join('')"),

    # ---------------------------------------------------------------- lists & comprehensions
    C("list-comp", "list comprehension", ["lists", "comprehension"], "Squares of the evens",
      "Write `even_squares(nums)` returning the squares of the even numbers, in order, in ONE expression.",
      '''
      def even_squares(nums):
          pass
      ''',
      '''
      def test_basic():
          assert even_squares([1, 2, 3, 4]) == [4, 16], f"got {even_squares([1, 2, 3, 4])!r}"
      def test_empty():
          assert even_squares([]) == [], "empty in, empty out"
      def test_negative():
          assert even_squares([-2, 5]) == [4], f"got {even_squares([-2, 5])!r}"
      ''',
      ["A list comprehension is [expression for item in iterable if condition].",
       "Even means n % 2 == 0; square is n * n or n ** 2.",
       "return [n * n for n in nums if n % 2 == 0]"],
      '''
      def even_squares(nums):
          return [n * n for n in nums if n % 2 == 0]
      ''',
      "`[expr for x in xs if cond]` replaces `.filter().map()`. Read it left to right: what you produce, then where it comes from, then the filter.",
      ts="nums.filter(n => n % 2 === 0).map(n => n * n)"),

    C("flatten", "nested comprehension", ["lists", "comprehension"], "Flatten a grid",
      "Write `flatten(grid)`: `[[1, 2], [3], []]` → `[1, 2, 3]`, using a single comprehension.",
      '''
      def flatten(grid):
          pass
      ''',
      '''
      def test_basic():
          assert flatten([[1, 2], [3], []]) == [1, 2, 3], f"got {flatten([[1, 2], [3], []])!r}"
      def test_empty():
          assert flatten([]) == [], "empty grid gives []"
      ''',
      ["Two `for` clauses can live in one comprehension.",
       "The for clauses go in the same order as nested loops: outer first.",
       "return [x for row in grid for x in row]"],
      '''
      def flatten(grid):
          return [x for row in grid for x in row]
      ''',
      "Nested comprehensions read like nested loops written on one line: `[x for row in grid for x in row]` — outer loop first.",
      ts="grid.flat()"),

    # ---------------------------------------------------------------- dicts & sets
    C("dict-get", "dict.get", ["dict", "counting"], "Count words with dict.get",
      "Write `count_words(words)` returning a dict word → count, using a plain dict (no imports).",
      '''
      def count_words(words):
          pass
      ''',
      '''
      def test_basic():
          got = count_words(["a", "b", "a"])
          assert got == {"a": 2, "b": 1}, f"got {got!r}"
      def test_empty():
          assert count_words([]) == {}, "no words gives {}"
      ''',
      ["Loop over words and bump a counter for each one.",
       "d.get(key, default) returns the default instead of raising KeyError.",
       "counts[w] = counts.get(w, 0) + 1"],
      '''
      def count_words(words):
          counts = {}
          for w in words:
              counts[w] = counts.get(w, 0) + 1
          return counts
      ''',
      "`d[k]` raises KeyError for a missing key; `d.get(k, 0)` doesn't. (Week 2: `collections.Counter` does this for you.)",
      ts="counts[w] = (counts[w] ?? 0) + 1"),

    C("dict-comp", "dict comprehension", ["dict", "comprehension"], "Invert a dict",
      "Write `invert(d)` that swaps keys and values: `{'a': 1, 'b': 2}` → `{1: 'a', 2: 'b'}`.",
      '''
      def invert(d):
          pass
      ''',
      '''
      def test_basic():
          assert invert({"a": 1, "b": 2}) == {1: "a", 2: "b"}, f"got {invert({'a': 1, 'b': 2})!r}"
      def test_empty():
          assert invert({}) == {}, "empty dict gives {}"
      ''',
      ["A dict comprehension uses braces and key: value.",
       "d.items() yields (key, value) pairs you can unpack in the for clause.",
       "return {v: k for k, v in d.items()}"],
      '''
      def invert(d):
          return {v: k for k, v in d.items()}
      ''',
      "`{k: v for ...}` builds a dict; iterate `d.items()` to get key and value together (plain `for k in d` gives keys only).",
      ts="Object.fromEntries(Object.entries(d).map(([k, v]) => [v, k]))"),

    C("set-ops", "set operations", ["set"], "Common elements",
      "Write `common(a, b)` returning the values present in both lists, sorted ascending, without duplicates.",
      '''
      def common(a, b):
          pass
      ''',
      '''
      def test_basic():
          assert common([3, 1, 2, 2], [2, 3, 4]) == [2, 3], f"got {common([3, 1, 2, 2], [2, 3, 4])!r}"
      def test_none():
          assert common([1], [2]) == [], "nothing shared gives []"
      ''',
      ["Turn both lists into sets.",
       "The & operator is set intersection; sorted() turns any iterable into a sorted list.",
       "return sorted(set(a) & set(b))"],
      '''
      def common(a, b):
          return sorted(set(a) & set(b))
      ''',
      "Sets have operators: `&` intersection, `|` union, `-` difference, `^` symmetric difference. Membership is O(1) on average.",
      ts="[...new Set(a)].filter(x => new Set(b).has(x)).sort((x, y) => x - y)"),

    # ---------------------------------------------------------------- loops, enumerate, zip
    C("enumerate", "enumerate", ["loops", "enumerate"], "Numbered list",
      "Write `numbered(items)`: `['eggs', 'milk']` → `['1. eggs', '2. milk']`.",
      '''
      def numbered(items):
          pass
      ''',
      '''
      def test_basic():
          assert numbered(["eggs", "milk"]) == ["1. eggs", "2. milk"], f"got {numbered(['eggs', 'milk'])!r}"
      def test_empty():
          assert numbered([]) == [], "empty in, empty out"
      ''',
      ["Don't use range(len(items)): there's a builtin that yields (index, item).",
       "enumerate(items, start=1) starts counting at 1.",
       "return [f\"{i}. {x}\" for i, x in enumerate(items, start=1)]"],
      '''
      def numbered(items):
          return [f"{i}. {x}" for i, x in enumerate(items, start=1)]
      ''',
      "`enumerate(xs, start=1)` gives (index, value) pairs — Python's answer to `forEach((x, i) => ...)`.",
      ts="items.map((x, i) => `${i + 1}. ${x}`)"),

    C("zip", "zip", ["loops", "zip", "dict"], "Zip into a dict",
      "Write `to_dict(keys, values)`: `(['a', 'b'], [1, 2])` → `{'a': 1, 'b': 2}`. One line.",
      '''
      def to_dict(keys, values):
          pass
      ''',
      '''
      def test_basic():
          assert to_dict(["a", "b"], [1, 2]) == {"a": 1, "b": 2}, f"got {to_dict(['a', 'b'], [1, 2])!r}"
      def test_uneven():
          assert to_dict(["a", "b", "c"], [1]) == {"a": 1}, "zip stops at the shorter input"
      ''',
      ["There's a builtin that walks two iterables in lockstep.",
       "zip(keys, values) yields pairs; dict() accepts an iterable of pairs.",
       "return dict(zip(keys, values))"],
      '''
      def to_dict(keys, values):
          return dict(zip(keys, values))
      ''',
      "`zip(a, b)` pairs items and stops at the shortest input (`zip(a, b, strict=True)` raises instead). `dict(pairs)` builds a dict.",
      ts="Object.fromEntries(keys.map((k, i) => [k, values[i]]))"),

    C("fizzbuzz", "for loop + print", ["loops", "print"], "FizzBuzz to 15 (print it)",
      "At top level, PRINT the numbers 1..15, one per line, but `Fizz` for multiples of 3, `Buzz` for 5, `FizzBuzz` for both.",
      '''
      for i in range(1, 16):
          pass
      ''',
      '''
      EXPECTED = ["1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz",
                  "11", "Fizz", "13", "14", "FizzBuzz"]
      def test_output():
          got = captured_output.split()
          assert got == EXPECTED, f"expected {EXPECTED}, printed {got}"
      ''',
      ["range(1, 16) stops BEFORE 16. Use % to test divisibility.",
       "Check the 'both' case first (i % 15 == 0), then 3, then 5, else the number.",
       "if i % 15 == 0: print(\"FizzBuzz\") / elif i % 3 == 0: ... / elif i % 5 == 0: ... / else: print(i)"],
      '''
      for i in range(1, 16):
          if i % 15 == 0:
              print("FizzBuzz")
          elif i % 3 == 0:
              print("Fizz")
          elif i % 5 == 0:
              print("Buzz")
          else:
              print(i)
      ''',
      "`range(a, b)` is half-open [a, b). It's `elif`, not `else if`. `print` adds a newline itself.",
      ts="for (let i = 1; i <= 15; i++) console.log(i % 15 === 0 ? 'FizzBuzz' : ...)"),

    # ---------------------------------------------------------------- sorted / min / max
    C("sorted-key", "sorted key=", ["sorting", "lambda"], "Longest first, ties alphabetical",
      "Write `longest_first(words)`: sort by length descending; equal lengths in alphabetical order.",
      '''
      def longest_first(words):
          pass
      ''',
      '''
      def test_basic():
          got = longest_first(["bb", "a", "ccc", "aa"])
          assert got == ["ccc", "aa", "bb", "a"], f"got {got!r}"
      def test_no_mutation():
          w = ["b", "aa"]
          longest_first(w)
          assert w == ["b", "aa"], "don't sort the caller's list in place"
      ''',
      ["sorted() returns a new list and takes a key= function.",
       "A key can return a tuple: it compares element by element. Negate the length to get descending.",
       "return sorted(words, key=lambda w: (-len(w), w))"],
      '''
      def longest_first(words):
          return sorted(words, key=lambda w: (-len(w), w))
      ''',
      "Python sorts with `key=` (a one-arg function), not a comparator. Tuple keys give multi-level sorts; `-x` flips one level.",
      ts="[...words].sort((a, b) => b.length - a.length || a.localeCompare(b))"),

    C("max-key", "max key=", ["sorting", "lambda", "dict"], "Oldest person",
      "`people` is a list of dicts like `{'name': 'Ada', 'age': 36}`. Write `oldest(people)` returning the NAME of the oldest.",
      '''
      def oldest(people):
          pass
      ''',
      '''
      PEOPLE = [{"name": "Ada", "age": 36}, {"name": "Linus", "age": 54}, {"name": "Grace", "age": 45}]
      def test_basic():
          assert oldest(PEOPLE) == "Linus", f"got {oldest(PEOPLE)!r}"
      def test_one():
          assert oldest([{"name": "Bo", "age": 1}]) == "Bo", "single person"
      ''',
      ["max() takes the same key= argument as sorted().",
       "The key gets one person dict and returns what to compare: p[\"age\"].",
       "return max(people, key=lambda p: p[\"age\"])[\"name\"]"],
      '''
      def oldest(people):
          return max(people, key=lambda p: p["age"])["name"]
      ''',
      "`max(xs, key=f)` / `min(xs, key=f)` return the ELEMENT with the biggest f(x) — no reduce needed. Add `default=` for empty inputs.",
      ts="people.reduce((a, b) => (b.age > a.age ? b : a)).name"),

    # ---------------------------------------------------------------- functions
    C("defaults-kwargs", "default args", ["functions", "keyword args"], "Defaults and keyword args",
      "Write `make_url(path, host='localhost', port=8000)` returning `'http://HOST:PORT/PATH'`.",
      '''
      def make_url(path):
          pass
      ''',
      '''
      def test_defaults():
          assert make_url("api") == "http://localhost:8000/api", f"got {make_url('api')!r}"
      def test_keyword():
          got = make_url("x", port=9000)
          assert got == "http://localhost:9000/x", f"make_url('x', port=9000) gave {got!r}"
      def test_all():
          assert make_url("y", "example.com", 80) == "http://example.com:80/y", "positional host and port"
      ''',
      ["Default values go in the signature: def f(a, b=1).",
       "Callers can skip host and pass port=9000 by name; your signature needs both defaults.",
       "def make_url(path, host=\"localhost\", port=8000): return f\"http://{host}:{port}/{path}\""],
      '''
      def make_url(path, host="localhost", port=8000):
          return f"http://{host}:{port}/{path}"
      ''',
      "Any parameter can be passed by name (`port=9000`), so Python rarely needs an options object. Defaults must come after non-defaults.",
      ts="function makeUrl(path: string, { host = 'localhost', port = 8000 } = {})"),

    C("star-args", "*args", ["functions", "args"], "Sum any number of args",
      "Write `total(...)` so that `total()` → 0, `total(1, 2, 3)` → 6.",
      '''
      def total():
          pass
      ''',
      '''
      def test_many():
          assert total(1, 2, 3) == 6, f"total(1, 2, 3) gave {total(1, 2, 3)!r}"
      def test_none():
          assert total() == 0, "total() should be 0"
      def test_spread():
          nums = [4, 5]
          assert total(*nums) == 9, "total(*nums) should spread the list"
      ''',
      ["A starred parameter collects extra positional args into a tuple.",
       "def total(*nums): ... and nums is a tuple; sum() adds an iterable.",
       "def total(*nums): return sum(nums)"],
      '''
      def total(*nums):
          return sum(nums)
      ''',
      "`*args` collects positionals into a tuple (TS rest params). At the CALL site, `f(*xs)` spreads a list and `f(**d)` spreads a dict.",
      ts="function total(...nums: number[]) { return nums.reduce((a, b) => a + b, 0) }"),

    C("kwargs", "**kwargs", ["functions", "kwargs"], "HTML tag with **kwargs",
      "Write `tag(name, **attrs)`: `tag('a', href='/', id='x')` → `'<a href=\"/\" id=\"x\">'`. Keep the order the attrs were passed.",
      '''
      def tag(name):
          pass
      ''',
      '''
      def test_attrs():
          got = tag("a", href="/", id="x")
          assert got == '<a href="/" id="x">', f"got {got!r}"
      def test_bare():
          assert tag("br") == "<br>", f"tag('br') gave {tag('br')!r}"
      ''',
      ["**attrs collects keyword args into a dict (insertion order is kept).",
       "Build ' key=\"value\"' for each item in attrs.items() and join them.",
       "parts = \"\".join(f' {k}=\"{v}\"' for k, v in attrs.items()); return f\"<{name}{parts}>\""],
      '''
      def tag(name, **attrs):
          parts = "".join(f' {k}="{v}"' for k, v in attrs.items())
          return f"<{name}{parts}>"
      ''',
      "`**kwargs` collects named args into a dict. Dicts keep insertion order (guaranteed since 3.7).",
      ts="function tag(name: string, attrs: Record<string, string> = {})"),

    C("kw-only", "keyword-only args", ["functions", "keyword args"], "Force a keyword argument",
      "Write `connect(host, timeout=5)` returning `f'{host}:{timeout}'`, but make `timeout` keyword-only: `connect('db', 10)` must raise TypeError.",
      '''
      def connect(host, timeout=5):
          pass
      ''',
      '''
      def test_default():
          assert connect("db") == "db:5", f"got {connect('db')!r}"
      def test_named():
          assert connect("db", timeout=10) == "db:10", "timeout=10 should work"
      def test_positional_rejected():
          try:
              connect("db", 10)
          except TypeError:
              return
          assert False, "connect('db', 10) should raise TypeError (timeout is keyword-only)"
      ''',
      ["A bare marker in the parameter list makes everything after it keyword-only.",
       "The marker is a lone star: def f(a, *, b=1).",
       "def connect(host, *, timeout=5): return f\"{host}:{timeout}\""],
      '''
      def connect(host, *, timeout=5):
          return f"{host}:{timeout}"
      ''',
      "A bare `*` in the signature forces the following params to be named — great for booleans and timeouts (`sort(key=..., reverse=True)` works this way).",
      ts="function connect(host: string, { timeout = 5 }: { timeout?: number } = {})"),

    C("main-guard", "__name__ guard", ["modules", "functions"], "The main guard",
      "Define `main()` that prints `ready`, and call it ONLY when the file is run as a script (not when imported).",
      '''
      def main():
          pass
      ''',
      '''
      import io, contextlib
      def test_main_prints():
          buf = io.StringIO()
          with contextlib.redirect_stdout(buf):
              main()
          assert buf.getvalue().strip() == "ready", f"main() printed {buf.getvalue()!r}"
      def test_not_run_on_import():
          assert captured_output == "", "main() ran on import — wrap the call in the __name__ check"
      ''',
      ["Python sets a module-level variable to \"__main__\" only for the file you run directly.",
       "if __name__ == \"__main__\": goes at the bottom, unindented.",
       "def main(): print(\"ready\")  then  if __name__ == \"__main__\": main()"],
      '''
      def main():
          print("ready")


      if __name__ == "__main__":
          main()
      ''',
      "`if __name__ == \"__main__\":` runs code only when the file is executed directly, so the module stays importable (and testable) without side effects.",
      ts="if (require.main === module) main()  // or import.meta.main"),

    # ---------------------------------------------------------------- exceptions
    C("try-except", "try/except", ["exceptions"], "Parse an int safely",
      "Write `parse_int(s, default=0)` returning `int(s)`, or `default` if `s` isn't a valid integer.",
      '''
      def parse_int(s, default=0):
          pass
      ''',
      '''
      def test_ok():
          assert parse_int("42") == 42, f"got {parse_int('42')!r}"
      def test_bad():
          assert parse_int("4x") == 0, f"got {parse_int('4x')!r}"
      def test_custom_default():
          assert parse_int("", default=-1) == -1, "should return the given default"
      ''',
      ["int('4x') raises an exception; catch that specific one.",
       "The exception is ValueError. Avoid a bare except: it hides real bugs.",
       "try: return int(s) / except ValueError: return default"],
      '''
      def parse_int(s, default=0):
          try:
              return int(s)
          except ValueError:
              return default
      ''',
      "Catch the narrowest exception (`except ValueError:`), never a bare `except:`. Python favours EAFP: try it, handle the failure.",
      ts="const n = Number.parseInt(s, 10); return Number.isNaN(n) ? def : n"),

    C("raise", "raise", ["exceptions"], "Raise on bad input",
      "Write `withdraw(balance, amount)` returning the new balance, but raise `ValueError('insufficient funds')` if `amount > balance`.",
      '''
      def withdraw(balance, amount):
          pass
      ''',
      '''
      def test_ok():
          assert withdraw(100, 30) == 70, f"got {withdraw(100, 30)!r}"
      def test_raises():
          try:
              withdraw(10, 50)
          except ValueError as e:
              assert "insufficient" in str(e), f"message was {e!r}"
              return
          assert False, "withdraw(10, 50) should raise ValueError"
      ''',
      ["Python uses raise, not throw.",
       "Create the exception by calling the class with a message: ValueError(\"...\").",
       "if amount > balance: raise ValueError(\"insufficient funds\")"],
      '''
      def withdraw(balance, amount):
          if amount > balance:
              raise ValueError("insufficient funds")
          return balance - amount
      ''',
      "`raise ValueError(\"msg\")` — pick a built-in that fits (ValueError for bad values, TypeError for wrong types, KeyError for missing keys).",
      ts="if (amount > balance) throw new Error('insufficient funds')"),

    C("try-else-finally", "try/else/finally", ["exceptions"], "try / except / else / finally",
      "Write `safe_div(a, b, log)`: return `a / b`, or `None` on division by zero. Append to `log`: `'div0'` on error, `'ok'` on success, and ALWAYS `'done'` last.",
      '''
      def safe_div(a, b, log):
          pass
      ''',
      '''
      def test_ok():
          log = []
          assert safe_div(6, 3, log) == 2, "6 / 3 should be 2"
          assert log == ["ok", "done"], f"log was {log}"
      def test_zero():
          log = []
          assert safe_div(1, 0, log) is None, "division by zero returns None"
          assert log == ["div0", "done"], f"log was {log}"
      ''',
      ["`else:` runs only if the try block raised nothing; `finally:` runs no matter what — even after return.",
       "Put the division in try, catch ZeroDivisionError, log 'ok' in else, 'done' in finally.",
       "try: r = a / b / except ZeroDivisionError: log.append(\"div0\"); return None / else: log.append(\"ok\"); return r / finally: log.append(\"done\")"],
      '''
      def safe_div(a, b, log):
          try:
              r = a / b
          except ZeroDivisionError:
              log.append("div0")
              return None
          else:
              log.append("ok")
              return r
          finally:
              log.append("done")
      ''',
      "`else` keeps the happy path out of the try (so you don't accidentally catch its errors); `finally` is for cleanup and runs even after `return`.",
      ts="try { ... } catch (e) { ... } finally { ... }  // TS has no else clause",
      difficulty=2),

    # ---------------------------------------------------------------- integer division / modulo
    C("divmod", "divmod", ["math", "f-strings", "formatting"], "Seconds to HH:MM:SS",
      "Write `to_hms(seconds)`: `3723` → `'01:02:03'`.",
      '''
      def to_hms(seconds):
          pass
      ''',
      '''
      def test_basic():
          assert to_hms(3723) == "01:02:03", f"got {to_hms(3723)!r}"
      def test_zero():
          assert to_hms(0) == "00:00:00", f"got {to_hms(0)!r}"
      def test_big():
          assert to_hms(36000 + 59) == "10:00:59", f"got {to_hms(36059)!r}"
      ''',
      ["// is integer division and % is remainder; divmod(a, b) returns both at once.",
       "h, rest = divmod(seconds, 3600); m, s = divmod(rest, 60). Zero-pad with the format spec :02.",
       "return f\"{h:02}:{m:02}:{s:02}\""],
      '''
      def to_hms(seconds):
          h, rest = divmod(seconds, 3600)
          m, s = divmod(rest, 60)
          return f"{h:02}:{m:02}:{s:02}"
      ''',
      "`/` always gives a float in Python 3; `//` floors. `divmod(a, b)` returns `(a // b, a % b)` — unpack it directly.",
      ts="const h = Math.floor(s / 3600); ... String(h).padStart(2, '0')"),

    # ---------------------------------------------------------------- predict
    {
        "id": "cb-w1-slice-rev", "type": "predict", "kind": "output", **W,
        "difficulty": 1, "tags": ["slicing"], "pattern": "slicing",
        "code": code('''
            s = "python"
            print(s[::-1][:3])
        '''),
        "question": "What does this print?",
        "choices": ["noh", "pyt", "nohtyp", "hon"],
        "answer": 0,
        "explanation": "s[::-1] reverses to 'nohtyp'; [:3] takes the first three characters.",
        "ts": "[...s].reverse().join('').slice(0, 3)",
    },
    P("slice-neg", "slicing", ["slicing", "lists"],
      '''
      xs = [10, 20, 30, 40, 50]
      print(xs[-2:], xs[1:-1])
      ''',
      ["[40, 50] [20, 30, 40]", "[40] [20, 30, 40, 50]", "[50, 40] [20, 30, 40]", "[40, 50] [20, 30]"], 0,
      "Negative indexes count from the end. Slices are half-open: xs[1:-1] drops the first and last element.",
      ts="xs.slice(-2), xs.slice(1, -1)"),
    P("truthiness", "truthiness", ["truthiness"],
      '''
      print(bool([]), bool("0"), bool(0.0), bool({}))
      ''',
      ["False True False False", "False False False False", "True True False True", "False True True False"], 0,
      "Empty containers and zero are falsy. \"0\" is a non-empty string, so it's truthy. Same as JS except [] and {} — those are truthy in JS but falsy in Python.",
      ts="In JS, [] and {} are truthy; in Python they're falsy."),
    P("floordiv", "integer division", ["math"],
      '''
      print(7 // 2, -7 // 2, -7 % 3, 7 / 2)
      ''',
      ["3 -4 2 3.5", "3 -3 -1 3.5", "3 -4 -1 3", "3 -3 2 3.5"], 0,
      "// floors toward negative infinity (so -7 // 2 is -4, not -3), and % takes the sign of the divisor (-7 % 3 is 2). / always returns a float.",
      ts="Math.trunc(-7 / 2) is -3 and -7 % 3 is -1 in JS — Python differs on both."),
    P("alias", "mutability", ["lists", "mutability"],
      '''
      a = [1, 2]
      b = a
      b.append(3)
      c = a[:]
      c.append(4)
      print(a)
      ''',
      ["[1, 2, 3]", "[1, 2]", "[1, 2, 3, 4]", "[1, 2, 4]"], 0,
      "b = a copies the reference, so appending via b changes a. a[:] (or list(a) / a.copy()) makes a shallow copy, so c is independent.",
      ts="Same as JS: const b = a shares; [...a] copies."),
    P("star-unpack", "unpacking", ["unpacking"],
      '''
      first, *rest = [1, 2, 3, 4]
      print(first, rest)
      ''',
      ["1 [2, 3, 4]", "1 (2, 3, 4)", "1 2", "[1] [2, 3, 4]"], 0,
      "A starred target collects the remaining items into a LIST (not a tuple). Unpacking works on any iterable; `a, b = b, a` is the swap idiom.",
      ts="const [first, ...rest] = [1, 2, 3, 4]"),
    P("set-comp", "set comprehension", ["set", "comprehension"],
      '''
      words = ["hi", "yo", "hey", "a"]
      print(sorted({len(w) for w in words}))
      ''',
      ["[1, 2, 3]", "[2, 2, 3, 1]", "[1, 2, 2, 3]", "{1, 2, 3}"], 0,
      "Braces without a colon make a SET comprehension, so duplicate lengths collapse. sorted() returns a list.",
      ts="[...new Set(words.map(w => w.length))].sort()"),
    P("is-vs-eq", "== vs is", ["identity", "equality"],
      '''
      a = [1, 2]
      b = [1, 2]
      print(a == b, a is b, None is None)
      ''',
      ["True False True", "False False True", "True True True", "False False False"], 0,
      "== compares values (deep, for lists); `is` compares identity. Use `is` only for None/True/False singletons: `if x is None:`.",
      ts="Python == on lists is like a deep-equal; `is` is like JS ===  on objects."),
    P("str-immutable", "str methods", ["strings"],
      '''
      s = "abc"
      s.upper()
      t = s.replace("b", "B")
      print(s, t)
      ''',
      ["abc aBc", "ABC aBc", "ABC ABC", "aBc aBc"], 0,
      "Strings are immutable: methods return a NEW string. s.upper() result is thrown away, so s is still 'abc'.",
      ts="Same in JS: s.toUpperCase() doesn't change s."),
    P("in-complexity", "in operator", ["set", "lists", "big-o"], None,
      ["list O(n), set O(1) average", "both O(1)", "both O(n)", "list O(log n), set O(1)"], 0,
      "`in` on a list scans every element. Sets and dicts hash the value, so lookup is O(1) on average. Convert to a set when you test membership in a loop.",
      question="Time complexity of `x in my_list` vs `x in my_set` (n elements)?",
      kind="complexity", ts="array.includes(x) is O(n); set.has(x) is O(1)."),
    P("name-main", "__name__ guard", ["modules"], None,
      ["Only 'A'", "'A' then 'B'", "Nothing", "Only 'B'"], 0,
      "When imported, the module's __name__ is 'utils', not '__main__', so the guarded block is skipped. Top-level code still runs on import.",
      question="utils.py contains `print('A')` and then `if __name__ == \"__main__\": print('B')`. Another file does `import utils`. What prints?",
      kind="concept"),

    # ---------------------------------------------------------------- parsons
    {
        "id": "cb-w1-parsons-word-freq", "type": "parsons", **W, "difficulty": 1,
        "tags": ["dict", "loops", "strings"], "pattern": "dict.get",
        "title": "Most frequent word",
        "prompt": "Arrange the lines so `most_frequent(text)` returns the most common lowercase word.",
        "lines": lines('''
            def most_frequent(text):
                counts = {}
                for word in text.lower().split():
                    counts[word] = counts.get(word, 0) + 1
                return max(counts, key=counts.get)
        '''),
        "tests": code('''
            def test_basic():
                assert most_frequent("the cat The dog the") == "the", "'the' appears 3 times"
            def test_single():
                assert most_frequent("hi") == "hi", "single word"
        '''),
        "lesson": "`max(d, key=d.get)` returns the key with the largest value — iterating a dict yields its keys.",
    },
    {
        "id": "cb-w1-parsons-to-ints", "type": "parsons", **W, "difficulty": 1,
        "tags": ["exceptions", "loops"], "pattern": "try/except",
        "title": "Keep only valid ints",
        "prompt": "Arrange the lines so `to_ints(strs)` converts each string to int and skips the invalid ones.",
        "lines": lines('''
            def to_ints(strs):
                out = []
                for s in strs:
                    try:
                        out.append(int(s))
                    except ValueError:
                        continue
                return out
        '''),
        "tests": code('''
            def test_mixed():
                assert to_ints(["1", "x", "3"]) == [1, 3], f"got {to_ints(['1', 'x', '3'])!r}"
            def test_empty():
                assert to_ints([]) == [], "empty in, empty out"
        '''),
        "lesson": "Keep the `try` body tiny (just the line that can fail) and catch the specific exception; `continue` skips to the next item.",
    },

    # ---------------------------------------------------------------- bugs
    {
        "id": "cb-w1-bug-mutable-default", "type": "bug", **W, "difficulty": 2,
        "tags": ["functions", "mutability"], "pattern": "mutable default arg",
        "title": "The list that remembers",
        "code": code('''
            def add_item(item, bucket=[]):
                bucket.append(item)
                return bucket
        '''),
        "bugLine": 1,
        "fixed": code('''
            def add_item(item, bucket=None):
                bucket = [] if bucket is None else bucket
                bucket.append(item)
                return bucket
        '''),
        "tests": code('''
            def test_fresh_each_call():
                assert add_item(1) == [1], "first call"
                assert add_item(2) == [2], "second call should start with a fresh list, got the old one"
            def test_given_bucket():
                b = [0]
                assert add_item(1, b) == [0, 1], "should append to the given list"
        '''),
        "choices": [
            "Default `bucket=None` and create a new list inside when it's None",
            "Return `bucket.copy()` instead of `bucket`",
            "Use `bucket += [item]` instead of append",
            "Move `bucket=[]` to the first line of the body and keep the default",
        ],
        "answer": 0,
        "explanation": "Default values are evaluated ONCE, when `def` runs, so every call shares the same list. Use `None` as the default and build a new list inside.",
    },
    {
        "id": "cb-w1-bug-sort-none", "type": "bug", **W, "difficulty": 1,
        "tags": ["sorting", "lists"], "pattern": "sort vs sorted",
        "title": "Top three scores",
        "code": code('''
            def top3(scores):
                ranked = scores.sort(reverse=True)
                return ranked[:3]
        '''),
        "bugLine": 2,
        "fixed": code('''
            def top3(scores):
                ranked = sorted(scores, reverse=True)
                return ranked[:3]
        '''),
        "tests": code('''
            def test_top3():
                assert top3([5, 1, 9, 7, 3]) == [9, 7, 5], f"got {top3([5, 1, 9, 7, 3])!r}"
            def test_no_mutation():
                s = [2, 1, 3]
                top3(s)
                assert s == [2, 1, 3], "don't reorder the caller's list"
        '''),
        "choices": [
            "Use `sorted(scores, reverse=True)` — `list.sort()` sorts in place and returns None",
            "Change the slice to `ranked[-3:]`",
            "Use `scores.sort(reversed=True)`",
            "Wrap it: `list(scores.sort(reverse=True))`",
        ],
        "answer": 0,
        "explanation": "`list.sort()` mutates and returns `None` (unlike JS `arr.sort()`, which returns the array). `sorted(xs)` returns a new list and leaves the input alone.",
    },
]
