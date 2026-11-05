"""Test harness shared by the app (Pyodide, in a Web Worker) and the
content validator (CPython). Keep it dependency-free.

run_tests(user_code, test_code) -> dict
    Executes the learner's code, then the hidden tests in the same namespace.
    Every top-level function named test_* is a test. Tests may be `async def`.

run_code(code) -> dict
    Executes code and returns captured stdout (used by predict-the-output).
"""
import asyncio
import contextlib
import inspect
import io
import traceback

USER_FILE = "<your code>"
TEST_FILE = "<tests>"


def _short_tb(exc):
    """Traceback limited to frames from the learner's code and the tests."""
    frames = [f for f in traceback.extract_tb(exc.__traceback__)
              if f.filename in (USER_FILE, TEST_FILE)]
    lines = [f'  {f.filename}, line {f.lineno}' + (f": {f.line}" if f.line else "")
             for f in frames[-4:]]
    msg = f"{type(exc).__name__}: {exc}".rstrip(": ")
    return "\n".join(lines + [msg]) if lines else msg


def _exec(code, filename, ns, out):
    compiled = compile(code, filename, "exec")
    # linecache lets tracebacks show the offending source line
    import linecache
    linecache.cache[filename] = (len(code), None, code.splitlines(True), filename)
    with contextlib.redirect_stdout(out):
        exec(compiled, ns)


async def _call(fn, out):
    with contextlib.redirect_stdout(out):
        result = fn()
        if inspect.isawaitable(result):
            await result


async def run_tests(user_code, test_code):
    out = io.StringIO()
    ns = {"__name__": "__solution__"}
    report = {"ok": False, "error": None, "stdout": "", "tests": []}
    try:
        _exec(user_code, USER_FILE, ns, out)
    except SyntaxError as e:
        report["error"] = f"SyntaxError on line {e.lineno}: {e.msg}"
        if e.text:
            report["error"] += f"\n    {e.text.rstrip()}"
        return report
    except BaseException as e:  # noqa: BLE001 - we report everything
        report["error"] = _short_tb(e)
        report["stdout"] = out.getvalue()[-4000:]
        return report
    ns["captured_output"] = out.getvalue()
    try:
        _exec(test_code, TEST_FILE, ns, io.StringIO())
    except BaseException as e:  # noqa: BLE001
        report["error"] = "Test setup failed: " + _short_tb(e)
        return report
    tests = [(k, v) for k, v in ns.items()
             if k.startswith("test_") and callable(v)]
    for name, fn in tests:
        try:
            await _call(fn, out)
            report["tests"].append({"name": name, "passed": True, "message": ""})
        except AssertionError as e:
            report["tests"].append({"name": name, "passed": False,
                                    "message": str(e) or _short_tb(e)})
        except BaseException as e:  # noqa: BLE001
            report["tests"].append({"name": name, "passed": False,
                                    "message": _short_tb(e)})
    report["stdout"] = out.getvalue()[-4000:]
    report["ok"] = bool(tests) and all(t["passed"] for t in report["tests"])
    return report


async def run_code(code):
    out = io.StringIO()
    ns = {"__name__": "__main__"}
    try:
        _exec(code, USER_FILE, ns, out)
        return {"ok": True, "stdout": out.getvalue(), "error": None}
    except BaseException as e:  # noqa: BLE001
        return {"ok": False, "stdout": out.getvalue(), "error": _short_tb(e)}


def run_sync(coro):
    """CPython helper used by the validator."""
    return asyncio.run(coro)
