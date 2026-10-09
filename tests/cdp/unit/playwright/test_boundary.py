"""The compat layer must only use pydoll's public API.

Reaching into private names of core objects would couple the layer to
implementation details; everything it needs is exposed publicly (query_script,
execute_command, iframe_context, target_id, events).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[3] / 'pydoll' / 'playwright'
CORE_NAMES = {'tab', 'chrome', 'element', 'root', 'owner', 'iframe', 'handler'}


def _modules() -> list[Path]:
    return sorted(PACKAGE.rglob('*.py'))


@pytest.mark.parametrize('module', _modules(), ids=lambda path: path.name)
def test_no_private_pydoll_attributes(module: Path) -> None:
    tree = ast.parse(module.read_text(encoding='utf-8'))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute) or not node.attr.startswith('_') or node.attr.startswith('__'):
            continue
        base = node.value
        if isinstance(base, ast.Name) and base.id in CORE_NAMES:
            offenders.append(f'{base.id}.{node.attr} (line {node.lineno})')
        if isinstance(base, ast.Attribute) and base.attr in {'_tab', '_chrome', '_root', '_element'}:
            offenders.append(f'{base.attr}.{node.attr} (line {node.lineno})')
    assert offenders == [], f'{module.name} touches private pydoll members: {offenders}'


@pytest.mark.parametrize('module', _modules(), ids=lambda path: path.name)
def test_no_private_module_imports(module: Path) -> None:
    tree = ast.parse(module.read_text(encoding='utf-8'))
    banned = {'pydoll.connection', 'pydoll.browser.managers'}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not any(node.module.startswith(name) for name in banned), (
                f'{module.name} imports internal module {node.module}'
            )
