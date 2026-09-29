"""The generated sync facades must match what the generator produces today.

If this fails, run ``python scripts/generate_sync_api.py`` and commit the result.
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import inspect
import re
import sys
import typing
from pathlib import Path

import pytest

from pydoll.interactions.keyboard import Keyboard as KeyboardImpl
from pydoll.playwright import sync_api
from pydoll.sync import Chrome, Keyboard, Mouse, Scroll, Tab

ROOT = Path(__file__).resolve().parents[3]


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        'generate_sync_api', ROOT / 'scripts' / 'generate_sync_api.py'
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules['generate_sync_api'] = module
    spec.loader.exec_module(module)
    return module


def _facade_module(target):
    name = '.'.join(target.output.relative_to(ROOT).with_suffix('').parts)
    return importlib.import_module(name)


TARGET_IDS = ['pydoll.sync', 'pydoll.playwright.sync_api']


@pytest.mark.parametrize('index', [0, 1], ids=TARGET_IDS)
def test_generated_module_is_current(index: int) -> None:
    generator = _load_generator()
    target = generator.TARGETS[index]
    assert target.output.read_text(encoding='utf-8') == generator.render(target), (
        f'{target.output.relative_to(ROOT)} is stale; run scripts/generate_sync_api.py'
    )


@pytest.mark.parametrize('index', [0, 1], ids=TARGET_IDS)
def test_generated_facades_cover_every_public_member(index: int) -> None:
    generator = _load_generator()
    target = generator.TARGETS[index]
    facades = _facade_module(target)
    for module_name, class_name in target.classes:
        impl = getattr(importlib.import_module(module_name), class_name)
        facade = getattr(facades, class_name)
        missing = [
            name
            for name in dir(impl)
            if not name.startswith('_') and not hasattr(facade, name)
        ]
        assert missing == [], f'{facade.__name__} lacks {missing}'


def test_sync_methods_are_plain_functions() -> None:
    assert not inspect.iscoroutinefunction(Tab.go_to)
    assert inspect.signature(Tab.go_to).parameters['timeout'].default == 300
    assert not isinstance(inspect.getattr_static(Tab, 'title'), property)
    assert isinstance(inspect.getattr_static(Tab, 'keyboard'), property)


def test_facade_properties_advertise_facade_types_not_implementation_aliases() -> None:
    generator = _load_generator()
    source = generator.TARGETS[0].output.read_text(encoding='utf-8')
    assert '    def keyboard(self) -> Keyboard:' in source
    assert '    def mouse(self) -> Mouse:' in source
    assert '    def scroll(self) -> Scroll:' in source
    assert re.search(r'->[^:\n]*\b(KeyboardAPI|MouseAPI|ScrollAPI)\b', source) is None
    module = sys.modules[Tab.__module__]
    for name, facade in (('keyboard', Keyboard), ('mouse', Mouse), ('scroll', Scroll)):
        getter = inspect.getattr_static(Tab, name).fget
        assert typing.get_type_hints(getter, vars(module))['return'] is facade


@pytest.mark.parametrize('index', [0, 1], ids=TARGET_IDS)
def test_sync_facades_do_not_advertise_async_callbacks(index: int) -> None:
    generator = _load_generator()
    tree = ast.parse(generator.TARGETS[index].output.read_text(encoding='utf-8'))
    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for argument in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]:
            if argument.arg not in generator.HANDLER_PARAMS or argument.annotation is None:
                continue
            annotation = ast.unparse(argument.annotation)
            if any(marker in annotation for marker in generator.ASYNC_CALLBACK_MARKERS):
                offenders.append(f'{node.name}({argument.arg}: {annotation})')
    assert offenders == []


def test_on_keeps_a_typed_signature_when_only_the_sync_overload_remains() -> None:
    parameters = inspect.signature(Tab.on).parameters
    assert parameters['event_name'].annotation == 'str'
    assert parameters['callback'].annotation == 'Callable[[dict], Any]'
    assert inspect.signature(Tab.on).return_annotation == 'int'


def test_enter_returns_what_aenter_returns() -> None:
    generator = _load_generator()
    sync_source = generator.TARGETS[0].output.read_text(encoding='utf-8')
    playwright_source = generator.TARGETS[1].output.read_text(encoding='utf-8')
    assert '    def __enter__(self) -> Chrome:' in sync_source
    assert '    def __enter__(self) -> Edge:' in sync_source
    assert '    def __enter__(self) -> Playwright:' in playwright_source
    assert '-> PlaywrightContextManager:' not in playwright_source.split('def sync_playwright')[0]
    enter = inspect.getattr_static(sync_api.PlaywrightContextManager, '__enter__')
    assert inspect.signature(enter).return_annotation == 'Playwright'


def test_class_level_constants_are_exposed_on_the_facade() -> None:
    assert Keyboard.PAUSE_CHARS is KeyboardImpl.PAUSE_CHARS


def test_instance_attributes_have_setters() -> None:
    options = inspect.getattr_static(Chrome, 'options')
    assert isinstance(options, property) and options.fset is not None
    chromium = inspect.getattr_static(sync_api.Playwright, 'chromium')
    assert isinstance(chromium, property) and chromium.fset is not None


def test_context_manager_yield_types_with_commas_survive() -> None:
    generator = _load_generator()
    node = ast.parse(
        'async def pair(self) -> AsyncGenerator[tuple[Foo, Bar], None]: ...'
    ).body[0]
    method = generator.Method('pair', node, True, 'asynccontextmanager', 'Owner')
    naming = generator.Naming(facade_names=set(), aliases={})
    assert generator._returns(node, method, naming) == ' -> AbstractContextManager[tuple[Foo, Bar]]'
    iterator_node = ast.parse('async def one(self) -> AsyncIterator[Foo]: ...').body[0]
    assert (
        generator._returns(iterator_node, method, naming) == ' -> AbstractContextManager[Foo]'
    )


def test_copied_docstrings_read_synchronously() -> None:
    generator = _load_generator()
    source = '\n'.join([
        'async def go(self):',
        '    """Navigate.',
        '',
        '    Example::',
        '',
        '        async def main():',
        '            async with async_playwright() as p:',
        '                await tab.go_to(url)',
        '                async for item in tab.items():',
        '                    pass',
        '',
        '        asyncio.run(main())',
        '    """',
    ])
    node = ast.parse(source).body[0]
    doc = generator._docstring(node)
    assert 'await ' not in doc
    assert 'async ' not in doc
    assert 'def main():' in doc
    assert 'with sync_playwright() as p:' in doc
    assert 'tab.go_to(url)' in doc
    assert 'for item in tab.items():' in doc
    assert doc.rstrip('"').rstrip().endswith('main()')
    for target in generator.TARGETS:
        generated = target.output.read_text(encoding='utf-8')
        assert 'await ' not in generated
        assert 'async with ' not in generated
        assert 'async for ' not in generated
        assert 'asyncio.run(' not in generated


def test_variadic_arguments_are_unwrapped_before_reaching_the_implementation() -> None:
    generator = _load_generator()
    sync_source = generator.TARGETS[0].output.read_text(encoding='utf-8')
    playwright_source = generator.TARGETS[1].output.read_text(encoding='utf-8')
    assert (
        '**{kwarg: mapping.to_impl(kwarg_value) for kwarg, kwarg_value in attributes.items()}'
        in sync_source
    )
    assert '*[mapping.to_impl(positional) for positional in args]' in playwright_source
    raw_forwarding = [
        line.strip()
        for line in (sync_source + playwright_source).splitlines()
        if ('._impl.' in line or 'Impl.' in line) and re.search(r'\*\*?\w+\)', line)
    ]
    assert raw_forwarding == []
