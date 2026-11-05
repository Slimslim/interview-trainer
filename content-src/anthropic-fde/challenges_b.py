from _helpers import code

# ---------------------------------------------------------------------------
# 1. In-memory key-value database (most-reported progressive problem, S17)
# ---------------------------------------------------------------------------

KV_S1 = code(r'''
    class InMemoryDB:
        def __init__(self):
            self._data = {}  # key -> {field: value}

        def set(self, key, field, value):
            self._data.setdefault(key, {})[field] = value

        def get(self, key, field):
            return self._data.get(key, {}).get(field)

        def delete(self, key, field):
            record = self._data.get(key)
            if record is None or field not in record:
                return False
            del record[field]
            if not record:          # drop empty keys so scans stay clean
                del self._data[key]
            return True
''')

KV_S2 = code(r'''
    class InMemoryDB:
        def __init__(self):
            self._data = {}  # key -> {field: value}

        def set(self, key, field, value):
            self._data.setdefault(key, {})[field] = value

        def get(self, key, field):
            return self._data.get(key, {}).get(field)

        def delete(self, key, field):
            record = self._data.get(key)
            if record is None or field not in record:
                return False
            del record[field]
            if not record:
                del self._data[key]
            return True

        def scan(self, key):
            return self.scan_by_prefix(key, "")

        def scan_by_prefix(self, key, prefix):
            record = self._data.get(key, {})
            matches = [(f, v) for f, v in record.items() if f.startswith(prefix)]
            return sorted(matches, key=lambda fv: fv[0])
''')

KV_S3 = code(r'''
    class InMemoryDB:
        """key -> {field: (value, expires_at)}; expires_at None means never."""

        def __init__(self):
            self._data = {}

        @staticmethod
        def _alive(entry, ts):
            _, expires_at = entry
            return expires_at is None or ts < expires_at

        def set(self, key, field, value, ts=0, ttl=None):
            expires_at = None if ttl is None else ts + ttl
            self._data.setdefault(key, {})[field] = (value, expires_at)

        def get(self, key, field, ts=0):
            entry = self._data.get(key, {}).get(field)
            if entry is None or not self._alive(entry, ts):
                return None
            return entry[0]

        def delete(self, key, field, ts=0):
            record = self._data.get(key, {})
            entry = record.get(field)
            if entry is None or not self._alive(entry, ts):
                return False
            del record[field]
            if not record:
                del self._data[key]
            return True

        def scan(self, key, ts=0):
            return self.scan_by_prefix(key, "", ts)

        def scan_by_prefix(self, key, prefix, ts=0):
            record = self._data.get(key, {})
            matches = [(f, e[0]) for f, e in record.items()
                       if f.startswith(prefix) and self._alive(e, ts)]
            return sorted(matches, key=lambda fv: fv[0])
''')

def _fix_kv_s4():
    head = "import json\n\n\n" + KV_S3 + "\n"
    tail = code(r'''
        # --- persistence ------------------------------------------------
        def dump(self, ts=0):
            """JSON snapshot of live records; TTLs stored as time REMAINING."""
            snapshot = {}
            for key, record in self._data.items():
                fields = {}
                for field, (value, expires_at) in record.items():
                    if expires_at is None:
                        fields[field] = [value, None]
                    elif ts < expires_at:
                        fields[field] = [value, expires_at - ts]
                if fields:
                    snapshot[key] = fields
            return json.dumps(snapshot, sort_keys=True)

        def load(self, blob, ts=0):
            """Replace all state; re-anchor remaining TTLs at the load time."""
            data = {}
            for key, fields in json.loads(blob).items():
                data[key] = {
                    field: (value, None if remaining is None else ts + remaining)
                    for field, (value, remaining) in fields.items()
                }
            self._data = data
    ''')
    tail = "".join(("    " + ln if ln.strip() else ln) for ln in tail.splitlines(True))
    return head + tail


KV_S4 = _fix_kv_s4()

KV_T1 = code(r'''
    def test_set_get():
        db = InMemoryDB()
        db.set("user1", "name", "Ada")
        db.set("user1", "age", 36)
        assert db.get("user1", "name") == "Ada", "get should return the stored value"
        assert db.get("user1", "age") == 36, "each field is stored separately"

    def test_overwrite():
        db = InMemoryDB()
        db.set("k", "f", 1)
        db.set("k", "f", 2)
        assert db.get("k", "f") == 2, "set on an existing field overwrites it"

    def test_missing_returns_none():
        db = InMemoryDB()
        assert db.get("nope", "x") is None, "missing key -> None"
        db.set("k", "a", 1)
        assert db.get("k", "b") is None, "missing field -> None"

    def test_keys_are_isolated():
        db = InMemoryDB()
        db.set("a", "f", 1)
        db.set("b", "f", 2)
        assert (db.get("a", "f"), db.get("b", "f")) == (1, 2), "same field name under different keys"

    def test_delete():
        db = InMemoryDB()
        db.set("k", "a", 1)
        db.set("k", "b", 2)
        assert db.delete("k", "a") is True, "delete of an existing field returns True"
        assert db.get("k", "a") is None, "deleted field is gone"
        assert db.get("k", "b") == 2, "other fields survive"
        assert db.delete("k", "a") is False, "second delete returns False"
        assert db.delete("zz", "a") is False, "delete on a missing key returns False"
''')

KV_T2 = KV_T1 + "\n" + code(r'''
    def test_scan_sorted():
        db = InMemoryDB()
        db.set("u", "zeta", 3)
        db.set("u", "alpha", 1)
        db.set("u", "mid", 2)
        assert db.scan("u") == [("alpha", 1), ("mid", 2), ("zeta", 3)], \
            "scan returns (field, value) pairs sorted by field"

    def test_scan_missing_key():
        db = InMemoryDB()
        assert db.scan("ghost") == [], "scan of a missing key is []"
        assert db.scan_by_prefix("ghost", "a") == [], "prefix scan of a missing key is []"

    def test_scan_by_prefix():
        db = InMemoryDB()
        for f, v in [("addr_city", "Paris"), ("addr_zip", "75001"), ("name", "Ada"), ("add", 0)]:
            db.set("u", f, v)
        assert db.scan_by_prefix("u", "addr_") == [("addr_city", "Paris"), ("addr_zip", "75001")]
        assert db.scan_by_prefix("u", "add") == [("add", 0), ("addr_city", "Paris"), ("addr_zip", "75001")]
        assert db.scan_by_prefix("u", "x") == [], "no match -> []"

    def test_scan_after_delete():
        db = InMemoryDB()
        db.set("u", "a", 1)
        db.set("u", "b", 2)
        db.delete("u", "a")
        assert db.scan("u") == [("b", 2)], "deleted fields disappear from scans"
''')

KV_T3 = KV_T2 + "\n" + code(r'''
    def test_ttl_expiry_boundary():
        db = InMemoryDB()
        db.set("k", "a", 1, ts=10, ttl=5)
        assert db.get("k", "a", ts=10) == 1, "alive at the set time"
        assert db.get("k", "a", ts=14) == 1, "alive before ts+ttl"
        assert db.get("k", "a", ts=15) is None, "expired AT ts+ttl (window is [ts, ts+ttl))"

    def test_no_ttl_never_expires():
        db = InMemoryDB()
        db.set("k", "a", 1, ts=0)
        assert db.get("k", "a", ts=10**9) == 1, "no ttl -> lives forever"

    def test_overwrite_resets_ttl():
        db = InMemoryDB()
        db.set("k", "a", 1, ts=0, ttl=5)
        db.set("k", "a", 2, ts=3)
        assert db.get("k", "a", ts=100) == 2, "overwriting without ttl removes the expiry"
        db.set("k", "a", 3, ts=100, ttl=10)
        assert db.get("k", "a", ts=109) == 3 and db.get("k", "a", ts=110) is None

    def test_scans_skip_expired():
        db = InMemoryDB()
        db.set("u", "a", 1, ts=0, ttl=10)
        db.set("u", "ab", 2, ts=0)
        db.set("u", "b", 3, ts=0, ttl=2)
        assert db.scan("u", ts=5) == [("a", 1), ("ab", 2)], "expired 'b' must not appear"
        assert db.scan_by_prefix("u", "a", ts=10) == [("ab", 2)], "'a' expired at 10"

    def test_delete_expired_is_false():
        db = InMemoryDB()
        db.set("k", "a", 1, ts=0, ttl=5)
        assert db.delete("k", "a", ts=6) is False, "an expired field counts as missing"
        db.set("k", "b", 2, ts=0, ttl=5)
        assert db.delete("k", "b", ts=4) is True
''')

KV_T4 = KV_T3 + "\n" + code(r'''
    import json as _json

    def test_dump_is_json_of_live_data():
        db = InMemoryDB()
        db.set("u", "name", "Ada", ts=0)
        db.set("u", "tmp", "x", ts=0, ttl=3)
        blob = db.dump(ts=5)
        assert isinstance(blob, str), "dump returns a JSON string"
        data = _json.loads(blob)
        assert "u" in data, "live key is in the snapshot"
        assert "tmp" not in _json.dumps(data), "expired field must not be backed up"

    def test_round_trip():
        db = InMemoryDB()
        db.set("a", "x", 1, ts=0)
        db.set("a", "y", "two", ts=0)
        db.set("b", "z", [1, 2], ts=0)
        fresh = InMemoryDB()
        fresh.load(db.dump(ts=1), ts=1)
        assert fresh.scan("a", ts=2) == [("x", 1), ("y", "two")]
        assert fresh.get("b", "z", ts=2) == [1, 2]

    def test_restore_honours_remaining_ttl():
        db = InMemoryDB()
        db.set("s", "token", "abc", ts=0, ttl=10)   # expires at 10
        blob = db.dump(ts=4)                         # 6 units left
        later = InMemoryDB()
        later.load(blob, ts=100)                     # should now expire at 106
        assert later.get("s", "token", ts=105) == "abc", "remaining TTL (6) re-anchored at load time"
        assert later.get("s", "token", ts=106) is None, "expires 6 units after the load"

    def test_load_replaces_state():
        db = InMemoryDB()
        db.set("old", "f", 1)
        snapshot = InMemoryDB().dump()
        db.load(snapshot)
        assert db.get("old", "f") is None, "load replaces everything (it's a restore, not a merge)"

    def test_snapshot_is_independent():
        db = InMemoryDB()
        db.set("k", "f", 1)
        blob = db.dump()
        db.set("k", "f", 2)
        other = InMemoryDB()
        other.load(blob)
        assert other.get("k", "f") == 1, "later writes must not leak into an earlier snapshot"
''')

