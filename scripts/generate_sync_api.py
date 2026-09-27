"""Generate the synchronous facades from the asynchronous implementation classes.

Usage::

    python scripts/generate_sync_api.py          # rewrite the generated modules
    python scripts/generate_sync_api.py --check  # exit 1 when they are stale

The generator reads each implementation class with ``ast`` (so defaults and
annotations are reproduced exactly as written), walks its pydoll base classes,
and emits one facade per class: every ``async def`` becomes a blocking method
that runs the coroutine on the shared loop, properties and plain methods are
forwarded, async context managers become ``with`` blocks, and callback
parameters are wrapped so user code runs on the dispatch thread. Facades keep
the implementation's names, so annotations need no translation.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import inspect
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

HANDLER_PARAMS = {'callback', 'handler', 'listener', 'f'}
PREDICATE_PARAMS = {'predicate', 'url_or_predicate'}
SKIPPED_METHODS = {
    '__init__',
    '__repr__',
    '__str__',
    '__eq__',
    '__hash__',
    '__getattr__',
    '__aenter__',
    '__aexit__',
}


@dataclass
class Target:
    """One generated module."""

    output: Path
    module_docstring: str
    classes: list[tuple[str, str]]
    constructible: set[str]
    extra_header: str = ''
    extra_footer: str = ''
    renames: dict[str, str] = field(default_factory=dict)


TARGETS = [
    Target(
        output=ROOT / 'pydoll' / 'sync' / '_generated.py',
        module_docstring='Synchronous facades over pydoll (generated, do not edit).',
        classes=[
            ('pydoll.browser.chromium.chrome', 'Chrome'),
            ('pydoll.browser.chromium.edge', 'Edge'),
            ('pydoll.browser.tab', 'Tab'),
            ('pydoll.browser.tab', '_DownloadHandle'),
            ('pydoll.elements.web_element', 'WebElement'),
            ('pydoll.elements.shadow_root', 'ShadowRoot'),
            ('pydoll.interactions.keyboard', 'Keyboard'),
            ('pydoll.interactions.mouse', 'Mouse'),
            ('pydoll.interactions.scroll', 'Scroll'),
            ('pydoll.browser.requests.request', 'Request'),
            ('pydoll.browser.requests.response', 'Response'),
        ],
        constructible={'Chrome', 'Edge'},
        renames={'_DownloadHandle': 'DownloadHandle'},
    ),
]


@dataclass
class Method:
    name: str
    node: ast.FunctionDef | ast.AsyncFunctionDef
    is_async: bool
    kind: str
    owner: str


def _decorator_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    names = []
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name):
            names.append(decorator.id)
        elif isinstance(decorator, ast.Attribute):
            names.append(decorator.attr)
        elif isinstance(decorator, ast.Call):
            names.append(_decorator_names_call(decorator))
    return names


def _decorator_names_call(call: ast.Call) -> str:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return ''


def _class_node(cls: type) -> ast.ClassDef:
    source = textwrap.dedent(inspect.getsource(cls))
    module = ast.parse(source)
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == cls.__name__:
            return node
    raise RuntimeError(f'Class {cls.__name__} not found in its source')


def _collect_methods(cls: type) -> list[Method]:
    """Public methods of ``cls`` and its pydoll bases, subclass definitions winning."""
    methods: dict[str, Method] = {}
    for base in cls.__mro__:
        if base is object or not base.__module__.startswith('pydoll'):
            continue
        for node in _class_node(base).body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            decorators = _decorator_names(node)
            if 'overload' in decorators:
                continue
            name = node.name
            if name.startswith('_') and name not in {'__enter__', '__exit__'}:
                continue
            if name in SKIPPED_METHODS or name in methods:
                continue
            if 'property' in decorators:
                kind = 'property'
            elif 'setter' in decorators:
                kind = 'setter'
            elif 'staticmethod' in decorators:
                kind = 'static'
            elif 'classmethod' in decorators:
                kind = 'classmethod'
            elif 'asynccontextmanager' in decorators:
                kind = 'asynccontextmanager'
            else:
                kind = 'method'
            methods[name] = Method(
                name, node, isinstance(node, ast.AsyncFunctionDef), kind, base.__name__
            )
        for node in _class_node(base).body:
            if isinstance(node, ast.FunctionDef) and 'setter' in _decorator_names(node):
                key = f'{node.name}.setter'
                if key not in methods:
                    methods[key] = Method(node.name, node, False, 'setter', base.__name__)
    return list(methods.values())


def _instance_attributes(cls: type, known: set[str]) -> list[tuple[str, str]]:
    """Public ``self.name = ...`` assignments in ``__init__`` across pydoll bases."""
    found: dict[str, str] = {}
    for base in cls.__mro__:
        if base is object or not base.__module__.startswith('pydoll'):
            continue
        for node in _class_node(base).body:
            if not isinstance(node, ast.FunctionDef) or node.name != '__init__':
                continue
            for statement in ast.walk(node):
                target = None
                annotation = 'Any'
                if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
                    target = statement.targets[0]
                    if isinstance(statement.value, ast.Call) and isinstance(
                        statement.value.func, ast.Name
                    ):
                        annotation = (
                            statement.value.func.id if statement.value.func.id in known else 'Any'
                        )
                elif isinstance(statement, ast.AnnAssign):
                    target = statement.target
                    annotation = ast.unparse(statement.annotation)
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == 'self'
                    and not target.attr.startswith('_')
                    and target.attr not in found
                ):
                    found[target.attr] = annotation
    return list(found.items())


def _has_aenter(cls: type) -> bool:
    return any('__aenter__' in vars(base) for base in cls.__mro__)


def _signature_text(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    return ast.unparse(node.args)


def _call_args(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Forward every parameter to the implementation, wrapping callbacks."""
    args = node.args
    parts: list[str] = []
    positional = [*args.posonlyargs, *args.args]
    for index, argument in enumerate(positional):
        if index == 0 and argument.arg in {'self', 'cls'}:
            continue
        value = _wrap(argument.arg)
        parts.append(value if argument in args.posonlyargs else f'{argument.arg}={value}')
    if args.vararg:
        parts.append(f'*{args.vararg.arg}')
    for argument in args.kwonlyargs:
        parts.append(f'{argument.arg}={_wrap(argument.arg)}')
    if args.kwarg:
        parts.append(f'**{args.kwarg.arg}')
    return ', '.join(parts)


