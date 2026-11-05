from _helpers import code, lines

W = {"stage": "week3", "week": 3}

ITEMS = [
    # ------------------------------------------------------------------ hashing
    {
        **W, "id": "cb-w3-two-sum", "type": "code", "difficulty": 2,
        "tags": ["hashing", "dict"], "pattern": "hash map lookup",
        "title": "Two sum in one pass",
        "prompt": "Write `two_sum(nums, target)` returning the indices `(i, j)` with `i < j` and "
                  "`nums[i] + nums[j] == target`, or `None`. Aim for O(n).",
        "starter": code('''
            def two_sum(nums, target):
                pass
        '''),
        "tests": code('''
            def test_basic():
                assert two_sum([2, 7, 11, 15], 9) == (0, 1), "2 + 7 = 9"
            def test_later_pair():
                assert two_sum([3, 2, 4], 6) == (1, 2), "2 + 4 = 6, not 3 + 3 (same index)"
            def test_duplicates():
                assert two_sum([3, 3], 6) == (0, 1), "two different 3s"
            def test_none():
                assert two_sum([1, 2], 7) is None, "no pair -> None"
        '''),
        "hints": ["For each number, which partner value would you need?",
                  "Keep a dict from value -> index of what you've already seen.",
                  "need = target - x; if need in seen: return (seen[need], i); then seen[x] = i"],
        "solution": code('''
            def two_sum(nums, target):
                seen = {}
                for i, x in enumerate(nums):
                    need = target - x
                    if need in seen:
                        return (seen[need], i)
                    seen[x] = i
                return None
        '''),
        "lesson": "Trade memory for time: a dict of 'things seen so far' turns an O(n²) pair search "
                  "into one O(n) pass. Check before you insert so an element never pairs with itself.",
        "alternative": "Sort (value, index) pairs and walk two pointers inward: O(n log n) time, "
                       "O(n) for the pairs, but the idea generalises to 3-sum.",
        "ts": "const seen = new Map<number, number>(); if (seen.has(need)) return [seen.get(need)!, i];",
    },
    {
        **W, "id": "cb-w3-group-anagrams", "type": "code", "difficulty": 2,
        "tags": ["hashing", "defaultdict"], "pattern": "group by canonical key",
        "title": "Group anagrams",
        "prompt": "Write `group_anagrams(words)` returning a list of groups (lists) of words that are "
                  "anagrams of each other. Keep words in input order inside each group and groups in "
                  "order of first appearance.",
        "starter": code('''
            def group_anagrams(words):
                pass
        '''),
        "tests": code('''
            def test_basic():
                got = group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
                assert got == [["eat", "tea", "ate"], ["tan", "nat"], ["bat"]], f"got {got}"
            def test_empty():
                assert group_anagrams([]) == [], "no words -> no groups"
            def test_single():
                assert group_anagrams(["a"]) == [["a"]]
        '''),
        "hints": ["Anagrams look identical once you put their letters in a canonical order.",
                  "Use the sorted letters as a dict key; a defaultdict(list) collects the group.",
                  "groups[''.join(sorted(w))].append(w); return list(groups.values())"],
        "solution": code('''
            from collections import defaultdict

            def group_anagrams(words):
                groups = defaultdict(list)
                for w in words:
                    groups["".join(sorted(w))].append(w)
                return list(groups.values())
        '''),
        "lesson": "Grouping = pick a canonical key, then dict[key].append(item). Python dicts keep "
                  "insertion order, so group order follows first appearance for free.",
        "alternative": "Key by a 26-count tuple (tuple(Counter(w)...)) — O(k) per word instead of "
                       "O(k log k), but uglier and only worth it for long words.",
        "ts": "const key = [...w].sort().join(''); (groups.get(key) ?? groups.set(key, []).get(key)!).push(w);",
    },
    {
        **W, "id": "cb-w3-first-unique", "type": "code", "difficulty": 1,
        "tags": ["hashing", "Counter"], "pattern": "count then scan",
        "title": "First unique character",
        "prompt": "Write `first_unique(s)` returning the index of the first character that appears "
                  "exactly once, or `-1`.",
        "starter": code('''
            def first_unique(s):
                pass
        '''),
        "tests": code('''
            def test_basic():
                assert first_unique("leetcode") == 0, "'l' is unique"
            def test_middle():
                assert first_unique("loveleetcode") == 2, "'v' at index 2"
            def test_none():
                assert first_unique("aabb") == -1, "no unique char -> -1"
            def test_empty():
                assert first_unique("") == -1
        '''),
        "hints": ["Two passes: one to count, one to find.",
                  "collections.Counter(s) gives you counts in one line.",
                  "for i, ch in enumerate(s): if counts[ch] == 1: return i"],
        "solution": code('''
            from collections import Counter

            def first_unique(s):
                counts = Counter(s)
                for i, ch in enumerate(s):
                    if counts[ch] == 1:
                        return i
                return -1
        '''),
        "lesson": "'Count, then scan in original order' is O(n) and keeps the ordering question "
                  "separate from the counting question.",
        "alternative": "s.index(ch) / s.count(ch) per character is shorter but O(n²).",
        "ts": "const counts = new Map<string, number>(); for (const c of s) counts.set(c, (counts.get(c) ?? 0) + 1);",
    },
    {
        **W, "id": "cb-w3-top-k", "type": "code", "difficulty": 2,
        "tags": ["hashing", "Counter", "heap"], "pattern": "frequency count",
        "title": "Top k frequent words",
        "prompt": "Write `top_k(words, k)` returning the `k` most frequent words, most frequent first; "
                  "ties broken alphabetically.",
        "starter": code('''
            def top_k(words, k):
                pass
        '''),
        "tests": code('''
            def test_basic():
                got = top_k(["a", "b", "a", "c", "b", "a"], 2)
                assert got == ["a", "b"], f"got {got}"
            def test_ties_alpha():
                got = top_k(["pear", "fig", "apple", "fig", "pear", "apple"], 2)
                assert got == ["apple", "fig"], f"all tied at 2 -> alphabetical, got {got}"
            def test_k_bigger():
                assert top_k(["x"], 3) == ["x"]
        '''),
        "hints": ["Count first, then sort the distinct words.",
                  "Sort key: higher count first, then the word itself.",
                  "sorted(counts, key=lambda w: (-counts[w], w))[:k]"],
        "solution": code('''
            from collections import Counter

            def top_k(words, k):
                counts = Counter(words)
                return sorted(counts, key=lambda w: (-counts[w], w))[:k]
        '''),
        "lesson": "Sort by a tuple key to express multi-level ordering; negate a number to flip it "
                  "to descending while the string stays ascending.",
        "alternative": "heapq.nsmallest(k, counts, key=lambda w: (-counts[w], w)) is O(n log k) — "
                       "better when k ≪ n. Counter.most_common(k) doesn't break ties alphabetically.",
        "ts": "[...counts.keys()].sort((a, b) => counts.get(b)! - counts.get(a)! || a.localeCompare(b)).slice(0, k)",
    },
    # ------------------------------------------------------------ two pointers
    {
        **W, "id": "cb-w3-pair-sorted", "type": "code", "difficulty": 2,
        "tags": ["two-pointers"], "pattern": "two pointers (converging)",
        "title": "Pair sum in a sorted list",
        "prompt": "`nums` is sorted ascending. Write `pair_sum(nums, target)` returning a tuple of "
                  "indices `(i, j)`, `i < j`, whose values add to `target`, else `None`. O(1) extra space.",
        "starter": code('''
            def pair_sum(nums, target):
                pass
        '''),
        "tests": code('''
            def test_basic():
                assert pair_sum([1, 2, 4, 7, 11], 15) == (2, 4), "4 + 11"
            def test_ends():
                assert pair_sum([1, 3, 5, 9], 10) == (0, 3), "1 + 9"
            def test_none():
                assert pair_sum([1, 2, 3], 100) is None
            def test_empty():
                assert pair_sum([], 0) is None
        '''),
        "hints": ["Start one pointer at each end.",
                  "If the sum is too small, which pointer should move? Too big?",
                  "while i < j: s = nums[i] + nums[j]; if s == target: return (i, j); elif s < target: i += 1; else: j -= 1"],
        "solution": code('''
            def pair_sum(nums, target):
                i, j = 0, len(nums) - 1
                while i < j:
                    s = nums[i] + nums[j]
                    if s == target:
                        return (i, j)
                    if s < target:
                        i += 1
                    else:
                        j -= 1
                return None
        '''),
        "lesson": "Sorted input + pair question → converging pointers. Each step discards one "
                  "candidate, so it's O(n) time and O(1) space.",
        "alternative": "The dict approach from two-sum also works (O(n) space) and doesn't need sorting.",
    },
    {
        **W, "id": "cb-w3-dedupe-inplace", "type": "code", "difficulty": 2,
        "tags": ["two-pointers", "in-place"], "pattern": "two pointers (read/write)",
        "title": "Dedupe a sorted list in place",
        "prompt": "Write `dedupe(nums)` that removes duplicates from sorted `nums` **in place** "
                  "(keep the first `k` slots unique, in order) and returns `k`. Don't build a new list.",
        "starter": code('''
            def dedupe(nums):
                pass
        '''),
        "tests": code('''
            def test_basic():
                a = [1, 1, 2, 3, 3, 3, 4]
                k = dedupe(a)
                assert k == 4, f"expected 4 unique, got {k}"
                assert a[:k] == [1, 2, 3, 4], f"first k slots wrong: {a[:k]}"
            def test_same_object():
                a = [5, 5]
                ref = a
                dedupe(a)
                assert a is ref and a[0] == 5, "modify the list you were given"
            def test_empty():
                assert dedupe([]) == 0
            def test_all_unique():
                a = [1, 2, 3]
                assert dedupe(a) == 3 and a == [1, 2, 3]
        '''),
        "hints": ["One pointer reads every element, another marks where the next unique value goes.",
                  "A value is new if it differs from the last value you wrote.",
                  "w = 1; for r in range(1, len(nums)): if nums[r] != nums[w-1]: nums[w] = nums[r]; w += 1"],
        "solution": code('''
            def dedupe(nums):
                if not nums:
                    return 0
                w = 1
                for r in range(1, len(nums)):
                    if nums[r] != nums[w - 1]:
                        nums[w] = nums[r]
                        w += 1
                return w
        '''),
        "lesson": "Read/write pointers compact an array in place in O(n): the reader scans "
                  "everything, the writer only advances when it keeps something.",
        "alternative": "nums[:] = dict.fromkeys(nums) is one line and also in-place from the caller's "
                       "view, but uses O(n) extra memory.",
    },
    {
        **W, "id": "cb-w3-palindrome", "type": "code", "difficulty": 1,
        "tags": ["two-pointers", "strings"], "pattern": "two pointers (converging)",
        "title": "Valid palindrome",
        "prompt": "Write `is_palindrome(s)`: True if `s` reads the same both ways considering only "
                  "letters/digits and ignoring case. Use two indices, not a reversed copy.",
        "starter": code('''
            def is_palindrome(s):
                pass
        '''),
        "tests": code('''
            def test_phrase():
                assert is_palindrome("A man, a plan, a canal: Panama") is True
            def test_no():
                assert is_palindrome("race a car") is False
            def test_empty():
                assert is_palindrome("") is True, "empty string is a palindrome"
            def test_punct_only():
                assert is_palindrome(".,") is True
        '''),
        "hints": ["Skip characters that aren't alphanumeric from either side.",
                  "str.isalnum() and str.lower() are what you need.",
                  "while i < j: skip non-alnum with inner whiles, compare s[i].lower() != s[j].lower()"],
        "solution": code('''
            def is_palindrome(s):
                i, j = 0, len(s) - 1
                while i < j:
                    if not s[i].isalnum():
                        i += 1
                    elif not s[j].isalnum():
                        j -= 1
                    elif s[i].lower() != s[j].lower():
                        return False
                    else:
                        i, j = i + 1, j - 1
                return True
        '''),
        "lesson": "An if/elif chain inside one while loop avoids nested skip-loops and their "
                  "off-by-one bugs: each iteration makes exactly one move.",
        "alternative": "t = [c.lower() for c in s if c.isalnum()]; return t == t[::-1] — clearer, O(n) extra space.",
    },
    # ---------------------------------------------------------- sliding window
    {
        **W, "id": "cb-w3-max-sum-k", "type": "code", "difficulty": 2,
        "tags": ["sliding-window"], "pattern": "fixed sliding window",
        "title": "Max sum of k consecutive",
        "prompt": "Write `max_sum_k(nums, k)` returning the largest sum of any `k` consecutive "
                  "numbers in O(n). Return `None` if `len(nums) < k`.",
        "starter": code('''
            def max_sum_k(nums, k):
                pass
        '''),
        "tests": code('''
            def test_basic():
                assert max_sum_k([2, 1, 5, 1, 3, 2], 3) == 9, "5 + 1 + 3"
            def test_negatives():
                assert max_sum_k([-3, -1, -2], 2) == -3, "-1 + -2"
            def test_whole():
                assert max_sum_k([4, 4], 2) == 8
            def test_short():
                assert max_sum_k([1], 2) is None
        '''),
        "hints": ["Sum the first window once; don't re-sum every window.",
                  "Sliding by one: add the new element, subtract the one that fell out.",
                  "window += nums[i] - nums[i - k]; best = max(best, window)"],
        "solution": code('''
            def max_sum_k(nums, k):
                if len(nums) < k:
                    return None
                window = best = sum(nums[:k])
                for i in range(k, len(nums)):
                    window += nums[i] - nums[i - k]
                    best = max(best, window)
                return best
        '''),
        "lesson": "Fixed window: maintain a running aggregate and update it in O(1) per step "
                  "(add the entering element, remove the leaving one).",
        "alternative": "max(sum(nums[i:i+k]) for i in range(len(nums)-k+1)) is one line but O(n·k).",
        "ts": "window += nums[i] - nums[i - k]; best = Math.max(best, window);",
    },
    {
        **W, "id": "cb-w3-longest-unique", "type": "code", "difficulty": 3,
        "tags": ["sliding-window", "hashing"], "pattern": "variable sliding window",
        "title": "Longest substring without repeats",
        "prompt": "Write `longest_unique(s)` returning the length of the longest substring with no "
                  "repeated characters.",
        "starter": code('''
            def longest_unique(s):
                pass
        '''),
        "tests": code('''
            def test_basic():
                assert longest_unique("abcabcbb") == 3, "'abc'"
            def test_same():
                assert longest_unique("bbbb") == 1
            def test_middle():
                assert longest_unique("pwwkew") == 3, "'wke'"
            def test_jump_back():
                assert longest_unique("abba") == 2, "don't move the left edge backwards"
            def test_empty():
                assert longest_unique("") == 0
        '''),
        "hints": ["Grow a window to the right; shrink from the left when a repeat enters.",
                  "Remember the last index of each char; on a repeat, jump left past it — but never backwards.",
                  "if last.get(ch, -1) >= left: left = last[ch] + 1; last[ch] = i; best = max(best, i - left + 1)"],
        "solution": code('''
            def longest_unique(s):
                last = {}
                left = best = 0
                for i, ch in enumerate(s):
                    if last.get(ch, -1) >= left:
                        left = last[ch] + 1
                    last[ch] = i
                    best = max(best, i - left + 1)
                return best
        '''),
        "lesson": "Variable window: expand right every step, move left only as far as needed to "
                  "restore the invariant ('no repeats'). Window length is i - left + 1.",
        "alternative": "Keep a set and `while ch in window: window.remove(s[left]); left += 1` — "
                       "same O(n) amortised, easier to reason about, slightly slower.",
    },
    {
        **W, "id": "cb-w3-min-subarray", "type": "code", "difficulty": 3,
        "tags": ["sliding-window"], "pattern": "variable sliding window",
        "title": "Shortest subarray with sum ≥ target",
        "prompt": "All `nums` are positive. Write `min_len(nums, target)` returning the length of the "
                  "shortest contiguous run whose sum is ≥ `target`, or `0` if none.",
        "starter": code('''
            def min_len(nums, target):
                pass
        '''),
        "tests": code('''
            def test_basic():
                assert min_len([2, 3, 1, 2, 4, 3], 7) == 2, "[4, 3]"
            def test_single():
                assert min_len([1, 4, 4], 4) == 1
            def test_none():
                assert min_len([1, 1, 1], 11) == 0
            def test_whole():
                assert min_len([1, 2, 3], 6) == 3
        '''),
        "hints": ["Add elements on the right until the sum reaches the target.",
                  "While it's still ≥ target, record the length and drop elements from the left.",
                  "for r, x in enumerate(nums): total += x; while total >= target: best = min(best, r-l+1); total -= nums[l]; l += 1"],
        "solution": code('''
            def min_len(nums, target):
                best = float("inf")
                total = left = 0
                for right, x in enumerate(nums):
                    total += x
                    while total >= target:
                        best = min(best, right - left + 1)
                        total -= nums[left]
                        left += 1
                return 0 if best == float("inf") else best
        '''),
        "lesson": "A 'while' shrink inside a 'for' grow is the variable-window template. It's O(n) "
                  "because each index enters and leaves the window once. Works because values are positive.",
        "alternative": "Prefix sums + bisect for each right end: O(n log n), also only valid for positive numbers.",
    },
    # --------------------------------------------------------- stacks & queues
    {
        **W, "id": "cb-w3-valid-parens", "type": "code", "difficulty": 2,
        "tags": ["stack"], "pattern": "stack matching",
        "title": "Valid brackets",
        "prompt": "Write `valid(s)` → True if every `()[]{}` bracket in `s` is closed in the right order. "
                  "Ignore other characters.",
        "starter": code('''
            def valid(s):
                pass
        '''),
        "tests": code('''
            def test_simple():
                assert valid("()[]{}") is True
            def test_nested():
                assert valid("{[(a+b)*c]}") is True
            def test_wrong_order():
                assert valid("(]") is False and valid("([)]") is False
            def test_unclosed():
                assert valid("((") is False, "leftover openers -> False"
            def test_extra_close():
                assert valid("())") is False, "close with empty stack -> False"
        '''),
        "hints": ["The most recently opened bracket must close first — that's LIFO.",
                  "Map each closer to its opener: {')': '(', ...}.",
                  "on a closer: if not stack or stack.pop() != pairs[ch]: return False; at the end: return not stack"],
        "solution": code('''
            def valid(s):
                pairs = {")": "(", "]": "[", "}": "{"}
                stack = []
                for ch in s:
                    if ch in "([{":
                        stack.append(ch)
                    elif ch in pairs:
                        if not stack or stack.pop() != pairs[ch]:
                            return False
                return not stack
        '''),
        "lesson": "A Python list is your stack: append/pop are O(1) at the end. Two classic misses: "
                  "popping an empty stack, and forgetting to check the stack is empty at the end.",
        "ts": "const stack: string[] = []; stack.push(ch); stack.pop();",
    },
    {
        **W, "id": "cb-w3-min-stack", "type": "code", "difficulty": 2,
        "tags": ["stack", "class"], "pattern": "augmented stack",
        "title": "Min stack",
        "prompt": "Write class `MinStack` with `push(x)`, `pop()` (returns the value), and `min()` — "
                  "all O(1).",
        "starter": code('''
            class MinStack:
                def __init__(self):
                    pass
        '''),
        "tests": code('''
            def test_min_tracks():
                s = MinStack()
                s.push(5); s.push(3); s.push(7)
                assert s.min() == 3, "min of 5,3,7"
                assert s.pop() == 7
                assert s.min() == 3
                assert s.pop() == 3
                assert s.min() == 5, "after popping 3 the min goes back to 5"
            def test_duplicates():
                s = MinStack()
                s.push(2); s.push(2); s.pop()
                assert s.min() == 2, "duplicate minimums must survive one pop"
        '''),
        "hints": ["Recomputing min() on every call is O(n). Store more on each push.",
                  "Push a pair (value, min_so_far) instead of just the value.",
                  "m = x if not self.items else min(x, self.items[-1][1]); self.items.append((x, m))"],
        "solution": code('''
            class MinStack:
                def __init__(self):
                    self.items = []

                def push(self, x):
                    m = x if not self.items else min(x, self.items[-1][1])
                    self.items.append((x, m))

                def pop(self):
                    return self.items.pop()[0]

                def min(self):
                    return self.items[-1][1]
        '''),
        "lesson": "When a query must be O(1), cache its answer alongside each element at the moment "
                  "you push it. The stack's LIFO order means the cache is always valid.",
        "alternative": "A second stack that only pushes when x <= current min — less memory when "
                       "values are mostly increasing, but more edge cases (duplicates!).",
    },
    {
        **W, "id": "cb-w3-next-greater", "type": "code", "difficulty": 3,
        "tags": ["stack", "monotonic-stack"], "pattern": "monotonic stack",
        "title": "Next greater element",
        "prompt": "Write `next_greater(nums)` returning a list where `out[i]` is the first value to the "
                  "right of `nums[i]` that is larger, or `-1`. O(n).",
        "starter": code('''
            def next_greater(nums):
                pass
        '''),
        "tests": code('''
            def test_basic():
                assert next_greater([2, 1, 2, 4, 3]) == [4, 2, 4, -1, -1]
            def test_decreasing():
                assert next_greater([3, 2, 1]) == [-1, -1, -1]
            def test_equal_not_greater():
                assert next_greater([1, 1]) == [-1, -1], "equal is not greater"
            def test_empty():
                assert next_greater([]) == []
        '''),
        "hints": ["Keep a stack of indices still waiting for their answer.",
                  "When a bigger value arrives, it answers everyone smaller on top of the stack.",
                  "while stack and nums[stack[-1]] < x: out[stack.pop()] = x; then stack.append(i)"],
        "solution": code('''
            def next_greater(nums):
                out = [-1] * len(nums)
                stack = []
                for i, x in enumerate(nums):
                    while stack and nums[stack[-1]] < x:
                        out[stack.pop()] = x
                    stack.append(i)
                return out
        '''),
        "lesson": "A monotonic stack holds 'unresolved' items in decreasing order; each new item "
                  "resolves the smaller ones. Every index is pushed and popped once → O(n).",
        "alternative": "Nested loops scanning right for each i: trivial, O(n²). Say it first, then improve.",
    },
    {
        **W, "id": "cb-w3-recent-counter", "type": "code", "difficulty": 2,
        "tags": ["queue", "deque"], "pattern": "queue window",
        "title": "Requests in the last 3 seconds",
        "prompt": "Write class `RecentCounter` with `ping(t)` (t in ms, strictly increasing) that "
                  "returns how many pings happened in `[t - 3000, t]`.",
        "starter": code('''
            class RecentCounter:
                def ping(self, t):
                    pass
        '''),
        "tests": code('''
            def test_sequence():
                c = RecentCounter()
                assert c.ping(1) == 1
                assert c.ping(100) == 2
                assert c.ping(3001) == 3, "1 is still inside [1, 3001]"
                assert c.ping(3002) == 3, "1 drops out"
            def test_uses_deque():
                import collections
                c = RecentCounter()
                c.ping(5)
                assert any(isinstance(v, collections.deque) for v in vars(c).values()), \\
                    "store pings in a collections.deque"
        '''),
        "hints": ["Old pings fall out of the front, new ones join the back: a queue.",
                  "collections.deque has O(1) popleft(); list.pop(0) is O(n).",
                  "self.q.append(t); while self.q[0] < t - 3000: self.q.popleft(); return len(self.q)"],
        "solution": code('''
            from collections import deque

            class RecentCounter:
                def __init__(self):
                    self.q = deque()

                def ping(self, t):
                    self.q.append(t)
                    while self.q[0] < t - 3000:
                        self.q.popleft()
                    return len(self.q)
        '''),
        "lesson": "Use deque for queues: append + popleft are O(1). Expire from the front while the "
                  "oldest item is out of range — a time-based sliding window.",
        "ts": "JS has no deque; an array with shift() is O(n) — keep a head index instead.",
    },
    # ------------------------------------------------------------ BFS / DFS
    {
        **W, "id": "cb-w3-islands", "type": "code", "difficulty": 3,
        "tags": ["dfs", "grid"], "pattern": "grid flood fill",
        "title": "Count islands",
        "prompt": "`grid` is a list of strings of `'1'` (land) and `'0'` (water). Write "
                  "`islands(grid)` counting groups of land connected up/down/left/right.",
        "starter": code('''
            def islands(grid):
                pass
        '''),
        "tests": code('''
            def test_three():
                g = ["11000",
                     "11000",
                     "00100",
                     "00011"]
                assert islands(g) == 3
            def test_one_snake():
                assert islands(["111", "001", "111"]) == 1, "connected around the corner"
            def test_diagonal_not_connected():
                assert islands(["10", "01"]) == 2, "diagonals don't connect"
            def test_empty():
                assert islands([]) == 0
            def test_not_mutated():
                g = ["11", "11"]
                islands(g)
                assert g == ["11", "11"], "don't modify the input"
        '''),
        "hints": ["Scan every cell; each unvisited land cell starts a new island.",
                  "From that cell, visit all connected land (stack or recursion) and mark it in a `seen` set.",
                  "for each (r, c) popped: for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)): check bounds, '1', not seen"],
        "solution": code('''
            def islands(grid):
                seen, count = set(), 0
                for r in range(len(grid)):
                    for c in range(len(grid[0])):
                        if grid[r][c] != "1" or (r, c) in seen:
                            continue
                        count += 1
                        stack = [(r, c)]
                        seen.add((r, c))
                        while stack:
                            y, x = stack.pop()
                            for ny, nx in ((y+1, x), (y-1, x), (y, x+1), (y, x-1)):
                                if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]) \\
                                        and grid[ny][nx] == "1" and (ny, nx) not in seen:
                                    seen.add((ny, nx))
                                    stack.append((ny, nx))
                return count
        '''),
        "lesson": "Counting connected components = outer scan + inner flood fill. Mark cells seen "
                  "when you push them (not when you pop) so nothing is pushed twice.",
        "alternative": "Recursive DFS is shorter but can hit Python's recursion limit (~1000) on big grids; "
                       "union-find also works and shines when cells arrive incrementally.",
    },
    {
        **W, "id": "cb-w3-grid-shortest", "type": "code", "difficulty": 3,
        "tags": ["bfs", "grid", "deque"], "pattern": "BFS shortest path",
        "title": "Shortest path in a grid",
        "prompt": "`grid` is a list of strings; `'#'` is a wall, `'.'` is open. Write "
                  "`shortest(grid)` returning the fewest steps (4 directions) from top-left to "
                  "bottom-right, or `-1`.",
        "starter": code('''
            def shortest(grid):
                pass
        '''),
        "tests": code('''
            def test_open():
                assert shortest(["...", "...", "..."]) == 4, "2 down + 2 right"
            def test_detour():
                assert shortest(["..#", "#.#", "#.."]) == 4
            def test_blocked():
                assert shortest([".#", "#."]) == -1
            def test_single():
                assert shortest(["."]) == 0, "start is the goal"
            def test_wall_start():
                assert shortest(["#."]) == -1
        '''),
        "hints": ["In an unweighted graph, BFS reaches each cell first by a shortest path.",
                  "Queue (row, col, dist) in a deque; mark cells seen when you enqueue them.",
                  "q = deque([(0, 0, 0)]); while q: r, c, d = q.popleft(); if goal: return d; enqueue open unseen neighbours with d + 1"],
        "solution": code('''
            from collections import deque

            def shortest(grid):
                rows, cols = len(grid), len(grid[0])
                if grid[0][0] == "#":
                    return -1
                q, seen = deque([(0, 0, 0)]), {(0, 0)}
                while q:
                    r, c, d = q.popleft()
                    if (r, c) == (rows - 1, cols - 1):
                        return d
                    for nr, nc in ((r+1, c), (r-1, c), (r, c+1), (r, c-1)):
                        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == "." \\
                                and (nr, nc) not in seen:
                            seen.add((nr, nc))
                            q.append((nr, nc, d + 1))
                return -1
        '''),
        "lesson": "Shortest path with equal-cost steps → BFS with a deque. DFS finds *a* path, not "
                  "the shortest. O(rows·cols).",
        "alternative": "With weighted edges you'd switch to Dijkstra (heapq); with 0/1 weights a deque "
                       "with appendleft works (0-1 BFS).",
    },
    {
        **W, "id": "cb-w3-reachable", "type": "code", "difficulty": 2,
        "tags": ["bfs", "graph"], "pattern": "graph traversal",
        "title": "Can A reach B?",
        "prompt": "`graph` is a dict `node -> list of neighbours` (directed). Write "
                  "`reachable(graph, start, goal)` → bool. Graphs may contain cycles.",
        "starter": code('''
            def reachable(graph, start, goal):
                pass
        '''),
        "tests": code('''
            G = {"a": ["b"], "b": ["c", "a"], "c": [], "d": ["a"]}
            def test_yes():
                assert reachable(G, "a", "c") is True
            def test_direction():
                assert reachable(G, "a", "d") is False, "edges are one-way"
            def test_self():
                assert reachable(G, "c", "c") is True
            def test_missing_node():
                assert reachable({"x": ["y"]}, "x", "y") is True, "y has no entry in the dict"
        '''),
        "hints": ["Without a visited set, the cycle a → b → a loops forever.",
                  "Use a stack (or deque) of nodes to visit; graph.get(node, []) handles leaf nodes.",
                  "while todo: n = todo.pop(); if n == goal: return True; for m in graph.get(n, []): if m not in seen: seen.add(m); todo.append(m)"],
        "solution": code('''
            def reachable(graph, start, goal):
                todo, seen = [start], {start}
                while todo:
                    n = todo.pop()
                    if n == goal:
                        return True
                    for m in graph.get(n, []):
                        if m not in seen:
                            seen.add(m)
                            todo.append(m)
                return False
        '''),
        "lesson": "Every graph traversal is: frontier + visited set + 'expand neighbours'. A list "
                  "frontier gives DFS, a deque with popleft gives BFS.",
        "alternative": "Recursive DFS with a seen set — shorter, but watch the recursion limit.",
    },
    {
        **W, "id": "cb-w3-topo-sort", "type": "code", "difficulty": 3,
        "tags": ["graph", "topological-sort", "bfs"], "pattern": "topological sort (Kahn)",
        "title": "Build order (topological sort)",
        "prompt": "`deps` maps each task to the list of tasks it depends on. Write `order(deps)` "
                  "returning a list where every task comes after its dependencies (ties: "
                  "alphabetical). Raise `ValueError` on a cycle.",
        "starter": code('''
            def order(deps):
                pass
        '''),
        "tests": code('''
            def test_chain():
                assert order({"c": ["b"], "b": ["a"], "a": []}) == ["a", "b", "c"]
            def test_ties():
                got = order({"app": ["db", "cache"], "db": [], "cache": []})
                assert got == ["cache", "db", "app"], f"got {got}"
            def test_dep_not_a_key():
                assert order({"b": ["a"]}) == ["a", "b"], "'a' only appears as a dependency"
            def test_cycle():
                try:
                    order({"a": ["b"], "b": ["a"]})
                except ValueError:
                    return
                assert False, "a cycle must raise ValueError"
        '''),
        "hints": ["Count unmet dependencies per task; tasks with 0 are ready.",
                  "When you finish a task, decrement its dependents; newly-0 tasks become ready. Use a heap for alphabetical ties.",
                  "If len(result) < number of tasks at the end, there's a cycle."],
        "solution": code('''
            import heapq

            def order(deps):
                tasks = set(deps) | {d for ds in deps.values() for d in ds}
                need = {t: len(set(deps.get(t, []))) for t in tasks}
                users = {t: [] for t in tasks}
                for t, ds in deps.items():
                    for d in set(ds):
                        users[d].append(t)
                ready = [t for t in tasks if need[t] == 0]
                heapq.heapify(ready)
                out = []
                while ready:
                    t = heapq.heappop(ready)
                    out.append(t)
                    for u in users[t]:
                        need[u] -= 1
                        if need[u] == 0:
                            heapq.heappush(ready, u)
                if len(out) < len(tasks):
                    raise ValueError("cycle")
                return out
        '''),
        "lesson": "Kahn's algorithm: in-degree counts + a queue of ready nodes. Fewer outputs than "
                  "nodes means a cycle. O(V + E) (plus log for the heap).",
        "alternative": "graphlib.TopologicalSorter(deps).static_order() is in the stdlib (3.9+) and "
                       "raises CycleError — mention it, but expect to hand-write it in an interview.",
    },
    # -------------------------------------------------- sorting + binary search
    {
        **W, "id": "cb-w3-bisect-count", "type": "code", "difficulty": 1,
        "tags": ["bisect", "binary-search"], "pattern": "bisect",
        "title": "Count values in a range with bisect",
        "prompt": "`xs` is sorted. Write `count_between(xs, lo, hi)` returning how many values `v` "
                  "satisfy `lo <= v <= hi`, in O(log n).",
        "starter": code('''
            def count_between(xs, lo, hi):
                pass
        '''),
        "tests": code('''
            def test_basic():
                assert count_between([1, 3, 3, 5, 8, 9], 3, 8) == 4, "3, 3, 5, 8"
            def test_none():
                assert count_between([1, 2], 5, 6) == 0
            def test_all():
                assert count_between([2, 2, 2], 2, 2) == 3
        '''),
        "hints": ["The bisect module finds insertion points in sorted lists.",
                  "bisect_left gives the first index ≥ lo; bisect_right gives the first index > hi.",
                  "return bisect_right(xs, hi) - bisect_left(xs, lo)"],
        "solution": code('''
            from bisect import bisect_left, bisect_right

            def count_between(xs, lo, hi):
                return bisect_right(xs, hi) - bisect_left(xs, lo)
        '''),
        "lesson": "bisect_left(xs, v) = first index with xs[i] >= v; bisect_right = first index with "
                  "xs[i] > v. Their difference counts a closed range.",
        "alternative": "sum(lo <= v <= hi for v in xs) is O(n) — fine if you only query once.",
    },
    {
        **W, "id": "cb-w3-search-insert", "type": "code", "difficulty": 2,
        "tags": ["binary-search"], "pattern": "binary search (lower bound)",
        "title": "Search insert position (by hand)",
        "prompt": "Without `bisect`, write `search_insert(nums, target)` returning the index of "
                  "`target` in sorted `nums`, or where it would be inserted to keep order.",
        "starter": code('''
            def search_insert(nums, target):
                pass
        '''),
        "tests": code('''
            def test_found():
                assert search_insert([1, 3, 5, 6], 5) == 2
            def test_middle():
                assert search_insert([1, 3, 5, 6], 2) == 1
            def test_end():
                assert search_insert([1, 3, 5, 6], 7) == 4
            def test_start():
                assert search_insert([1, 3], 0) == 0
            def test_empty():
                assert search_insert([], 4) == 0
            def test_dups_leftmost():
                assert search_insert([2, 2, 2], 2) == 0, "leftmost position"
        '''),
        "hints": ["Search the half-open range [lo, hi) with hi = len(nums).",
                  "If nums[mid] < target the answer is right of mid; otherwise mid could be the answer.",
                  "while lo < hi: mid = (lo + hi) // 2; if nums[mid] < target: lo = mid + 1; else: hi = mid"],
        "solution": code('''
            def search_insert(nums, target):
                lo, hi = 0, len(nums)
                while lo < hi:
                    mid = (lo + hi) // 2
                    if nums[mid] < target:
                        lo = mid + 1
                    else:
                        hi = mid
                return lo
        '''),
        "lesson": "Memorise one template: half-open [lo, hi), `while lo < hi`, `lo = mid + 1` or "
                  "`hi = mid`. It always terminates and returns the lower bound.",
        "alternative": "bisect.bisect_left(nums, target) does exactly this — use it in real code.",
        "ts": "const mid = (lo + hi) >> 1;",
    },
    {
        **W, "id": "cb-w3-merge-intervals", "type": "code", "difficulty": 2,
        "tags": ["sorting", "intervals"], "pattern": "sort then sweep",
        "title": "Merge overlapping intervals",
        "prompt": "Write `merge(intervals)` taking `[start, end]` pairs (any order) and returning "
                  "merged, sorted intervals. Touching intervals (`[1,2]`, `[2,3]`) merge.",
        "starter": code('''
            def merge(intervals):
                pass
        '''),
        "tests": code('''
            def test_basic():
                assert merge([[1, 3], [8, 10], [2, 6]]) == [[1, 6], [8, 10]]
            def test_touching():
                assert merge([[1, 2], [2, 3]]) == [[1, 3]]
            def test_contained():
                assert merge([[1, 10], [2, 3]]) == [[1, 10]], "inner interval must not shrink the end"
            def test_empty():
                assert merge([]) == []
        '''),
        "hints": ["Sort by start first; then overlaps are always with the last merged interval.",
                  "Overlap if the next start ≤ the last end.",
                  "if out and s <= out[-1][1]: out[-1][1] = max(out[-1][1], e) else: out.append([s, e])"],
        "solution": code('''
            def merge(intervals):
                out = []
                for s, e in sorted(intervals):
                    if out and s <= out[-1][1]:
                        out[-1][1] = max(out[-1][1], e)
                    else:
                        out.append([s, e])
                return out
        '''),
        "lesson": "Sorting first turns many interval problems into a single left-to-right sweep "
                  "comparing with the last kept item. O(n log n).",
        "alternative": "Event sweep: +1 at each start, -1 at each end, sorted — generalises to "
                       "'max overlapping meetings'.",
    },
    {
        **W, "id": "cb-w3-sort-key", "type": "code", "difficulty": 1,
        "tags": ["sorting"], "pattern": "sort with key",
        "title": "Leaderboard sort",
        "prompt": "`rows` is a list of `(name, score)`. Write `leaderboard(rows)` returning names "
                  "by score descending, ties by name ascending.",
        "starter": code('''
            def leaderboard(rows):
                pass
        '''),
        "tests": code('''
            def test_basic():
                rows = [("bo", 5), ("al", 9), ("cy", 5)]
                assert leaderboard(rows) == ["al", "bo", "cy"]
            def test_input_unchanged():
                rows = [("b", 1), ("a", 2)]
                leaderboard(rows)
                assert rows == [("b", 1), ("a", 2)], "use sorted(), don't mutate input"
        '''),
        "hints": ["sorted() takes a key function.",
                  "A tuple key sorts by its first element, then the second…",
                  "[name for name, _ in sorted(rows, key=lambda r: (-r[1], r[0]))]"],
        "solution": code('''
            def leaderboard(rows):
                return [name for name, _ in sorted(rows, key=lambda r: (-r[1], r[0]))]
        '''),
        "lesson": "sorted(xs, key=...) returns a new list; list.sort() mutates. Tuple keys give "
                  "multi-level ordering; negate numbers to reverse one level.",
        "ts": "[...rows].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))",
    },
    # --------------------------------------------------------------- predict
    {
        **W, "id": "cb-w3-bigo-nested", "type": "predict", "kind": "complexity", "difficulty": 1,
        "tags": ["big-o"], "pattern": "Big-O reasoning",
        "code": code('''
            def has_pair(nums, t):
                for i in range(len(nums)):
                    for j in range(i + 1, len(nums)):
                        if nums[i] + nums[j] == t:
                            return True
                return False
        '''),
        "question": "Worst-case time complexity?",
        "choices": ["O(n)", "O(n log n)", "O(n²)", "O(2ⁿ)"],
        "answer": 2,
        "explanation": "The inner loop runs n-1, n-2, … 1 times: n(n-1)/2 comparisons → O(n²). "
                       "Starting j at i+1 halves the work but doesn't change the class.",
    },
    {
        **W, "id": "cb-w3-bigo-in-list", "type": "predict", "kind": "complexity", "difficulty": 2,
        "tags": ["big-o", "hashing"], "pattern": "Big-O reasoning",
        "code": code('''
            def common(a, b):          # len(a) = n, len(b) = m
                return [x for x in a if x in b]
        '''),
        "question": "`a` and `b` are lists. Time complexity — and the one-word fix?",
        "choices": ["O(n + m); already optimal",
                    "O(n·m); make b a set first",
                    "O(n log m); sort b",
                    "O(n); `in` is constant time"],
        "answer": 1,
        "explanation": "`x in list` scans the list: O(m) per check → O(n·m). `bs = set(b)` once makes "
                       "each check O(1) on average → O(n + m).",
        "ts": "Same trap as arr.includes() inside a loop; use a Set.",
    },
    {
        **W, "id": "cb-w3-bigo-halving", "type": "predict", "kind": "complexity", "difficulty": 2,
        "tags": ["big-o"], "pattern": "Big-O reasoning",
        "code": code('''
            def steps(n):
                count = 0
                while n > 1:
                    n //= 2
                    count += 1
                return count
        '''),
        "question": "Time complexity in terms of n?",
        "choices": ["O(1)", "O(log n)", "O(n)", "O(√n)"],
        "answer": 1,
        "explanation": "Halving each iteration reaches 1 after about log₂ n steps — the same shape "
                       "as binary search.",
    },
    {
        **W, "id": "cb-w3-bigo-sort-loop", "type": "predict", "kind": "complexity", "difficulty": 2,
        "tags": ["big-o", "sorting"], "pattern": "Big-O reasoning",
        "code": code('''
            def closest_gap(nums):
                nums = sorted(nums)
                return min(b - a for a, b in zip(nums, nums[1:]))
        '''),
        "question": "Time complexity?",
        "choices": ["O(n)", "O(n log n)", "O(n²)", "O(n² log n)"],
        "answer": 1,
        "explanation": "Sort O(n log n) + one linear pass O(n): the bigger term wins → O(n log n). "
                       "Sequential steps add; nested steps multiply.",
    },
    {
        **W, "id": "cb-w3-deque-order", "type": "predict", "kind": "output", "difficulty": 1,
        "tags": ["deque", "queue"], "pattern": "stack vs queue",
        "code": code('''
            from collections import deque
            q = deque([1, 2])
            q.append(3)
            q.appendleft(0)
            print(q.popleft(), q.pop())
        '''),
        "question": "What does this print?",
        "choices": ["0 3", "1 3", "0 2", "3 0"],
        "answer": 0,
        "explanation": "After the appends the deque is [0, 1, 2, 3]. popleft() takes from the front (0), "
                       "pop() from the back (3).",
    },
    {
        **W, "id": "cb-w3-pick-pattern", "type": "predict", "kind": "concept", "difficulty": 2,
        "tags": ["patterns"], "pattern": "pattern selection",
        "question": "\"Longest substring containing at most k distinct characters.\" Which pattern "
                    "should you reach for first?",
        "choices": ["Binary search on the answer",
                    "Variable sliding window + a Counter of the window",
                    "BFS over substrings",
                    "Sort the string, then two pointers"],
        "answer": 1,
        "explanation": "'Longest/shortest contiguous run satisfying a condition' is the sliding-window "
                       "signal. Grow right, shrink left while the Counter has more than k keys. O(n).",
    },
    # ------------------------------------------------------------------- bugs
    {
        **W, "id": "cb-w3-bug-two-sum", "type": "bug", "difficulty": 1,
        "tags": ["hashing"], "pattern": "hash map lookup",
        "title": "Two-sum pairs an element with itself",
        "code": code('''
            def two_sum(nums, target):
                seen = {}
                for i, x in enumerate(nums):
                    seen[x] = i
                    if target - x in seen:
                        return (seen[target - x], i)
                return None
        '''),
        "bugLine": 4,
        "fixed": code('''
            def two_sum(nums, target):
                seen = {}
                for i, x in enumerate(nums):
                    if target - x in seen:
                        return (seen[target - x], i)
                    seen[x] = i
                return None
        '''),
        "tests": code('''
            def test_not_self():
                assert two_sum([3, 2, 4], 6) == (1, 2), "3 must not pair with itself"
            def test_basic():
                assert two_sum([2, 7], 9) == (0, 1)
        '''),
        "choices": ["Insert x into `seen` only after checking for its partner",
                    "Use `nums.index(target - x)` instead of the dict",
                    "Start enumerate at 1",
                    "Return (i, seen[target - x]) instead"],
        "answer": 0,
        "explanation": "Storing x before the lookup lets 3 find itself when target is 6. Check first, "
                       "then record — the dict must only contain *earlier* elements.",
    },
    {
        **W, "id": "cb-w3-bug-parens", "type": "bug", "difficulty": 1,
        "tags": ["stack"], "pattern": "stack matching",
        "title": "Brackets that never close",
        "code": code('''
            def valid(s):
                pairs = {")": "(", "]": "["}
                stack = []
                for ch in s:
                    if ch in "([":
                        stack.append(ch)
                    elif not stack or stack.pop() != pairs[ch]:
                        return False
                return True
        '''),
        "bugLine": 9,
        "fixed": code('''
            def valid(s):
                pairs = {")": "(", "]": "["}
                stack = []
                for ch in s:
                    if ch in "([":
                        stack.append(ch)
                    elif not stack or stack.pop() != pairs[ch]:
                        return False
                return not stack
        '''),
        "tests": code('''
            def test_ok():
                assert valid("([])") is True
            def test_unclosed():
                assert valid("((") is False, "unclosed openers"
        '''),
        "choices": ["`return not stack` at the end",
                    "Use stack.pop(0) for FIFO order",
                    "Check `ch in pairs.values()` first",
                    "Initialise stack with a sentinel"],
        "answer": 0,
        "explanation": "\"((\" never hits a closer, so the loop finishes with openers left. The final "
                       "answer must be 'stack is empty'.",
    },
    {
        **W, "id": "cb-w3-bug-merge", "type": "bug", "difficulty": 2,
        "tags": ["intervals", "sorting"], "pattern": "sort then sweep",
        "title": "Merged interval shrinks",
        "code": code('''
            def merge(intervals):
                out = []
                for s, e in sorted(intervals):
                    if out and s <= out[-1][1]:
                        out[-1][1] = e
                    else:
                        out.append([s, e])
                return out
        '''),
        "bugLine": 5,
        "fixed": code('''
            def merge(intervals):
                out = []
                for s, e in sorted(intervals):
                    if out and s <= out[-1][1]:
                        out[-1][1] = max(out[-1][1], e)
                    else:
                        out.append([s, e])
                return out
        '''),
        "tests": code('''
            def test_contained():
                assert merge([[1, 10], [2, 3]]) == [[1, 10]], "contained interval"
            def test_basic():
                assert merge([[1, 3], [2, 6]]) == [[1, 6]]
        '''),
        "choices": ["Take max(out[-1][1], e) as the new end",
                    "Use `s < out[-1][1]` (strict)",
                    "Sort by end instead of start",
                    "Append a copy: out.append([s, e][:])"],
        "answer": 0,
        "explanation": "[2, 3] sits inside [1, 10]; overwriting the end with 3 shrinks it. The merged "
                       "end is whichever end reaches further.",
    },
    # ---------------------------------------------------------------- parsons
    {
        **W, "id": "cb-w3-parsons-bfs", "type": "parsons", "difficulty": 2,
        "tags": ["bfs", "graph", "deque"], "pattern": "BFS shortest path",
        "title": "BFS distance in a graph",
        "prompt": "Arrange the lines so `dist(graph, start, goal)` returns the number of edges on the "
                  "shortest path, or -1.",
        "lines": lines('''
            from collections import deque
            def dist(graph, start, goal):
                q, seen = deque([(start, 0)]), {start}
                while q:
                    node, d = q.popleft()
                    if node == goal:
                        return d
                    for nxt in graph.get(node, []):
                        if nxt not in seen:
                            seen.add(nxt)
                            q.append((nxt, d + 1))
                return -1
        '''),
        "tests": code('''
            G = {"a": ["b", "c"], "b": ["d"], "c": ["d"], "d": ["e"], "e": []}
            def test_dist():
                assert dist(G, "a", "e") == 3
            def test_same():
                assert dist(G, "a", "a") == 0
            def test_unreachable():
                assert dist(G, "e", "a") == -1
        '''),
        "lesson": "BFS template: deque of (node, distance), seen set, popleft, check goal, enqueue "
                  "unseen neighbours with d + 1.",
    },
    {
        **W, "id": "cb-w3-parsons-window", "type": "parsons", "difficulty": 2,
        "tags": ["sliding-window", "Counter"], "pattern": "variable sliding window",
        "title": "Longest run with at most k distinct",
        "prompt": "Arrange the lines so `longest_k(s, k)` returns the length of the longest substring "
                  "with at most `k` distinct characters.",
        "lines": lines('''
            from collections import Counter
            def longest_k(s, k):
                window, left, best = Counter(), 0, 0
                for right, ch in enumerate(s):
                    window[ch] += 1
                    while len(window) > k:
                        window[s[left]] -= 1
                        if window[s[left]] == 0:
                            del window[s[left]]
                        left += 1
                    best = max(best, right - left + 1)
                return best
        '''),
        "tests": code('''
            def test_basic():
                assert longest_k("eceba", 2) == 3, "'ece'"
            def test_all():
                assert longest_k("aa", 1) == 2
            def test_zero():
                assert longest_k("abc", 0) == 0
        '''),
        "lesson": "Counter as a window: increment on entry, decrement on exit and delete zero counts "
                  "so len(window) is the number of distinct characters.",
    },
]