KV = {
    "id": "fde-ch-kv-db", "type": "challenge", "stage": "coding", "difficulty": 3,
    "source": "S17",
    "tags": ["dict", "class design", "ttl", "json", "progressive"],
    "pattern": "dict-of-dicts state with lazy expiry",
    "title": "In-memory key-value database (4 levels)",
    "summary": "The most-reported Anthropic progressive problem: a key -> field -> value store that grows scans, TTL with explicit timestamps, then backup/restore. Each level forces you to change the stored shape, so the first design matters.",
    "talkPrompts": [
        "I'll store key -> {field: value}; nested dicts give O(1) get/set/delete and an easy per-key scan.",
        "Timestamps are passed in, not read from a clock, so I'll treat ts as the only notion of 'now'.",
        "I'll expire lazily: check liveness on read instead of running a sweeper. Memory tradeoff noted.",
        "For the snapshot I store remaining TTL, not the absolute expiry, so a restore at a different time still works.",
        "Before each level I'll rerun the old asserts so I know the refactor didn't break anything.",
    ],
    "steps": [
        {
            "title": "Level 1: set / get / delete",
            "minutes": 8,
            "prompt": code(r'''
                Implement `class InMemoryDB` storing **records**: each `key` holds many `field -> value` pairs.

                - `set(key, field, value) -> None` - insert or overwrite.
                - `get(key, field)` - the value, or `None` if the key or field is missing.
                - `delete(key, field) -> bool` - `True` if it existed and was removed, else `False`.

                ```python
                db = InMemoryDB()
                db.set("u1", "name", "Ada")
                db.get("u1", "name")    # "Ada"
                db.delete("u1", "name") # True
                db.delete("u1", "name") # False
                ```
            '''),
            "starter": code(r'''
                class InMemoryDB:
                    def __init__(self):
                        pass

                    def set(self, key, field, value):
                        pass

                    def get(self, key, field):
                        pass

                    def delete(self, key, field):
                        pass
            '''),
            "tests": KV_T1,
            "hints": [
                "Two levels of lookup: key, then field. What Python structure maps naturally to that?",
                "A dict of dicts: `self._data[key][field] = value`. `setdefault` creates the inner dict on first write.",
                "`get`: `self._data.get(key, {}).get(field)`. `delete`: check membership first, `del`, and drop the key when its inner dict becomes empty.",
            ],
            "solution": KV_S1,
            "lesson": "Pick the state shape that the next level will need: nested dicts make every op O(1) and keep a key's fields together for scans. Chained `.get(key, {}).get(field)` handles both missing levels without try/except.",
            "alternative": "A flat dict keyed by `(key, field)` tuples is just as fast for get/set, but every per-key scan becomes O(total fields) - a bad fit for level 2.",
        },
        {
            "title": "Level 2: scan and scan_by_prefix",
            "minutes": 7,
            "prompt": code(r'''
                Add:

                - `scan(key) -> list[tuple]` - all `(field, value)` pairs of `key`, **sorted by field**.
                - `scan_by_prefix(key, prefix) -> list[tuple]` - only fields starting with `prefix`, sorted.

                A missing key gives `[]`. Level 1 behaviour must still work.

                ```python
                db.set("u", "b", 2); db.set("u", "a", 1); db.set("u", "ab", 3)
                db.scan("u")                 # [("a", 1), ("ab", 3), ("b", 2)]
                db.scan_by_prefix("u", "a")  # [("a", 1), ("ab", 3)]
                ```
            '''),
            "tests": KV_T2,
            "hints": [
                "Both functions are the same thing with a different filter. Can one call the other?",
                "`scan(key)` is `scan_by_prefix(key, \"\")` - every string starts with the empty string.",
                "`sorted(((f, v) for f, v in record.items() if f.startswith(prefix)), key=lambda fv: fv[0])`",
            ],
            "solution": KV_S2,
            "lesson": "Express the general operation once and derive the special case (`scan` = prefix ''). Sort by an explicit key (`fv[0]`) so values of mixed types are never compared.",
            "alternative": "Keep each record's fields in a sorted list (`bisect`) for O(log n + k) prefix scans; worth it only if scans dominate writes. For interview sizes, sort on read.",
        },
        {
            "title": "Level 3: TTL with explicit timestamps",
            "minutes": 12,
            "prompt": code(r'''
                Every method gains an optional timestamp `ts=0` (ints, non-decreasing). `set` also takes `ttl=None`:

                - `set(key, field, value, ts=0, ttl=None)` - with a ttl the field lives in `[ts, ts + ttl)`; without one it never expires. Overwriting replaces the old expiry.
                - `get / delete / scan / scan_by_prefix(..., ts=0)` - treat expired fields as missing (`delete` of an expired field returns `False`).

                ```python
                db.set("k", "a", 1, ts=10, ttl=5)
                db.get("k", "a", ts=14)   # 1
                db.get("k", "a", ts=15)   # None
                ```
            '''),
            "tests": KV_T3,
            "hints": [
                "Each field now needs a second piece of data next to its value. Where do you keep it?",
                "Store `(value, expires_at)` with `expires_at = ts + ttl` or `None`. Write one `_alive(entry, ts)` helper.",
                "`_alive`: `expires_at is None or ts < expires_at`. Use it in get, delete and inside the scan filter; don't bother deleting expired entries eagerly.",
            ],
            "solution": KV_S3,
            "lesson": "When a level changes what you store, change the stored shape once (value -> (value, expires_at)) and funnel every read through a single liveness check. Absolute expiry times make the comparison trivial; lazy expiry avoids a background sweeper.",
            "alternative": "Keep a min-heap of (expires_at, key, field) and purge expired entries at the start of each call. That frees memory but adds bookkeeping for overwrites (stale heap entries); lazy checks are simpler and correct.",
        },
        {
            "title": "Level 4: backup and restore",
            "minutes": 12,
            "prompt": code(r'''
                Add persistence:

                - `dump(ts=0) -> str` - a **JSON string** snapshot of all fields live at `ts`. Expired fields are left out.
                - `load(blob, ts=0) -> None` - **replace** the whole DB with the snapshot. A field that had `r` time units left when dumped must expire `r` units after the load `ts`.

                ```python
                db.set("s", "tok", "abc", ts=0, ttl=10)
                blob = db.dump(ts=4)        # 6 left
                db2 = InMemoryDB(); db2.load(blob, ts=100)
                db2.get("s", "tok", ts=105) # "abc"
                db2.get("s", "tok", ts=106) # None
                ```
            '''),
            "tests": KV_T4,
            "hints": [
                "Absolute expiry times are meaningless after a restore at another time. What should the snapshot store instead?",
                "Store `[value, remaining]` where `remaining = expires_at - ts` (or `None`). JSON has no tuples, so use lists.",
                "`load`: `json.loads`, then rebuild `{field: (value, None if r is None else ts + r)}` per key and assign `self._data = data` (a fresh dict, not a merge).",
            ],
            "solution": KV_S4,
            "lesson": "Serialize relative state (time remaining), not absolute state tied to a clock, and re-anchor on load. Build the new state completely and swap it in at the end so a bad blob can't leave a half-restored DB.",
            "alternative": "`copy.deepcopy(self._data)` gives an in-process snapshot with no encoding step, but it isn't portable to a file and keeps absolute expiries, so restoring later resurrects or kills fields wrongly.",
        },
    ],
}

# ---------------------------------------------------------------------------
# 2. File deduplication
# ---------------------------------------------------------------------------

DD_S1 = code(r'''
    from collections import defaultdict


    def find_duplicates(files):
        by_content = defaultdict(list)
        for path, content in files.items():
            by_content[content].append(path)
        return sorted(sorted(paths) for paths in by_content.values() if len(paths) > 1)
''')

DD_S2 = code(r'''
    import hashlib
    from collections import defaultdict


    def find_duplicates(sizes, read):
        by_size = defaultdict(list)
        for path, size in sizes.items():
            by_size[size].append(path)

        groups = []
        for paths in by_size.values():
            if len(paths) < 2:
                continue  # a unique size can't have a duplicate: never read it
            by_hash = defaultdict(list)
            for path in paths:
                by_hash[hashlib.sha256(read(path)).hexdigest()].append(path)
            groups += [g for g in by_hash.values() if len(g) > 1]
        return sorted(sorted(g) for g in groups)
''')

DD_S3 = code(r'''
    import hashlib
    from collections import defaultdict


    def find_duplicates(sizes, read_chunks):
        by_size = defaultdict(list)
        for path, size in sizes.items():
            by_size[size].append(path)

        groups = []
        for paths in by_size.values():
            if len(paths) > 1:
                groups += _split_by_content(paths, read_chunks)
        return sorted(sorted(g) for g in groups)


    def _split_by_content(paths, read_chunks):
        """Read same-size files chunk by chunk in lock-step. After each chunk,
        split the group by that chunk's hash; a file alone in its bucket is
        unique, so we stop reading it (early exit)."""
        streams = {p: iter(read_chunks(p)) for p in paths}
        pending, done = [list(paths)], []
        while pending:
            group = pending.pop()
            buckets = defaultdict(list)
            for path in group:
                chunk = next(streams[path], None)          # None = end of file
                digest = None if chunk is None else hashlib.sha256(chunk).digest()
                buckets[digest].append(path)
            for digest, members in buckets.items():
                if len(members) < 2:
                    continue
                if digest is None:
                    done.append(members)     # identical all the way to EOF
                else:
                    pending.append(members)  # still equal: read the next chunk
        return done
''')

DD_S4 = DD_S3 + "\n\n" + code(r'''
    def choose_keeper(paths):
        return min(paths, key=lambda p: (len(p), p))  # shortest, then lexicographic


    def dedup_report(sizes, read_chunks):
        groups = []
        for paths in find_duplicates(sizes, read_chunks):
            keep = choose_keeper(paths)
            remove = sorted(p for p in paths if p != keep)
            groups.append({"keep": keep, "remove": remove,
                           "wasted": sizes[keep] * len(remove)})
        groups.sort(key=lambda g: (-g["wasted"], g["keep"]))
        return {"groups": groups, "wasted_bytes": sum(g["wasted"] for g in groups)}
''')

DD_T1 = code(r'''
    def test_basic_groups():
        files = {"a.txt": b"hello", "b.txt": b"world", "c.txt": b"hello"}
        assert find_duplicates(files) == [["a.txt", "c.txt"]], "a and c have identical bytes"

    def test_no_duplicates():
        assert find_duplicates({"x": b"1", "y": b"2"}) == [], "unique files -> []"
        assert find_duplicates({}) == [], "empty input -> []"

    def test_sorted_output():
        files = {"z": b"A", "m": b"A", "q": b"B", "b": b"B", "k": b"A"}
        assert find_duplicates(files) == [["b", "q"], ["k", "m", "z"]], \
            "paths sorted inside each group, groups sorted by their first path"
''')

DD_T2 = code(r'''
    def make_fs(files):
        reads = []
        sizes = {p: len(b) for p, b in files.items()}
        def read(path):
            reads.append(path)
            return files[path]
        return sizes, read, reads

    def test_basic_groups():
        sizes, read, _ = make_fs({"a.txt": b"hello", "b.txt": b"world", "c.txt": b"hello"})
        assert find_duplicates(sizes, read) == [["a.txt", "c.txt"]]

    def test_sorted_output():
        sizes, read, _ = make_fs({"z": b"A", "m": b"A", "q": b"B", "b": b"B", "k": b"A"})
        assert find_duplicates(sizes, read) == [["b", "q"], ["k", "m", "z"]]

    def test_unique_sizes_never_read():
        sizes, read, reads = make_fs({"big": b"x" * 100, "mid": b"y" * 50, "s1": b"ab", "s2": b"ab"})
        assert find_duplicates(sizes, read) == [["s1", "s2"]]
        assert "big" not in reads and "mid" not in reads, \
            f"files with a unique size must not be read, but read {reads}"

    def test_each_file_read_once():
        sizes, read, reads = make_fs({"a": b"1234", "b": b"1234", "c": b"5678", "d": b"1234"})
        assert find_duplicates(sizes, read) == [["a", "b", "d"]]
        assert sorted(reads) == ["a", "b", "c", "d"], \
            f"hash each candidate once (no pairwise compares): reads={reads}"

    def test_same_size_different_content():
        sizes, read, _ = make_fs({"a": b"abcd", "b": b"abce"})
        assert find_duplicates(sizes, read) == [], "same size is not enough"
''')

