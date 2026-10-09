"""Injected JavaScript engine shared by every Playwright-compatible object.

The engine source (``engine.js``) is a single expression that evaluates to an
object exposing the selector resolver, element-state checks and DOM actions.
Each frame evaluates it once inside an isolated world and keeps the resulting
object; later calls receive that object as their first argument, so the page's
main world never sees the engine, its globals or its prototype lookups.
"""

from __future__ import annotations

import json
from functools import cache
from importlib import resources


@cache
def engine_source() -> str:
    """Return the engine expression source, read once from package data."""
    return resources.files(__package__).joinpath('engine.js').read_text(encoding='utf-8')


def engine_call(body: str) -> str:
    """Build a function declaration ``function(engine, a0..a5)`` around ``body``.

    ``engine`` is the evaluated engine object passed as the first call argument,
    ``a0``.. are the remaining call arguments and ``this`` is the call target.
    """
    return f'function(engine, a0, a1, a2, a3, a4, a5) {{\n{body}\n}}'


def inline_engine_call(body: str) -> str:
    """Like ``engine_call`` but evaluates the engine inline (tests and one-off use)."""
    return f'function(a0, a1, a2, a3, a4, a5) {{\nconst engine = {engine_source()};\n{body}\n}}'


def js_string(value: str) -> str:
    """Encode a Python string as a JavaScript string literal."""
    return json.dumps(value, ensure_ascii=False)