def _wrap(name: str) -> str:
    if name in HANDLER_PARAMS:
        return f'mapping.wrap_handler({name})'
    if name in PREDICATE_PARAMS:
        return f'mapping.wrap_predicate({name})'
    return f'mapping.to_impl({name})'


def _returns(node: ast.FunctionDef | ast.AsyncFunctionDef, method: Method) -> str:
    if node.returns is None:
        return ''
    text = ast.unparse(node.returns)
    if method.kind == 'asynccontextmanager':
        inner = text
        if text.startswith('AsyncGenerator[') or text.startswith('AsyncIterator['):
            inner = text[text.index('[') + 1 :].rsplit(']', 1)[0].split(',')[0].strip()
        return f' -> AbstractContextManager[{inner}]'
    if text.startswith("'") or text.startswith('"'):
        text = text.strip('\'"')
    return f' -> {text}'


def _docstring(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> str:
    doc = ast.get_docstring(node, clean=False)
    if not doc:
        return ''
    return '"""' + doc.replace('\\', '\\\\') + '"""'


def _emit_method(method: Method, facade_name: str) -> str:
    node = method.node
    signature = _signature_text(node)
    returns = _returns(node, method)
    doc = _docstring(node)
    lines: list[str] = []
    body_doc = f'        {doc}\n' if doc else ''
    call = f'self._impl.{method.name}({_call_args(node)})'
    if method.kind == 'property':
        lines.append('    @property')
        lines.append(f'    def {method.name}(self){returns}:')
        lines.append(body_doc.rstrip('\n') if doc else '')
        expression = f'self._impl.{method.name}'
        if method.is_async:
            expression = f'self._run({expression})'
        lines.append(f'        return mapping.from_impl({expression})')
    elif method.kind == 'setter':
        value = node.args.args[1].arg if len(node.args.args) > 1 else 'value'
        lines.append(f'    @{method.name}.setter')
        lines.append(f'    def {method.name}(self, {value}: Any) -> None:')
        lines.append(f'        self._impl.{method.name} = mapping.to_impl({value})')
    elif method.kind == 'asynccontextmanager':
        lines.append(f'    def {method.name}({signature}){returns}:')
        lines.append(body_doc.rstrip('\n') if doc else '')
        lines.append(f'        return mapping.from_impl({call})')
    elif method.kind == 'static':
        lines.append('    @staticmethod')
        lines.append(f'    def {method.name}({signature}){returns}:')
        lines.append(body_doc.rstrip('\n') if doc else '')
        impl_call = f'_{facade_name}Impl.{method.name}({_call_args_static(node)})'
        lines.append(_return_line(f'self._run({impl_call})' if method.is_async else impl_call))
    elif method.kind == 'classmethod':
        lines.append('    @classmethod')
        lines.append(f'    def {method.name}({signature}){returns}:')
        lines.append(body_doc.rstrip('\n') if doc else '')
        impl_call = f'_{facade_name}Impl.{method.name}({_call_args(node)})'
        lines.append(_return_line(f'run_sync({impl_call})' if method.is_async else impl_call))
    else:
        lines.append(f'    def {method.name}({signature}){returns}:')
        lines.append(body_doc.rstrip('\n') if doc else '')
        expression = f'self._run({call})' if method.is_async else call
        lines.append(f'        return mapping.from_impl({expression})')
    return '\n'.join(line for line in lines if line) + '\n'


def _return_line(expression: str) -> str:
    return f'        return mapping.from_impl({expression})'


def _call_args_static(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = node.args
    parts = [
        f'{argument.arg}={_wrap(argument.arg)}' for argument in [*args.posonlyargs, *args.args]
    ]
    if args.vararg:
        parts.append(f'*{args.vararg.arg}')
    parts.extend(f'{argument.arg}={_wrap(argument.arg)}' for argument in args.kwonlyargs)
    if args.kwarg:
        parts.append(f'**{args.kwarg.arg}')
    return ', '.join(parts)


def _emit_init(cls: type, facade_name: str) -> str:
    node = None
    for base in cls.__mro__:
        if base is object or not base.__module__.startswith('pydoll'):
            continue
        for candidate in _class_node(base).body:
            if isinstance(candidate, ast.FunctionDef) and candidate.name == '__init__':
                node = candidate
                break
        if node is not None:
            break
    if node is None:
        return ''
    signature = _signature_text(node)
    doc = _docstring(node)
    lines = [f'    def __init__({signature}) -> None:']
    if doc:
        lines.append(f'        {doc}')
    lines.append(f'        super().__init__(_{facade_name}Impl({_call_args(node)}))')
    return '\n'.join(lines) + '\n'


def _emit_class(module_name: str, class_name: str, target: Target) -> tuple[str, str]:
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    facade_name = target.renames.get(class_name, class_name)
    node = _class_node(cls)
    doc = _docstring(node)
    lines = [f'class {facade_name}(SyncBase):']
    if doc:
        lines.append(f'    {doc}')
    lines.append(f'    _impl: _{facade_name}Impl')
    lines.append('')
    if class_name in target.constructible:
        lines.append(_emit_init(cls, facade_name))
    if _has_aenter(cls):
        lines.append(
            f'    def __enter__(self) -> {facade_name}:\n'
            '        return mapping.from_impl(self._run(self._impl.__aenter__()))\n'
        )
        lines.append(
            '    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> Any:\n'
            '        return self._run(self._impl.__aexit__(exc_type, exc, tb))\n'
        )
    methods = _collect_methods(cls)
    method_names = {method.name for method in methods}
    known = {target.renames.get(name, name) for _, name in target.classes}
    for attribute, annotation in _instance_attributes(cls, known):
        if attribute in method_names:
            continue
        lines.append(
            f'    @property\n'
            f'    def {attribute}(self) -> {annotation}:\n'
            f'        return mapping.from_impl(self._impl.{attribute})\n'
        )
    for method in methods:
        lines.append(_emit_method(method, facade_name))
    body = '\n'.join(lines).rstrip() + '\n'
    import_line = f'from {module_name} import {class_name} as _{facade_name}Impl'
    return import_line, body


def _type_checking_imports(target: Target) -> list[str]:
    """Copy the import statements of every source module (defaults and annotations need them)."""
    seen: list[str] = []
    for module_name, _ in target.classes:
        module = importlib.import_module(module_name)
        source = inspect.getsource(module)
        tree = ast.parse(source)
        nodes: list[ast.stmt] = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                nodes.append(node)
            elif isinstance(node, ast.If) and _is_type_checking(node.test):
                nodes.extend(
                    child for child in node.body if isinstance(child, (ast.Import, ast.ImportFrom))
                )
        for node in nodes:
            text = ast.unparse(node)
            if 'from __future__' in text or text in seen:
                continue
            seen.append(text)
    return seen


def _is_type_checking(test: ast.expr) -> bool:
    return (isinstance(test, ast.Name) and test.id == 'TYPE_CHECKING') or (
        isinstance(test, ast.Attribute) and test.attr == 'TYPE_CHECKING'
    )


def render(target: Target) -> str:
    imports: list[str] = []
    bodies: list[str] = []
    registrations: list[str] = []
    for module_name, class_name in target.classes:
        import_line, body = _emit_class(module_name, class_name, target)
        facade_name = target.renames.get(class_name, class_name)
        imports.append(import_line)
        bodies.append(body)
        registrations.append(f'mapping.register(_{facade_name}Impl, {facade_name})')
    header = textwrap.dedent(
        f'''\
        """{target.module_docstring}

        Regenerate with ``python scripts/generate_sync_api.py``.
        """

        # ruff: noqa
        # fmt: off
        from __future__ import annotations

        from contextlib import AbstractContextManager
        from typing import Any

        from pydoll.sync._runtime import SyncBase, mapping, run_sync
        '''
    )
    source_imports = '\n'.join(_type_checking_imports(target))
    parts = [header, '\n'.join(imports), '', source_imports, '', target.extra_header]
    parts.extend(bodies)
    parts.append('\n'.join(registrations))
    parts.append(target.extra_footer)
    parts.append(
        '__all__ = ['
        + ', '.join(f"'{target.renames.get(name, name)}'" for _, name in target.classes)
        + (", 'sync_playwright'" if 'sync_playwright' in target.extra_footer else '')
        + ']\n'
    )
    return '\n\n'.join(part.rstrip('\n') for part in parts if part is not None) + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--check', action='store_true', help='fail when the generated files are stale'
    )
    options = parser.parse_args()
    stale = []
    for target in TARGETS:
        content = render(target)
        if options.check:
            if not target.output.exists() or target.output.read_text(encoding='utf-8') != content:
                stale.append(target.output)
            continue
        target.output.parent.mkdir(parents=True, exist_ok=True)
        target.output.write_text(content, encoding='utf-8')
        print(f'wrote {target.output.relative_to(ROOT)}')
    if stale:
        for path in stale:
            print(f'stale: {path.relative_to(ROOT)} (run scripts/generate_sync_api.py)')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