DD_T3 = code(r'''
    from collections import defaultdict as _dd

    def make_fs(files, chunk=4):
        consumed, opened = _dd(int), []
        sizes = {p: len(b) for p, b in files.items()}
        def read_chunks(path):
            opened.append(path)
            data = files[path]
            for i in range(0, len(data), chunk):
                consumed[path] += 1
                yield data[i:i + chunk]
        return sizes, read_chunks, consumed, opened

    def test_basic_groups():
        sizes, rc, _, _ = make_fs({"a.txt": b"hello", "b.txt": b"world", "c.txt": b"hello"})
        assert find_duplicates(sizes, rc) == [["a.txt", "c.txt"]]

    def test_sorted_output():
        sizes, rc, _, _ = make_fs({"z": b"A", "m": b"A", "q": b"B", "b": b"B", "k": b"A"})
        assert find_duplicates(sizes, rc) == [["b", "q"], ["k", "m", "z"]]

    def test_unique_sizes_never_opened():
        sizes, rc, _, opened = make_fs({"big": b"x" * 100, "s1": b"abcdefgh", "s2": b"abcdefgh"})
        assert find_duplicates(sizes, rc) == [["s1", "s2"]]
        assert "big" not in opened, "a file with a unique size must never be opened"

    def test_early_exit_on_first_differing_chunk():
        files = {"a": b"AAAABBBBCCCC", "b": b"AAAABBBBCCCC",
                 "c": b"ZZZZBBBBCCCC", "d": b"AAAABBBBDDDD"}
        sizes, rc, consumed, _ = make_fs(files)
        assert find_duplicates(sizes, rc) == [["a", "b"]]
        assert consumed["c"] == 1, f"'c' differs in chunk 1, stop after 1 chunk (read {consumed['c']})"
        assert consumed["d"] == 3, "'d' only differs in chunk 3"

    def test_chunks_across_many_chunks():
        same = bytes(range(256)) * 4
        sizes, rc, _, _ = make_fs({"p": same, "q": same, "r": same[:-1] + b"!"}, chunk=64)
        assert find_duplicates(sizes, rc) == [["p", "q"]], "last byte differs for r"

    def test_empty_files_are_duplicates():
        sizes, rc, _, _ = make_fs({"e1": b"", "e2": b"", "x": b"1"})
        assert find_duplicates(sizes, rc) == [["e1", "e2"]], "two empty files are identical"
''')

DD_T4 = DD_T3 + "\n" + code(r'''
    def test_report_basic():
        files = {"docs/a.txt": b"hello!", "a.txt": b"hello!", "backup/a.txt": b"hello!",
                 "x": b"zz", "y": b"zz", "solo": b"unique-file"}
        sizes, rc, _, _ = make_fs(files)
        rep = dedup_report(sizes, rc)
        assert rep["groups"][0] == {"keep": "a.txt", "remove": ["backup/a.txt", "docs/a.txt"],
                                    "wasted": 12}, f"shortest path is kept: {rep['groups'][0]}"
        assert rep["groups"][1] == {"keep": "x", "remove": ["y"], "wasted": 2}
        assert rep["wasted_bytes"] == 14, "total = sum of group waste"

    def test_keeper_tie_breaks_lexicographically():
        sizes, rc, _, _ = make_fs({"b/f": b"same", "a/f": b"same", "c/f": b"same"})
        rep = dedup_report(sizes, rc)
        assert rep["groups"][0]["keep"] == "a/f", "equal length -> lexicographically smallest"
        assert rep["groups"][0]["remove"] == ["b/f", "c/f"]

    def test_groups_sorted_by_waste():
        sizes, rc, _, _ = make_fs({"s1": b"ab", "s2": b"ab", "s3": b"ab",
                                   "L1": b"x" * 10, "L2": b"x" * 10})
        rep = dedup_report(sizes, rc)
        assert [g["wasted"] for g in rep["groups"]] == [10, 4], "biggest waste first"

    def test_report_empty():
        sizes, rc, _, _ = make_fs({"a": b"1", "b": b"2"})
        assert dedup_report(sizes, rc) == {"groups": [], "wasted_bytes": 0}
''')

DEDUP = {
    "id": "fde-ch-file-dedup", "type": "challenge", "stage": "coding", "difficulty": 2,
    "tags": ["hashing", "hashlib", "generators", "defaultdict", "progressive"],
    "pattern": "cheap filter first, expensive check only on candidates",
    "title": "File deduplication (4 levels)",
    "summary": "Find duplicate files, then make it efficient the way real tools do: group by size, hash only collisions, stream big files chunk by chunk with early exit, and finally produce an actionable cleanup report.",
    "talkPrompts": [
        "Equal content implies equal size, so size is a free first filter - unique sizes are never read.",
        "I'll use sha256 so each file is read once; comparing pairs would be O(n^2) reads.",
        "For big files I compare chunk by chunk in lock-step and drop a file the moment it is alone in its bucket.",
        "The keeper rule is a sort key: (len(path), path). I'll make it a separate function so it's easy to change.",
        "What about reading errors, symlinks and hard links? I'd flag those as out of scope unless you want them.",
    ],
    "steps": [
        {
            "title": "Level 1: group identical files",
            "minutes": 5,
            "prompt": code(r'''
                `find_duplicates(files) -> list[list[str]]` where `files` is a dict `path -> bytes`.

                Return the groups of paths with **identical content** (only groups of 2+). Sort paths inside each group, and sort the groups.

                ```python
                find_duplicates({"a": b"hi", "b": b"yo", "c": b"hi"})
                # [["a", "c"]]
                ```
            '''),
            "starter": code(r'''
                def find_duplicates(files):
                    pass
            '''),
            "tests": DD_T1,
            "hints": [
                "Invert the mapping: content -> paths.",
                "`bytes` are hashable, so they can be dict keys. `defaultdict(list)` collects the paths.",
                "`sorted(sorted(ps) for ps in by_content.values() if len(ps) > 1)`",
            ],
            "solution": DD_S1,
            "lesson": "Grouping = invert the mapping into `defaultdict(list)` keyed by the property that defines 'same'. Sort at the end for deterministic output.",
            "alternative": "`itertools.groupby(sorted(files.items(), key=...))` also works but needs a sort first and is easier to get wrong (groupby only merges adjacent items).",
        },
        {
            "title": "Level 2: size first, then sha256",
            "minutes": 8,
            "prompt": code(r'''
                Files are now too big to hold in a dict. New signature:

                `find_duplicates(sizes, read) -> list[list[str]]`

                - `sizes`: dict `path -> size in bytes` (free to look at)
                - `read(path) -> bytes` (expensive)

                Rules: **never call `read` on a file whose size is unique**, read each candidate **at most once**, and compare by `hashlib.sha256` digest. Same output format as before.
            '''),
            "tests": DD_T2,
            "hints": [
                "Two files can only be equal if their sizes are equal. Group by size before touching content.",
                "Bucket paths by size; skip buckets with one path. Inside a bucket, bucket again by `hashlib.sha256(read(p)).hexdigest()`.",
                "Collect `[g for g in by_hash.values() if len(g) > 1]` from each size bucket, then sort like level 1.",
            ],
            "solution": DD_S2,
            "lesson": "Funnel pattern: apply the cheapest discriminating filter first (size, from metadata), and the expensive one (read + hash) only on survivors. Hashing turns n^2 pairwise comparisons into n reads plus a dict lookup.",
            "alternative": "Hash only the first 4 KB as a middle filter before the full hash (what fdupes-style tools do). It saves reads when many files share a size but differ early - which level 3 generalizes.",
        },
        {
            "title": "Level 3: stream chunks, exit early",
            "minutes": 12,
            "prompt": code(r'''
                `read` is replaced by `read_chunks(path)`, a generator of `bytes` chunks (fixed chunk size, so same-size files yield the same number of chunks).

                `find_duplicates(sizes, read_chunks)`:

                - still never open unique-size files;
                - read same-size files **chunk by chunk in lock-step**, hashing each chunk;
                - as soon as a file's chunk differs from all others in its group, **stop reading it**.

                Example: `a=b"AAAABBBB"`, `b=b"AAAABBBB"`, `c=b"ZZZZBBBB"` (chunk 4): `c` is read for 1 chunk only. Empty files are still duplicates of each other.
            '''),
            "tests": DD_T3,
            "hints": [
                "Open one iterator per candidate file and advance them together with `next(it, None)` (None = end of file).",
                "Keep a work list of groups. For a group, read one chunk from each member and bucket by the chunk's sha256; buckets of size 1 are dropped (no more reads).",
                "A bucket whose key is None (all members hit EOF together) is a finished duplicate group; any other bucket of 2+ goes back on the work list.",
            ],
            "solution": DD_S3,
            "lesson": "Refine partitions incrementally: split a candidate group by the next piece of evidence and only keep reading where there is still ambiguity. `next(iterator, None)` lets you drive several generators in lock-step without exceptions.",
            "alternative": "Feed every chunk into one `hashlib.sha256()` per file (`h.update(chunk)`) and group by the final digest. Simpler and constant memory, but reads every candidate to the end - no early exit.",
        },
        {
            "title": "Level 4: cleanup report",
            "minutes": 8,
            "prompt": code(r'''
                Add `dedup_report(sizes, read_chunks) -> dict`:

                ```python
                {"groups": [{"keep": "a.txt",
                             "remove": ["backup/a.txt", "docs/a.txt"],
                             "wasted": 12}],
                 "wasted_bytes": 12}
                ```

                - **keep** = shortest path, ties broken lexicographically; `remove` = the others, sorted.
                - **wasted** = size x number of removed copies.
                - Groups sorted by `wasted` descending, then by `keep`. `find_duplicates` must keep working.
            '''),
            "tests": DD_T4,
            "hints": [
                "Reuse `find_duplicates` - the report is just post-processing of its groups.",
                "The keeper is `min(paths, key=lambda p: (len(p), p))`: tuples compare element by element.",
                "`wasted = sizes[keep] * len(remove)`; sort with `key=lambda g: (-g['wasted'], g['keep'])` and sum for the total.",
            ],
            "solution": DD_S4,
            "lesson": "Encode multi-criteria rules as tuple sort keys, and negate a numeric field for descending order. Keep policy (which copy to keep) in its own small function so the customer can change it without touching the algorithm.",
            "alternative": "Return dataclasses instead of dicts for typed, self-documenting output; dicts are quicker to write and JSON-ready for an API response.",
        },
    ],
}

