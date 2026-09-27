"""(De)serialization of ``evaluate`` arguments and results.

Arguments travel as one JSON tree in which handles are replaced by
``{"__pydoll_handle__": index}`` markers, followed by one CDP call argument per
handle. ``REBUILD_SOURCE`` restores the original structure in the page.
Results come back by value; the few values JSON cannot carry (NaN, Infinity,
-0, undefined) arrive as ``unserializableValue`` and are mapped back here.
"""

from __future__ import annotations

import datetime
import math
import re
from typing import Any, Pattern

from pydoll.playwright._element_handle import JSHandle, PrimitiveHandle
from pydoll.protocol.runtime.types import CallArgument

HANDLE_KEY = '__pydoll_handle__'
VALUE_KEY = '__pydoll_value__'
DATE_KEY = '__pydoll_date__'
REGEX_KEY = '__pydoll_regex__'

REBUILD_SOURCE = """
function(tree, handles) {
  const visit = value => {
    if (value === null || typeof value !== 'object')
      return value;
    if (Array.isArray(value))
      return value.map(visit);
    const keys = Object.keys(value);
    if (keys.length === 1) {
      if (keys[0] === '__pydoll_handle__')
        return handles[value.__pydoll_handle__];
      if (keys[0] === '__pydoll_value__') {
        const v = value.__pydoll_value__;
        if (v === 'undefined') return undefined;
        if (v === 'NaN') return NaN;
        if (v === 'Infinity') return Infinity;
        if (v === '-Infinity') return -Infinity;
        if (v === '-0') return -0;
      }
      if (keys[0] === '__pydoll_date__')
        return new Date(value.__pydoll_date__);
      if (keys[0] === '__pydoll_regex__')
        return new RegExp(value.__pydoll_regex__[0], value.__pydoll_regex__[1]);
    }
    const result = {};
    for (const key of keys)
      result[key] = visit(value[key]);
    return result;
  };
  return visit(tree);
}
"""

SAFE_RETURN_SOURCE = """
function(value) {
  const seen = new Set();
  const visit = (v, depth) => {
    if (v === null || v === undefined) return v;
    const t = typeof v;
    if (t === 'string' || t === 'boolean' || t === 'number') return v;
    if (t === 'bigint') return Number(v);
    if (t !== 'object') return undefined;
    if (depth > 100 || seen.has(v)) return undefined;
    if (v instanceof Date) return v.toISOString();
    if (v instanceof RegExp) return v.toString();
    if (v instanceof Error) return { name: v.name, message: v.message, stack: v.stack };
    if (v instanceof Map) v = Object.fromEntries(v);
    if (v instanceof Set) v = Array.from(v);
    if (ArrayBuffer.isView(v)) v = Array.from(v);
    const tag = Object.prototype.toString.call(v);
    if (tag === '[object Window]' || tag === '[object global]') return undefined;
    if (typeof v.nodeType === 'number' && typeof v.nodeName === 'string') return undefined;
    seen.add(v);
    try {
      if (Array.isArray(v)) return v.map(item => visit(item, depth + 1));
      if (typeof v.toJSON === 'function') return visit(v.toJSON(), depth + 1);
      const result = {};
      for (const key of Object.keys(v)) {
        let item;
        try { item = v[key]; } catch (e) { continue; }
        result[key] = visit(item, depth + 1);
      }
      return result;
    } catch (e) {
      return undefined;
    } finally {
      seen.delete(v);
    }
  };
  return visit(value, 0);
}
"""

_EVALUATE_TEMPLATE = """
function(tree, ...handles) {
  const rebuild = %s;
  const safeReturn = %s;
  const arg = rebuild(tree, handles);
  let result = (
%s
  );
  if (typeof result === 'function')
    result = result(%s);
  if (result && typeof result.then === 'function')
    return result.then(safeReturn);
  return safeReturn(result);
}
"""

_IDENTITY_SOURCE = 'function(value) { return value; }'


def evaluate_source(
    expression: str, *, with_this: bool = False, by_value: bool = True, all_elements: bool = False
) -> str:
    """Function declaration that evaluates ``expression`` without touching ``eval``.

    The expression text is embedded in the declaration itself, so the page's
    ``window.eval`` is never consulted and cannot observe the source. A function
    expression is called with the arguments, anything else is returned as is.
    """
    if all_elements:
        call = 'elements, arg'
    elif with_this:
        call = 'this, arg'
    else:
        call = 'arg'
    return _EVALUATE_TEMPLATE % (
        REBUILD_SOURCE,
        SAFE_RETURN_SOURCE if by_value else _IDENTITY_SOURCE,
        normalize_expression(expression),
        call,
    )


def normalize_expression(expression: str) -> str:
    """Wrap function declarations in parentheses so ``eval`` yields the function."""
    expression = expression.strip()
    if re.match(r'^(async)?\s*function(\s|\()', expression):
        expression = f'({expression})'
    return expression


def serialize_argument(arg: Any) -> tuple[Any, list[JSHandle]]:
    """Return the JSON tree for ``arg`` and the handles it references, in order."""
    handles: list[JSHandle] = []
    tree = _serialize(arg, handles, set())
    return tree, handles


def call_arguments(arg: Any) -> list[CallArgument]:
    """Build the CDP call arguments (argument tree, then handles) for an evaluation."""
    tree, handles = serialize_argument(arg)
    arguments: list[CallArgument] = [{'value': tree}]
    arguments.extend({'objectId': handle.object_id} for handle in handles)
    return arguments


def _serialize(value: Any, handles: list[JSHandle], visited: set[int]) -> Any:
    if isinstance(value, PrimitiveHandle):
        return _serialize(value._value, handles, visited)
    if isinstance(value, JSHandle):
        handles.append(value)
        return {HANDLE_KEY: len(handles) - 1}
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if math.isnan(value):
            return {VALUE_KEY: 'NaN'}
        if math.isinf(value):
            return {VALUE_KEY: 'Infinity' if value > 0 else '-Infinity'}
        if value == 0 and math.copysign(1, value) < 0:
            return {VALUE_KEY: '-0'}
        return value
    if isinstance(value, datetime.datetime):
        aware = value if value.tzinfo else value.replace(tzinfo=datetime.timezone.utc)
        return {
            DATE_KEY: aware.astimezone(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
        }
    if isinstance(value, Pattern):
        flags = ''
        if value.flags & re.IGNORECASE:
            flags += 'i'
        if value.flags & re.MULTILINE:
            flags += 'm'
        if value.flags & re.DOTALL:
            flags += 's'
        return {REGEX_KEY: [value.pattern, flags]}
    if id(value) in visited:
        raise ValueError('Cannot serialize a circular structure as an evaluate argument')
    if isinstance(value, (list, tuple, set, frozenset)):
        visited.add(id(value))
        result = [_serialize(item, handles, visited) for item in value]
        visited.discard(id(value))
        return result
    if isinstance(value, dict):
        visited.add(id(value))
        result_dict = {str(key): _serialize(item, handles, visited) for key, item in value.items()}
        visited.discard(id(value))
        return result_dict
    return {VALUE_KEY: 'undefined'}
