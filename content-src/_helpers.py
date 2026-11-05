"""Helpers for authoring pack content in Python (code is easier to write here
than inside JSON strings). tools/build_packs.py turns these into packs/*.json."""
import textwrap


def code(s: str) -> str:
    """Dedent a triple-quoted block and normalise to end with one newline."""
    return textwrap.dedent(s).strip("\n") + "\n"


def lines(s: str) -> list[str]:
    """Parsons helper: dedented source -> list of lines (indentation kept)."""
    return code(s).rstrip("\n").split("\n")