# ---------------------------------------------------------------------------
# 3. Log / trace parsing (S15: process call stacks into execution traces)
# ---------------------------------------------------------------------------

LOG_S1 = code(r'''
    LEVELS = {"DEBUG", "INFO", "WARN", "ERROR"}
    ALIASES = {"WARNING": "WARN"}


    def parse_line(line):
        parts = line.strip().split(maxsplit=3)   # msg may contain spaces
        if len(parts) < 3:
            return None
        ts, level, service = parts[:3]
        level = ALIASES.get(level.upper(), level.upper())
        if level not in LEVELS:
            return None
        msg = parts[3] if len(parts) == 4 else ""
        return {"ts": ts, "level": level, "service": service, "msg": msg}
''')

LOG_S2 = LOG_S1 + "\n\n" + code(r'''
    from collections import Counter


    def error_counts(lines):
        counts = Counter()
        for line in lines:
            entry = parse_line(line)
            if entry and entry["level"] == "ERROR":
                counts[entry["service"]] += 1
        return dict(counts)


    def top_error_services(lines, n=3):
        counts = error_counts(lines)
        return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:n]
''')

LOG_S3 = LOG_S2 + "\n\n" + code(r'''
    from collections import defaultdict

    SPAN_FIELDS = ("trace", "id", "parent", "start", "end", "name")


    def parse_span(line):
        entry = parse_line(line)
        if entry is None or not entry["msg"].startswith("span "):
            return None
        fields = dict(tok.split("=", 1) for tok in entry["msg"].split()[1:] if "=" in tok)
        if any(f not in fields for f in SPAN_FIELDS):
            return None
        try:
            start, end = int(fields["start"]), int(fields["end"])
        except ValueError:
            return None
        if end < start:
            return None
        return {"trace": fields["trace"], "id": fields["id"],
                "parent": None if fields["parent"] == "-" else fields["parent"],
                "name": fields["name"], "service": entry["service"],
                "start": start, "end": end, "children": []}


    def build_traces(lines):
        spans = defaultdict(dict)                       # trace -> span id -> node
        for line in lines:
            span = parse_span(line)
            if span:
                spans[span["trace"]].setdefault(span["id"], span)

        def order(node):
            return (node["start"], node["id"])

        traces = {}
        for trace_id, nodes in spans.items():           # 2nd pass: parents may come later
            roots = []
            for node in nodes.values():
                parent = nodes.get(node["parent"])
                (parent["children"] if parent else roots).append(node)
            for node in nodes.values():
                node["children"].sort(key=order)
            traces[trace_id] = sorted(roots, key=order)
        return traces
''')

LOG_S4 = LOG_S3 + "\n\n" + code(r'''
    def duration(node):
        return node["end"] - node["start"]


    def critical_path(lines, trace_id):
        roots = build_traces(lines).get(trace_id)
        if not roots:
            return [], 0
        node = max(roots, key=duration)        # max keeps the first on ties
        total = duration(node)
        path = [node["id"]]
        while node["children"]:
            # the parent was waiting on whichever child finished last
            node = max(node["children"], key=lambda c: (c["end"], duration(c)))
            path.append(node["id"])
        return path, total
''')

LOG_COMMON = code(r'''
    LOGS = [
        "2024-05-01T10:00:00Z INFO api request received GET /checkout",
        "2024-05-01T10:00:01Z ERROR payments card declined for user 42",
        "2024-05-01T10:00:02Z error payments timeout talking to bank",
        "garbage",
        "",
        "2024-05-01T10:00:03Z WARNING api slow response",
        "2024-05-01T10:00:04Z ERROR db connection reset",
        "2024-05-01T10:00:05Z FATAL db unknown level is malformed",
        "2024-05-01T10:00:06Z ERROR auth",
    ]
''')

LOG_T1 = LOG_COMMON + "\n" + code(r'''
    def test_parse_basic():
        e = parse_line("2024-05-01T10:00:01Z ERROR payments card declined for user 42")
        assert e == {"ts": "2024-05-01T10:00:01Z", "level": "ERROR", "service": "payments",
                     "msg": "card declined for user 42"}, f"got {e}"

    def test_level_normalised():
        assert parse_line("t1 error svc boom")["level"] == "ERROR", "levels are case-insensitive"
        assert parse_line("t1 WARNING svc slow")["level"] == "WARN", "WARNING is an alias of WARN"

    def test_empty_message_ok():
        assert parse_line("t1 ERROR auth") == {"ts": "t1", "level": "ERROR", "service": "auth", "msg": ""}

    def test_malformed_lines():
        for bad in ["garbage", "", "   ", "t1 ERROR", "t1 FATAL db x"]:
            assert parse_line(bad) is None, f"{bad!r} should parse to None"

    def test_whitespace_tolerated():
        e = parse_line("  t1   INFO   api   hello   world \n")
        assert e is not None and e["service"] == "api" and e["msg"] == "hello   world", f"got {e}"
''')

LOG_T2 = LOG_T1 + "\n" + code(r'''
    def test_error_counts():
        assert error_counts(LOGS) == {"payments": 2, "db": 1, "auth": 1}, \
            "count ERROR lines per service; skip malformed and non-error lines"

    def test_error_counts_empty():
        assert error_counts([]) == {}
        assert error_counts(["junk", "t1 INFO api ok"]) == {}

    def test_top_error_services():
        assert top_error_services(LOGS, 2) == [("payments", 2), ("auth", 1)], \
            "sort by count desc, then service name"
        assert top_error_services(LOGS) == [("payments", 2), ("auth", 1), ("db", 1)], "default n=3"
''')

SPANS = code(r'''
    SPAN_LOGS = [
        "t0 INFO api span trace=t1 id=a parent=- start=0 end=100 name=checkout",
        "t0 INFO pay span trace=t1 id=c parent=a start=30 end=90 name=charge",
        "t0 INFO api span trace=t1 id=b parent=a start=5 end=25 name=auth",
        "t0 INFO bank span trace=t1 id=d parent=c start=35 end=85 name=bank_call",
        "t0 INFO pay span trace=t1 id=e parent=c start=31 end=40 name=fraud",
        "t0 ERROR api span trace=t1 id=x parent=a start=oops end=9 name=bad_int",
        "t0 INFO api span trace=t1 id=y start=1 end=2 name=missing_parent_field",
        "t0 INFO api span trace=t1 id=z parent=a start=9 end=3 name=end_before_start",
        "t0 INFO web span trace=t2 id=r parent=- start=0 end=10 name=home",
        "t0 INFO web span trace=t2 id=o parent=ghost start=2 end=4 name=orphan",
        "t0 INFO api request received",
        "not a log line",
    ]

    def shape(node):
        return (node["id"], [shape(c) for c in node["children"]])
''')

LOG_T3 = LOG_T2 + "\n" + SPANS + "\n" + code(r'''
    def test_tree_built_out_of_order():
        traces = build_traces(SPAN_LOGS)
        roots = traces["t1"]
        assert [shape(r) for r in roots] == [("a", [("b", []), ("c", [("e", []), ("d", [])])])], \
            f"children sorted by start; got {[shape(r) for r in roots]}"

    def test_node_fields():
        root = build_traces(SPAN_LOGS)["t1"][0]
        assert (root["name"], root["service"], root["start"], root["end"]) == ("checkout", "api", 0, 100)

    def test_malformed_spans_skipped():
        ids = set()
        def walk(n):
            ids.add(n["id"]); [walk(c) for c in n["children"]]
        for r in build_traces(SPAN_LOGS)["t1"]:
            walk(r)
        assert ids == {"a", "b", "c", "d", "e"}, f"bad spans must be skipped, got {sorted(ids)}"

    def test_orphan_becomes_root():
        roots = build_traces(SPAN_LOGS)["t2"]
        assert [shape(r) for r in roots] == [("r", []), ("o", [])], "unknown parent -> treat as a root"

    def test_no_spans():
        assert build_traces(["t1 INFO api hello", "junk"]) == {}
''')

LOG_T4 = LOG_T3 + "\n" + code(r'''
    def test_critical_path():
        path, total = critical_path(SPAN_LOGS, "t1")
        assert path == ["a", "c", "d"], f"follow the child that finished last: got {path}"
        assert total == 100, "total = duration of the root span"

    def test_critical_path_single_span():
        lines = ["t INFO s span trace=q id=only parent=- start=5 end=12 name=n"]
        assert critical_path(lines, "q") == (["only"], 7)

    def test_longest_root_chosen():
        lines = SPAN_LOGS + ["t INFO web span trace=t2 id=big parent=- start=0 end=50 name=batch"]
        assert critical_path(lines, "t2") == (["big"], 50), "with several roots, start from the longest"

    def test_tie_on_end_prefers_longer_child():
        lines = [
            "t INFO s span trace=k id=root parent=- start=0 end=20 name=r",
            "t INFO s span trace=k id=short parent=root start=15 end=18 name=s",
            "t INFO s span trace=k id=long parent=root start=2 end=18 name=l",
        ]
        assert critical_path(lines, "k") == (["root", "long"], 20), "equal end -> longer child"

    def test_unknown_trace():
        assert critical_path(SPAN_LOGS, "nope") == ([], 0)
''')

LOGS = {
    "id": "fde-ch-log-traces", "type": "challenge", "stage": "coding", "difficulty": 3,
    "source": "S15",
    "tags": ["parsing", "trees", "Counter", "defaultdict", "progressive"],
    "pattern": "parse defensively, then build a tree in two passes",
    "title": "Logs to execution traces (4 levels)",
    "summary": "Parse messy service logs, aggregate errors, rebuild distributed traces from span lines into nested trees, and find the critical path. Mirrors the reported 'process call stacks into execution traces' question.",
    "talkPrompts": [
        "Real logs are dirty, so the parser returns None for anything malformed instead of raising - one bad line must not kill the job.",
        "split(maxsplit=3) keeps spaces inside the message.",
        "Children can appear before their parents, so I index every span first and link them in a second pass.",
        "An orphan span with an unknown parent becomes a root rather than vanishing - you'd want to see it.",
        "Critical path: the parent is blocked on the child that finishes last, so I follow max end time down the tree.",
    ],
    "steps": [
        {
            "title": "Level 1: parse one line",
            "minutes": 6,
            "prompt": code(r'''
                Lines look like `"<ts> <level> <service> <msg...>"`; the message may contain spaces or be empty.

                `parse_line(line) -> dict | None` returns `{"ts", "level", "service", "msg"}`:

                - `level` is case-insensitive, normalised to upper case; `WARNING` -> `WARN`;
                - valid levels: `DEBUG INFO WARN ERROR`;
                - return `None` for malformed lines (fewer than 3 parts, unknown level). Never raise.

                ```python
                parse_line("t1 error pay card declined")
                # {"ts": "t1", "level": "ERROR", "service": "pay", "msg": "card declined"}
                ```
            '''),
            "starter": code(r'''
                def parse_line(line):
                    pass
            '''),
            "tests": LOG_T1,
            "hints": [
                "`str.split()` with no separator also collapses runs of whitespace. How do you stop it splitting the message?",
                "`line.strip().split(maxsplit=3)` gives at most 4 parts; the 4th is the whole message.",
                "Check `len(parts) < 3`, normalise with an alias dict (`{'WARNING': 'WARN'}`), check membership in a `LEVELS` set, and default msg to `''`.",
            ],
            "solution": LOG_S1,
            "lesson": "Defensive parsing: return a sentinel (None) for bad input and let the caller skip it. `split(maxsplit=n)` is the idiom for 'fixed columns, then free text'.",
            "alternative": "A regex like `^(\\S+)\\s+(\\S+)\\s+(\\S+)\\s*(.*)$` documents the format in one place; it's harder to read under time pressure but easier to extend with stricter ts validation.",
        },
        {
            "title": "Level 2: errors per service",
            "minutes": 6,
            "prompt": code(r'''
                Add:

                - `error_counts(lines) -> dict` - `service -> number of ERROR lines` (services with 0 errors are absent; malformed lines skipped).
                - `top_error_services(lines, n=3) -> list[tuple]` - `(service, count)` sorted by count **descending**, ties by service name.

                ```python
                error_counts(logs)          # {"payments": 2, "db": 1, "auth": 1}
                top_error_services(logs, 2) # [("payments", 2), ("auth", 1)]
                ```
            '''),
            "tests": LOG_T2,
            "hints": [
                "Reuse `parse_line`; skip `None` results.",
                "`collections.Counter` handles the counting. Return `dict(counts)`.",
                "Sort with `key=lambda kv: (-kv[1], kv[0])` and slice `[:n]`. (`most_common` doesn't break ties by name.)",
            ],
            "solution": LOG_S2,
            "lesson": "Compose: parse -> filter -> aggregate. Use a tuple key with a negated count for 'desc by count, asc by name' - `Counter.most_common` keeps insertion order on ties, which is not deterministic enough for a spec.",
            "alternative": "`heapq.nsmallest(n, counts.items(), key=lambda kv: (-kv[1], kv[0]))` is O(m log n) instead of a full sort - useful with millions of services, overkill here.",
        },
        {
            "title": "Level 3: rebuild traces",
            "minutes": 12,
            "prompt": code(r'''
                Some messages are spans:
                `t0 INFO pay span trace=t1 id=c parent=a start=30 end=90 name=charge` (`parent=-` means root).

                `build_traces(lines) -> dict` maps `trace_id -> list of root nodes`. A node is a dict with at least `id, name, service, start, end, children`.

                - Spans may arrive **in any order** (child before parent).
                - Sort children and roots by `(start, id)`.
                - A span whose parent isn't in the trace becomes a root.
                - Skip malformed spans: a missing field, non-int start/end, or `end < start`.
            '''),
            "tests": LOG_T3,
            "hints": [
                "Because a child may come before its parent, you can't attach on the fly. Think two passes.",
                "Pass 1: parse every span into a node dict and index it as `spans[trace][id] = node`. Pass 2: append each node to `nodes[parent]['children']`, or to `roots` if the parent is missing.",
                "Parse the `key=value` tokens with `dict(tok.split('=', 1) for tok in msg.split()[1:] if '=' in tok)`, convert start/end in a try/except ValueError, then sort with `key=lambda n: (n['start'], n['id'])`.",
            ],
            "solution": LOG_S3,
            "lesson": "Building a tree from parent pointers: index all nodes by id first, link in a second pass, and decide explicitly what happens to orphans. Shared mutable node dicts mean appending to `children` builds the whole tree in place.",
            "alternative": "Build a `children_of = defaultdict(list)` adjacency map and construct nodes recursively from the roots. Cleaner output objects, but you need cycle protection (a visited set) to avoid infinite recursion on bad data.",
        },
        {
            "title": "Level 4: critical path",
            "minutes": 9,
            "prompt": code(r'''
                `critical_path(lines, trace_id) -> (list[str], int)`:

                - start at the trace's **longest root** (first in root order on ties);
                - repeatedly step to the child that **ends last** (tie: longer duration, then first in child order) until a leaf;
                - return the span ids on that path and the root's duration (`end - start`).

                Unknown trace -> `([], 0)`.

                ```python
                critical_path(SPAN_LOGS, "t1")   # (["a", "c", "d"], 100)
                ```
            '''),
            "tests": LOG_T4,
            "hints": [
                "Reuse `build_traces`; the path is a walk down the tree, not a search over all paths.",
                "`max(iterable, key=...)` returns the FIRST maximal element, so ties fall back to the existing (start, id) order for free.",
                "`node = max(node['children'], key=lambda c: (c['end'], c['end'] - c['start']))` in a `while node['children']` loop, appending ids.",
            ],
            "solution": LOG_S4,
            "lesson": "Critical path in nested spans = the chain of 'last to finish' children: shortening anything off that chain doesn't make the request faster. Lean on stable `max`/`sorted` so tie-breaking is decided by order you already defined.",
            "alternative": "Compute each span's self time (duration minus time covered by children) and report the spans with the largest self time. That finds 'where the time is actually spent', which is often more useful to a customer than the path.",
        },
    ],
}

# ---------------------------------------------------------------------------
# 4. Retry with backoff
# ---------------------------------------------------------------------------

RETRY_ERRORS = code(r'''
    import time


    class APIError(Exception):
        """An HTTP error from an API call."""
        def __init__(self, status, message=""):
            super().__init__(f"HTTP {status} {message}".strip())
            self.status = status


    class RateLimitError(APIError):
        """HTTP 429. retry_after: seconds the server asked us to wait, or None."""
        def __init__(self, retry_after=None):
            super().__init__(429, "rate limited")
            self.retry_after = retry_after
''')

RT_S1 = RETRY_ERRORS + "\n\n" + code(r'''
    def retry(fn, attempts=3):
        for attempt in range(attempts):
            try:
                return fn()
            except Exception:
                if attempt == attempts - 1:
                    raise              # out of attempts: surface the last error
''')

RT_S2 = RETRY_ERRORS + "\n\n" + code(r'''
    def retry(fn, attempts=3, base_delay=0.5, max_delay=8.0, sleep=time.sleep, jitter=None):
        for attempt in range(attempts):
            try:
                return fn()
            except Exception:
                if attempt == attempts - 1:
                    raise
                delay = min(max_delay, base_delay * 2 ** attempt)
                sleep(jitter(delay) if jitter else delay)
''')

RT_S3 = RETRY_ERRORS + "\n\n" + code(r'''
    def is_retryable(exc):
        return isinstance(exc, APIError) and (exc.status == 429 or exc.status >= 500)


    def backoff_delay(exc, attempt, base_delay, max_delay, jitter):
        if isinstance(exc, RateLimitError) and exc.retry_after is not None:
            return exc.retry_after                    # the server knows best
        delay = min(max_delay, base_delay * 2 ** attempt)
        return jitter(delay) if jitter else delay


    def retry(fn, attempts=3, base_delay=0.5, max_delay=8.0, sleep=time.sleep, jitter=None):
        for attempt in range(attempts):
            try:
                return fn()
            except Exception as exc:
                if not is_retryable(exc) or attempt == attempts - 1:
                    raise
                sleep(backoff_delay(exc, attempt, base_delay, max_delay, jitter))
''')

RT_S4 = "import functools\n" + RETRY_ERRORS + "\n\n" + code(r'''
    def is_retryable(exc):
        return isinstance(exc, APIError) and (exc.status == 429 or exc.status >= 500)


    def backoff_delay(exc, attempt, base_delay, max_delay, jitter):
        if isinstance(exc, RateLimitError) and exc.retry_after is not None:
            return exc.retry_after
        delay = min(max_delay, base_delay * 2 ** attempt)
        return jitter(delay) if jitter else delay


    def retry(fn, attempts=3, base_delay=0.5, max_delay=8.0, sleep=time.sleep,
              jitter=None, deadline=None, clock=time.monotonic):
        start = clock()
        for attempt in range(attempts):
            try:
                return fn()
            except Exception as exc:
                if not is_retryable(exc) or attempt == attempts - 1:
                    raise
                delay = backoff_delay(exc, attempt, base_delay, max_delay, jitter)
                if deadline is not None and clock() - start + delay > deadline:
                    raise                     # sleeping would blow the budget
                sleep(delay)


    def retrying(**options):
        """Decorator form: @retrying(attempts=5, sleep=fake_sleep)."""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return retry(lambda: func(*args, **kwargs), **options)
            return wrapper
        return decorator
''')

RT_HELPERS = code(r'''
    def flaky(*outcomes):
        """fn() that raises/returns the given outcomes in order; calls counts invocations."""
        calls = []
        it = iter(outcomes)
        def fn():
            calls.append(1)
            o = next(it)
            if isinstance(o, BaseException):
                raise o
            return o
        return fn, calls
''')

RT_T1 = RT_HELPERS + "\n" + code(r'''
    def test_success_first_try():
        fn, calls = flaky("ok")
        assert retry(fn) == "ok"
        assert len(calls) == 1, "no retry when the first call succeeds"

    def test_retries_until_success():
        fn, calls = flaky(APIError(503), APIError(502), "done")
        assert retry(fn, attempts=3) == "done", "two failures then success within 3 attempts"
        assert len(calls) == 3

    def test_gives_up_and_reraises_last():
        last = APIError(504, "third")
        fn, calls = flaky(APIError(500), APIError(503), last)
        try:
            retry(fn, attempts=3)
        except APIError as e:
            assert e is last, "re-raise the LAST exception, not a new one"
        else:
            assert False, "should raise after exhausting attempts"
        assert len(calls) == 3, "attempts counts total calls, including the first"

    def test_attempts_one_means_no_retry():
        fn, calls = flaky(APIError(500), "never")
        try:
            retry(fn, attempts=1)
            assert False, "should raise"
        except APIError:
            pass
        assert len(calls) == 1
''')

RT_SLEEP = code(r'''
    class FakeTime:
        def __init__(self):
            self.now = 0.0
            self.sleeps = []
        def sleep(self, d):
            self.sleeps.append(d)
            self.now += d
        def clock(self):
            return self.now
''')

RT_T2 = RT_T1 + "\n" + RT_SLEEP + "\n" + code(r'''
    def test_exponential_delays():
        t = FakeTime()
        fn, _ = flaky(APIError(500), APIError(500), APIError(500), "ok")
        assert retry(fn, attempts=4, base_delay=0.5, sleep=t.sleep) == "ok"
        assert t.sleeps == [0.5, 1.0, 2.0], f"delay doubles each retry: {t.sleeps}"

    def test_no_sleep_after_last_failure():
        t = FakeTime()
        fn, _ = flaky(APIError(500), APIError(500))
        try:
            retry(fn, attempts=2, base_delay=1, sleep=t.sleep)
        except APIError:
            pass
        assert t.sleeps == [1], "sleep only BETWEEN attempts"

    def test_max_delay_cap():
        t = FakeTime()
        fn, _ = flaky(*([APIError(500)] * 5), "ok")
        retry(fn, attempts=6, base_delay=1, max_delay=5, sleep=t.sleep)
        assert t.sleeps == [1, 2, 4, 5, 5], f"cap each delay at max_delay: {t.sleeps}"

    def test_jitter_applied():
        t = FakeTime()
        seen = []
        def half(d):
            seen.append(d)
            return d / 2
        fn, _ = flaky(APIError(500), APIError(500), "ok")
        retry(fn, attempts=3, base_delay=2, sleep=t.sleep, jitter=half)
        assert seen == [2, 4], "jitter receives the capped exponential delay"
        assert t.sleeps == [1, 2], "and its return value is what we sleep"

    def test_no_sleep_on_success():
        t = FakeTime()
        fn, _ = flaky("ok")
        retry(fn, sleep=t.sleep)
        assert t.sleeps == []
''')

RT_T3 = RT_T2 + "\n" + code(r'''
    def test_client_errors_not_retried():
        for exc in [APIError(400), APIError(404), APIError(401)]:
            t = FakeTime()
            fn, calls = flaky(exc, "never")
            try:
                retry(fn, attempts=5, sleep=t.sleep)
                assert False, "4xx should raise"
            except APIError as e:
                assert e is exc
            assert len(calls) == 1 and t.sleeps == [], f"HTTP {exc.status} must fail fast"

    def test_non_api_errors_not_retried():
        t = FakeTime()
        fn, calls = flaky(ValueError("bug"), "never")
        try:
            retry(fn, attempts=5, sleep=t.sleep)
            assert False, "ValueError should propagate"
        except ValueError:
            pass
        assert len(calls) == 1, "programming errors are never retried"

    def test_rate_limit_retried_with_backoff():
        t = FakeTime()
        fn, calls = flaky(RateLimitError(), "ok")
        assert retry(fn, attempts=3, base_delay=1, sleep=t.sleep) == "ok"
        assert t.sleeps == [1], "429 without retry_after uses normal backoff"

    def test_retry_after_honoured():
        t = FakeTime()
        fn, _ = flaky(RateLimitError(retry_after=7), APIError(503), "ok")
        retry(fn, attempts=3, base_delay=1, max_delay=2, sleep=t.sleep, jitter=lambda d: 0)
        assert t.sleeps == [7, 0], f"sleep exactly retry_after (no jitter/cap), then backoff: {t.sleeps}"
''')

RT_T4 = RT_T3 + "\n" + code(r'''
    def test_deadline_stops_before_oversleeping():
        t = FakeTime()
        fn, calls = flaky(*([APIError(500)] * 10))
        try:
            retry(fn, attempts=10, base_delay=1, sleep=t.sleep, clock=t.clock, deadline=5)
            assert False, "should raise once the next sleep would pass the deadline"
        except APIError:
            pass
        assert t.sleeps == [1, 2], f"1+2=3 elapsed; sleeping 4 more would exceed 5: {t.sleeps}"
        assert len(calls) == 3

    def test_deadline_counts_call_time():
        t = FakeTime()
        outcomes = iter([APIError(500), APIError(500), "ok"])
        def slow():
            t.now += 3                      # each call takes 3 s
            o = next(outcomes)
            if isinstance(o, Exception):
                raise o
            return o
        try:
            retry(slow, attempts=5, base_delay=1, sleep=t.sleep, clock=t.clock, deadline=6)
            assert False, "3 + 1 + 3 = 7 > 6, so the second retry must not happen"
        except APIError:
            pass
        assert t.sleeps == [1]

    def test_no_deadline_by_default():
        t = FakeTime()
        fn, _ = flaky(*([APIError(500)] * 4), "ok")
        assert retry(fn, attempts=5, base_delay=100, sleep=t.sleep, clock=t.clock) == "ok"

    def test_decorator():
        t = FakeTime()
        calls = []
        @retrying(attempts=3, base_delay=1, sleep=t.sleep)
        def fetch(x, scale=1):
            """Fetch a thing."""
            calls.append(x)
            if len(calls) < 3:
                raise APIError(502)
            return x * scale
        assert fetch(4, scale=10) == 40, "decorated function passes args through"
        assert calls == [4, 4, 4] and t.sleeps == [1, 2]
        assert fetch.__name__ == "fetch" and fetch.__doc__ == "Fetch a thing.", "use functools.wraps"

    def test_decorator_fails_fast_on_4xx():
        @retrying(attempts=3, sleep=lambda d: None)
        def bad():
            raise APIError(400)
        try:
            bad()
            assert False
        except APIError as e:
            assert e.status == 400
''')

RETRY = {
    "id": "fde-ch-retry-backoff", "type": "challenge", "stage": "coding", "difficulty": 2,
    "tags": ["error handling", "decorators", "dependency injection", "rate limits", "progressive"],
    "pattern": "inject time (sleep/clock) to make retries testable",
    "title": "Retry with exponential backoff (4 levels)",
    "summary": "Build the retry wrapper every Claude API integration needs: bounded attempts, exponential backoff with jitter, retry only what's retryable (429 / 5xx, honouring retry_after), then a decorator with an overall deadline. Time is injected so tests never sleep.",
    "talkPrompts": [
        "I'll inject sleep and clock so the tests are instant and deterministic - same trick I'd use in production code.",
        "Only transient errors are retryable: 429 and 5xx. A 400 will fail the same way every time, so retrying just burns quota.",
        "If the server sends retry_after I honour it; it knows its own load better than my backoff formula.",
        "Jitter spreads out clients that failed together, so they don't all retry in the same millisecond.",
        "A deadline caps total latency for the user; attempts alone don't bound time once delays grow.",
    ],
    "steps": [
        {
            "title": "Level 1: bounded retries",
            "minutes": 5,
            "prompt": code(r'''
                The starter defines `APIError(status)` and `RateLimitError(retry_after=None)` (status 429). Keep them.

                `retry(fn, attempts=3)` calls `fn()` (no args) up to `attempts` times **in total**:

                - return the first successful result;
                - if every call raises, re-raise the **last** exception.

                ```python
                retry(fn, attempts=3)   # fails, fails, "ok" -> "ok"
                ```
            '''),
            "starter": RETRY_ERRORS + "\n\n" + code(r'''
                def retry(fn, attempts=3):
                    pass
            '''),
            "tests": RT_T1,
            "hints": [
                "Loop over attempt numbers and use try/except inside the loop.",
                "`return fn()` inside `try` exits on success. In `except`, decide whether this was the last attempt.",
                "`except Exception: if attempt == attempts - 1: raise` - a bare `raise` re-raises the current exception with its traceback.",
            ],
            "solution": RT_S1,
            "lesson": "A bare `raise` inside `except` re-raises the original exception object and traceback; wrapping it in a new exception loses the status code callers may branch on.",
            "alternative": "Save `last_exc` in the except block and `raise last_exc` after the loop. Equivalent, but the early `raise` keeps the happy path and the give-up decision in one place.",
        },
        {
            "title": "Level 2: exponential backoff + jitter",
            "minutes": 7,
            "prompt": code(r'''
                New signature:

                `retry(fn, attempts=3, base_delay=0.5, max_delay=8.0, sleep=time.sleep, jitter=None)`

                - Before retry number `k` (0 for the first retry) sleep `min(max_delay, base_delay * 2**k)`.
                - If `jitter` is given, sleep `jitter(delay)` instead.
                - Never sleep after the final failure or after a success.

                base 0.5, 4 failing attempts -> sleeps `[0.5, 1.0, 2.0]`.
            '''),
            "tests": RT_T2,
            "hints": [
                "The attempt index you already loop over is exactly the exponent.",
                "Compute the delay only in the except branch, after deciding it wasn't the last attempt.",
                "`delay = min(max_delay, base_delay * 2 ** attempt)`, then `sleep(jitter(delay) if jitter else delay)`.",
            ],
            "solution": RT_S2,
            "lesson": "Inject side effects (sleep, randomness) as parameters with real defaults. Production uses `time.sleep` and `random.uniform`; tests pass fakes and assert the exact schedule.",
            "alternative": "'Full jitter' (AWS): `sleep(random.uniform(0, delay))`. It spreads retries best under contention; 'equal jitter' (`delay/2 + uniform(0, delay/2)`) keeps a minimum wait. Injecting `jitter` lets the caller choose.",
        },
        {
            "title": "Level 3: retry only what's retryable",
            "minutes": 8,
            "prompt": code(r'''
                Same signature. Now:

                - **Retry** `RateLimitError` (429) and `APIError` with `status >= 500`.
                - **Raise immediately** (no sleep) for other `APIError`s (4xx) and any non-`APIError` exception.
                - A `RateLimitError` with `retry_after` set: sleep **exactly** `retry_after` (no cap, no jitter). Without it, normal backoff.
            '''),
            "tests": RT_T3,
            "hints": [
                "Split the decision into two small functions: should I retry this exception? how long should I wait?",
                "`is_retryable(exc)`: `isinstance(exc, APIError) and (exc.status == 429 or exc.status >= 500)`.",
                "`except Exception as exc: if not is_retryable(exc) or attempt == attempts - 1: raise`; the delay helper returns `exc.retry_after` first when it's a RateLimitError with a value.",
            ],
            "solution": RT_S3,
            "lesson": "Classify errors as transient vs permanent before retrying: a 400 (bad request) or a bug (ValueError) will fail identically every time. Server hints like `retry-after` override your own formula.",
            "alternative": "Accept a `retry_on=(RateLimitError, ...)` tuple or a predicate parameter (like tenacity's `retry_if_exception`). More flexible for customers with different SDKs, at the cost of a wider API.",
        },
        {
            "title": "Level 4: decorator + overall deadline",
            "minutes": 10,
            "prompt": code(r'''
                1. `retry(...)` gains `deadline=None` (seconds) and `clock=time.monotonic`. Measure from the start of `retry`; if `elapsed + next_delay > deadline`, **raise the last error now** instead of sleeping.
                2. Add a decorator factory `retrying(**options)` taking the same keyword options:

                ```python
                @retrying(attempts=3, base_delay=1, sleep=fake_sleep)
                def fetch(x, scale=1): ...
                fetch(4, scale=10)
                ```

                It must pass args through and keep `__name__`/`__doc__`.
            '''),
            "tests": RT_T4,
            "hints": [
                "Read `start = clock()` once, before the loop. Check the budget right before you would sleep.",
                "`if deadline is not None and clock() - start + delay > deadline: raise` - elapsed includes the time the calls took.",
                "Decorator factory = three nested functions: `retrying(**options)` -> `decorator(func)` -> `@functools.wraps(func) wrapper(*args, **kwargs)` returning `retry(lambda: func(*args, **kwargs), **options)`.",
            ],
            "solution": RT_S4,
            "lesson": "Keep one core function and make the decorator a thin adapter (closure over args -> zero-arg callable). Budget by deadline, not just attempt count: what the user feels is total latency.",
            "alternative": "Write `retrying` as a class with `__call__` storing the options; easier to introspect and test, but a closure is the idiomatic short form. Libraries like tenacity/backoff do all of this - mention them, then show you can write it.",
        },
    ],
}

# ---------------------------------------------------------------------------
# 5. Streaming chunk assembler (Anthropic Messages streaming events)
# ---------------------------------------------------------------------------

ST_S1 = code(r'''
    def assemble(events):
        message = {"id": None, "stop_reason": None}
        parts = []
        for event in events:
            kind = event.get("type")
            if kind == "message_start":
                message["id"] = event["message"]["id"]
            elif kind == "content_block_delta" and event["delta"]["type"] == "text_delta":
                parts.append(event["delta"]["text"])
            elif kind == "message_delta":
                message["stop_reason"] = event["delta"].get("stop_reason")
            # ping and unknown event types are ignored
        message["text"] = "".join(parts)
        return message
''')

ST_S2 = code(r'''
    import json


    def assemble(events):
        message = {"id": None, "stop_reason": None}
        blocks = {}        # index -> block being built
        json_parts = {}    # index -> partial_json strings of a tool_use block
        for event in events:
            kind = event.get("type")
            if kind == "message_start":
                message["id"] = event["message"]["id"]
            elif kind == "content_block_start":
                i = event["index"]
                blocks[i] = dict(event["content_block"])
                if blocks[i]["type"] == "tool_use":
                    json_parts[i] = []
            elif kind == "content_block_delta":
                i, delta = event["index"], event["delta"]
                if delta["type"] == "text_delta":
                    blocks[i]["text"] += delta["text"]
                elif delta["type"] == "input_json_delta":
                    json_parts[i].append(delta["partial_json"])
            elif kind == "content_block_stop":
                i = event["index"]
                if i in json_parts:          # partial JSON is only valid once complete
                    raw = "".join(json_parts.pop(i))
                    blocks[i]["input"] = json.loads(raw) if raw else {}
            elif kind == "message_delta":
                message["stop_reason"] = event["delta"].get("stop_reason")
        message["content"] = [blocks[i] for i in sorted(blocks)]
        message["text"] = "".join(b["text"] for b in message["content"] if b["type"] == "text")
        return message
''')

ST_S3 = code(r'''
    import json


    class StreamError(Exception):
        def __init__(self, type_, message=""):
            super().__init__(f"{type_}: {message}")
            self.type = type_


    def _close_block(block, json_parts):
        if block["type"] == "tool_use":
            raw = "".join(json_parts)
            try:
                block["input"] = json.loads(raw) if raw else {}
            except json.JSONDecodeError as exc:
                raise StreamError("invalid_tool_input", f"{block.get('id')}: {exc}") from exc
        return block


    def assemble(events):
        message = {"id": None, "stop_reason": None, "complete": False}
        blocks, parts, closed = {}, {}, set()
        for event in events:
            kind = event.get("type")
            if kind == "error":
                err = event.get("error", {})
                raise StreamError(err.get("type", "unknown_error"), err.get("message", ""))
            if kind == "message_start":
                message["id"] = event["message"]["id"]
            elif kind == "content_block_start":
                i = event["index"]
                blocks[i], parts[i] = dict(event["content_block"]), []
            elif kind == "content_block_delta":
                i, delta = event["index"], event["delta"]
                if i in closed:
                    continue
                if i not in blocks:                  # missed the start event
                    if delta["type"] != "text_delta":
                        continue                     # can't invent a tool's id/name
                    blocks[i], parts[i] = {"type": "text", "text": ""}, []
                block = blocks[i]
                if delta["type"] == "text_delta" and block["type"] == "text":
                    block["text"] += delta["text"]
                elif delta["type"] == "input_json_delta" and block["type"] == "tool_use":
                    parts[i].append(delta["partial_json"])
            elif kind == "content_block_stop":
                i = event["index"]
                if i in blocks and i not in closed:  # duplicate stops are no-ops
                    _close_block(blocks[i], parts[i])
                    closed.add(i)
            elif kind == "message_delta":
                message["stop_reason"] = event["delta"].get("stop_reason")
            elif kind == "message_stop":
                message["complete"] = True
        for i in blocks:                             # stream cut short: close what's open
            if i not in closed:
                _close_block(blocks[i], parts[i])
        message["content"] = [blocks[i] for i in sorted(blocks)]
        message["text"] = "".join(b["text"] for b in message["content"] if b["type"] == "text")
        return message
''')

ST_S4 = code(r'''
    import json


    class StreamError(Exception):
        def __init__(self, type_, message=""):
            super().__init__(f"{type_}: {message}")
            self.type = type_


    class StreamAssembler:
        """Push-based state machine: feed() one event at a time.
        feed() returns a block the moment it completes, else None."""

        def __init__(self, on_text=None):
            self.message = {"id": None, "stop_reason": None, "complete": False}
            self.blocks = {}       # index -> block
            self._parts = {}       # index -> partial_json strings
            self._closed = set()
            self.on_text = on_text

        def feed(self, event):
            kind = event.get("type")
            if kind == "error":
                err = event.get("error", {})
                raise StreamError(err.get("type", "unknown_error"), err.get("message", ""))
            if kind == "message_start":
                self.message["id"] = event["message"]["id"]
            elif kind == "content_block_start":
                i = event["index"]
                self.blocks[i], self._parts[i] = dict(event["content_block"]), []
            elif kind == "content_block_delta":
                self._delta(event["index"], event["delta"])
            elif kind == "content_block_stop":
                i = event["index"]
                if i in self.blocks and i not in self._closed:
                    return self._close(i)
            elif kind == "message_delta":
                self.message["stop_reason"] = event["delta"].get("stop_reason")
            elif kind == "message_stop":
                self.message["complete"] = True
            return None

        def _delta(self, i, delta):
            if i in self._closed:
                return
            if i not in self.blocks:
                if delta["type"] != "text_delta":
                    return
                self.blocks[i], self._parts[i] = {"type": "text", "text": ""}, []
            block = self.blocks[i]
            if delta["type"] == "text_delta" and block["type"] == "text":
                block["text"] += delta["text"]
                if self.on_text:
                    self.on_text(delta["text"])
            elif delta["type"] == "input_json_delta" and block["type"] == "tool_use":
                self._parts[i].append(delta["partial_json"])

        def _close(self, i):
            block = self.blocks[i]
            if block["type"] == "tool_use":
                raw = "".join(self._parts[i])
                try:
                    block["input"] = json.loads(raw) if raw else {}
                except json.JSONDecodeError as exc:
                    raise StreamError("invalid_tool_input", f"{block.get('id')}: {exc}") from exc
            self._closed.add(i)
            return block

        def finish(self):
            """Close blocks that never got a stop event; return them in index order."""
            return [self._close(i) for i in sorted(self.blocks) if i not in self._closed]

        def result(self):
            content = [self.blocks[i] for i in sorted(self.blocks)]
            text = "".join(b["text"] for b in content if b["type"] == "text")
            return {**self.message, "content": content, "text": text}


    def iter_blocks(events, on_text=None):
        asm = StreamAssembler(on_text)
        for event in events:
            block = asm.feed(event)
            if block is not None:
                yield block
        yield from asm.finish()


    def assemble(events, on_text=None):
        asm = StreamAssembler(on_text)
        for event in events:
            asm.feed(event)
        asm.finish()
        return asm.result()
''')

ST_HELPERS = code(r'''
    def start(mid="msg_1"):
        return {"type": "message_start", "message": {"id": mid, "type": "message", "role": "assistant",
                "content": [], "stop_reason": None, "usage": {"input_tokens": 12, "output_tokens": 1}}}

    def block_start(i, block):
        return {"type": "content_block_start", "index": i, "content_block": block}

    def text(i, s):
        return {"type": "content_block_delta", "index": i, "delta": {"type": "text_delta", "text": s}}

    def js(i, s):
        return {"type": "content_block_delta", "index": i, "delta": {"type": "input_json_delta", "partial_json": s}}

    def stop(i):
        return {"type": "content_block_stop", "index": i}

    def end(reason="end_turn"):
        return [{"type": "message_delta", "delta": {"stop_reason": reason, "stop_sequence": None},
                 "usage": {"output_tokens": 9}}, {"type": "message_stop"}]

    def text_stream(*pieces):
        return ([start(), block_start(0, {"type": "text", "text": ""}), {"type": "ping"}]
                + [text(0, p) for p in pieces] + [stop(0)] + end())
''')

ST_T1 = ST_HELPERS + "\n" + code(r'''
    def test_text_assembled():
        m = assemble(text_stream("Hel", "lo, ", "world"))
        assert m["text"] == "Hello, world", f"concatenate text_delta pieces: {m['text']!r}"

    def test_id_and_stop_reason():
        m = assemble(text_stream("hi"))
        assert m["id"] == "msg_1", "id comes from message_start"
        assert m["stop_reason"] == "end_turn", "stop_reason comes from message_delta"

    def test_max_tokens_stop():
        evs = text_stream("trunc")[:-2] + end("max_tokens")
        assert assemble(evs)["stop_reason"] == "max_tokens"

    def test_ignores_ping_and_unknown():
        evs = text_stream("a", "b")
        evs.insert(3, {"type": "ping"})
        evs.insert(4, {"type": "some_future_event", "data": 1})
        assert assemble(evs)["text"] == "ab", "unknown event types must be ignored"

    def test_works_with_generator():
        assert assemble(iter(text_stream("x", "y")))["text"] == "xy", "events may be any iterable"
''')

TOOL_STREAM = code(r'''
    def tool_stream():
        return [start("msg_2"),
                block_start(0, {"type": "text", "text": ""}),
                text(0, "Let me check "), text(0, "the weather."),
                stop(0),
                block_start(1, {"type": "tool_use", "id": "toolu_1", "name": "get_weather", "input": {}}),
                js(1, ""), js(1, '{"city": "Pa'), js(1, 'ris", "unit'), js(1, '": "c"}'),
                stop(1)] + end("tool_use")

    WEATHER = {"type": "tool_use", "id": "toolu_1", "name": "get_weather",
               "input": {"city": "Paris", "unit": "c"}}
''')

ST_T2 = ST_T1 + "\n" + TOOL_STREAM + "\n" + code(r'''
    def test_content_blocks():
        m = assemble(tool_stream())
        assert m["content"][0] == {"type": "text", "text": "Let me check the weather."}
        assert m["content"][1] == WEATHER, f"partial JSON joined then json.loads'd: {m['content'][1]}"
        assert m["stop_reason"] == "tool_use" and m["id"] == "msg_2"

    def test_text_is_all_text_blocks():
        m = assemble(tool_stream())
        assert m["text"] == "Let me check the weather.", "text joins only text blocks"

    def test_tool_with_no_input():
        evs = [start(), block_start(0, {"type": "tool_use", "id": "t", "name": "now", "input": {}}),
               stop(0)] + end("tool_use")
        assert assemble(evs)["content"][0]["input"] == {}, "no input_json_delta -> {}"

    def test_interleaved_indices():
        evs = [start(), block_start(0, {"type": "text", "text": ""}),
               block_start(1, {"type": "text", "text": ""}),
               text(1, "B1 "), text(0, "A1 "), text(1, "B2"), text(0, "A2"), stop(1), stop(0)] + end()
        m = assemble(evs)
        assert [b["text"] for b in m["content"]] == ["A1 A2", "B1 B2"], "route deltas by index; order by index"
''')

ST_T3 = ST_T2 + "\n" + code(r'''
    def test_error_event_raises():
        evs = text_stream("partial")[:4] + [{"type": "error",
              "error": {"type": "overloaded_error", "message": "Overloaded"}}]
        try:
            assemble(evs)
            assert False, "an error event must raise StreamError"
        except StreamError as e:
            assert e.type == "overloaded_error", f"StreamError.type should be the API error type, got {e.type!r}"

    def test_complete_flag():
        assert assemble(text_stream("hi"))["complete"] is True, "message_stop seen -> complete"
        cut = text_stream("hi", "there")[:-3]           # no stop, no message_delta/stop
        m = assemble(cut)
        assert m["complete"] is False, "stream cut short -> complete False"
        assert m["text"] == "hithere", "keep what we got"

    def test_missing_block_stop_still_parses_tool_input():
        evs = tool_stream()
        evs.remove(stop(1))
        m = assemble(evs)
        assert m["content"][1]["input"] == {"city": "Paris", "unit": "c"}, "close open blocks at the end"

    def test_delta_without_start():
        evs = [start(), text(0, "orphan "), text(0, "text"), stop(0)] + end()
        assert assemble(evs)["content"] == [{"type": "text", "text": "orphan text"}], \
            "a text_delta for an unknown index starts an implicit text block"
        evs = [start(), js(3, '{"a": 1}'), stop(3)] + end()
        assert assemble(evs)["content"] == [], "an orphan input_json_delta is ignored"

    def test_duplicate_stop_and_late_delta_ignored():
        evs = text_stream("ok")
        evs[5:5] = [stop(0), text(0, " LATE")]
        assert assemble(evs)["text"] == "ok", "deltas after a block's stop are ignored"

    def test_invalid_tool_json():
        evs = [start(), block_start(0, {"type": "tool_use", "id": "t9", "name": "x", "input": {}}),
               js(0, '{"a": '), stop(0)] + end("tool_use")
        try:
            assemble(evs)
            assert False, "broken tool JSON must not be silently accepted"
        except StreamError as e:
            assert e.type == "invalid_tool_input"
''')

ST_T4 = ST_T3 + "\n" + code(r'''
    def test_on_text_callback():
        got = []
        m = assemble(tool_stream(), on_text=got.append)
        assert got == ["Let me check ", "the weather."], f"on_text gets each text delta in order: {got}"
        assert m["content"][1] == WEATHER

    def test_iter_blocks_yields_completed_blocks():
        blocks = list(iter_blocks(tool_stream()))
        assert blocks == [{"type": "text", "text": "Let me check the weather."}, WEATHER]

    def test_iter_blocks_is_lazy():
        seen = []
        def gen():
            for e in tool_stream():
                seen.append(e["type"])
                yield e
        it = iter_blocks(gen())
        first = next(it)
        assert first["type"] == "text", "first completed block is the text block"
        assert len(seen) == 5 and seen[-1] == "content_block_stop", \
            f"yield as soon as the block stops, before reading further: consumed {len(seen)} events"
        assert next(it) == WEATHER

    def test_iter_blocks_flushes_unclosed_at_end():
        evs = [start(), block_start(0, {"type": "text", "text": ""}), text(0, "a"),
               block_start(1, {"type": "text", "text": ""}), text(1, "b"), stop(1)]
        assert [b["text"] for b in iter_blocks(evs)] == ["b", "a"], \
            "closed blocks as they stop, then unclosed ones at the end"

    def test_iter_blocks_error_raises_mid_stream():
        evs = tool_stream()[:5] + [{"type": "error", "error": {"type": "api_error", "message": "boom"}}]
        it = iter_blocks(evs)
        assert next(it)["text"] == "Let me check the weather."
        try:
            next(it)
            assert False, "the error event must surface from the generator"
        except StreamError as e:
            assert e.type == "api_error"
''')

STREAM = {
    "id": "fde-ch-stream-assembler", "type": "challenge", "stage": "coding", "difficulty": 3,
    "tags": ["streaming", "claude api", "tool use", "json", "generators", "state machine", "progressive"],
    "pattern": "event-driven state machine keyed by block index",
    "title": "Claude streaming assembler (4 levels)",
    "summary": "Rebuild a full Messages API response from server-sent events: text deltas, multiple content blocks including tool_use with partial JSON, robustness to cut-off or out-of-order streams and error events, then incremental callbacks and a generator of completed blocks.",
    "talkPrompts": [
        "Each event has a type; I'll dispatch on it and ignore types I don't know so new event types don't break us.",
        "Content blocks are keyed by index, so I store them in a dict and sort at the end - interleaving is free.",
        "input_json_delta fragments aren't valid JSON on their own; I buffer strings and json.loads once at block stop.",
        "If the stream is cut, I keep what arrived and mark it incomplete rather than throwing it away.",
        "For the generator I'll turn the loop into a feed(event) state machine so the batch and streaming APIs share one code path.",
    ],
    "steps": [
        {
            "title": "Level 1: assemble text",
            "minutes": 6,
            "prompt": code(r'''
                `events` is an iterable of dicts shaped like Claude's streaming API:

                ```
                {"type": "message_start", "message": {"id": "msg_1", ...}}
                {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}
                {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "Hel"}}
                {"type": "content_block_stop", "index": 0}
                {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {...}}
                {"type": "message_stop"}
                ```

                `assemble(events) -> {"id", "text", "stop_reason"}`. Ignore `ping` and unknown types.
            '''),
            "starter": code(r'''
                def assemble(events):
                    pass
            '''),
            "tests": ST_T1,
            "hints": [
                "Loop once over the events and branch on `event['type']`.",
                "Grab the id from `event['message']['id']`, collect `delta['text']` for `text_delta`s, and `stop_reason` from `message_delta`'s delta.",
                "Append text pieces to a list and `''.join(parts)` at the end (repeated `+=` on strings is quadratic in the worst case).",
            ],
            "solution": ST_S1,
            "lesson": "Stream processing = one pass, dispatch on event type, accumulate into state, finalize at the end. Use `.get('type')` and an implicit 'else: ignore' so the client is forward-compatible with new event types.",
            "alternative": "A dispatch dict `{'message_start': on_start, ...}` mapping types to handler functions scales better as event types grow; an if/elif chain is clearer at this size.",
        },
        {
            "title": "Level 2: content blocks and tool_use",
            "minutes": 10,
            "prompt": code(r'''
                Responses can have several content blocks, by `index`. A tool call looks like:

                ```
                content_block_start index=1 {"type": "tool_use", "id": "toolu_1", "name": "get_weather", "input": {}}
                content_block_delta index=1 {"type": "input_json_delta", "partial_json": "{\"city\": \"Pa"}
                content_block_delta index=1 {"type": "input_json_delta", "partial_json": "ris\"}"}
                content_block_stop  index=1
                ```

                Return `{"id", "stop_reason", "text", "content"}`: `content` lists blocks in index order; tool blocks get `input = json.loads(joined partial_json)` (`{}` if empty) at their stop. `text` joins all text blocks.
            '''),
            "tests": ST_T2,
            "hints": [
                "Keep a dict `index -> block`; start it from a copy of `content_block`.",
                "Text deltas append to `blocks[i]['text']`; JSON deltas append to a separate `json_parts[i]` list - don't parse until the block stops.",
                "On `content_block_stop`: `raw = ''.join(json_parts.pop(i)); blocks[i]['input'] = json.loads(raw) if raw else {}`. At the end: `[blocks[i] for i in sorted(blocks)]`.",
            ],
            "solution": ST_S2,
            "lesson": "Key concurrent sub-streams by their id (here `index`) so interleaved events route themselves. Partial JSON is only parseable once complete: buffer strings, parse at the boundary event.",
            "alternative": "Use an incremental JSON parser to show tool arguments as they stream (what UIs do for 'typing' tool calls). Much more complex; only worth it if the user must see arguments before the block ends.",
        },
        {
            "title": "Level 3: robustness and errors",
            "minutes": 12,
            "prompt": code(r'''
                Make `assemble` survive real networks. Define `class StreamError(Exception)` with a `.type` attribute, and:

                - `{"type": "error", "error": {"type": "overloaded_error", "message": ...}}` -> raise `StreamError` with `.type == "overloaded_error"`.
                - Add `"complete": True` only if `message_stop` was seen (else `False`); still return what arrived.
                - Blocks with no `content_block_stop` are closed at the end (tool JSON parsed).
                - A `text_delta` for an index with no start creates a text block; other orphan deltas are ignored.
                - Duplicate stops and deltas after a block's stop are ignored.
                - Invalid tool JSON -> `StreamError` with `.type == "invalid_tool_input"`.
            '''),
            "tests": ST_T3,
            "hints": [
                "Track which indices are closed in a set; a block's 'close' logic (parse JSON) should live in one helper you can call from the stop event AND from the end of the loop.",
                "Check `error` first and raise. For an unknown index, create `{'type': 'text', 'text': ''}` only for `text_delta`; `continue` otherwise.",
                "Wrap `json.loads` in `try/except json.JSONDecodeError` and `raise StreamError('invalid_tool_input', ...) from exc`; after the loop close every index not in `closed`.",
            ],
            "solution": ST_S3,
            "lesson": "Decide a policy for each failure mode explicitly: fail loudly on things that would cause wrong actions (an error event, a malformed tool call you might execute), degrade gracefully on lost framing (missing stop -> close at end, flag incomplete). Put 'finalize a block' in one function so every path finalizes the same way.",
            "alternative": "Treat any protocol violation as fatal (raise on orphan deltas, missing stops). Simpler and safer for tool execution, but a flaky proxy that drops one event would lose the whole response; a retry at the request level could compensate.",
        },
        {
            "title": "Level 4: incremental callbacks and a block generator",
            "minutes": 12,
            "prompt": code(r'''
                Consumers want results while the stream is still arriving:

                - `assemble(events, on_text=None)` - call `on_text(piece)` for every text delta, in order. Same return value as level 3.
                - `iter_blocks(events, on_text=None)` - a **generator** that yields each block **as soon as its `content_block_stop` arrives** (without reading further events), then any unclosed blocks at the end in index order. Error events raise from the generator.

                ```python
                for block in iter_blocks(stream):
                    if block["type"] == "tool_use":
                        run_tool(block)   # start before the stream ends
                ```
            '''),
            "tests": ST_T4,
            "hints": [
                "Both functions need the same state machine. Can you turn the loop body into a method that handles one event?",
                "Make a `StreamAssembler` class with `feed(event)` that returns the finished block on `content_block_stop` (else None), `finish()` that closes leftovers, and `result()`.",
                "`iter_blocks`: `for e in events: b = asm.feed(e); if b is not None: yield b` then `yield from asm.finish()`. `assemble` feeds everything, calls `finish()`, returns `result()`.",
            ],
            "solution": ST_S4,
            "lesson": "Invert a pull loop into a push-based state machine (`feed(event)`): batch, callback and generator APIs then become three-line wrappers over one tested core. Generators give backpressure for free - nothing is read until the consumer asks.",
            "alternative": "Make `iter_blocks` an `async def` generator over an async event source (what the Anthropic SDK exposes with `async for`). Same state machine; only the wrapper changes.",
        },
    ],
}

ITEMS = [KV, DEDUP, LOGS, RETRY, STREAM]
