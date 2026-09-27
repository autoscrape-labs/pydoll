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
the implementation's names, so annotations need no translation; the only
rewrite is of module-level aliases of an implementation class (such as
``KeyboardAPI = Keyboard``), which are spelled with the facade's name so the
facade advertises facade types.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import inspect
import re
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

HANDLER_PARAMS = {'callback', 'handler', 'listener', 'f'}
PREDICATE_PARAMS = {'predicate', 'url_or_predicate'}
ASYNC_CALLBACK_MARKERS = ('Awaitable', 'Coroutine')
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
DOCSTRING_REWRITES = (
    ('asyncio.run(main())', 'main()'),
    ('async_playwright', 'sync_playwright'),
    ('async with ', 'with '),
    ('async for ', 'for '),
    ('async def ', 'def '),
    ('await ', ''),
)


@dataclass
class Target:
    """One generated module."""

    output: Path
    module_docstring: str
    classes: list[tuple[str, str]]
    constructible: set[str]
    extra_header: str = ''
    extra_footer: str = ''


TARGETS = [
    Target(
        output=ROOT / 'pydoll' / 'sync' / '_generated.py',
        module_docstring='Synchronous facades over pydoll (generated, do not edit).',
        classes=[
            ('pydoll.browser.chromium.chrome', 'Chrome'),
            ('pydoll.browser.chromium.edge', 'Edge'),
            ('pydoll.browser.tab', 'Tab'),
            ('pydoll.browser.tab', 'DownloadHandle'),
            ('pydoll.browser.tab', 'RequestHandle'),
            ('pydoll.browser.tab', 'ResponseHandle'),
            ('pydoll.elements.web_element', 'WebElement'),
            ('pydoll.elements.shadow_root', 'ShadowRoot'),
            ('pydoll.interactions.keyboard', 'Keyboard'),
            ('pydoll.interactions.mouse', 'Mouse'),
            ('pydoll.interactions.scroll', 'Scroll'),
            ('pydoll.browser.requests.request', 'Request'),
            ('pydoll.browser.requests.response', 'Response'),
        ],
        constructible={'Chrome', 'Edge'},
    ),
    Target(
        output=ROOT / 'pydoll' / 'playwright' / 'sync_api' / '_generated.py',
        module_docstring='Synchronous Playwright-compatible API (generated, do not edit).',
        classes=[
            ('pydoll.playwright._playwright', 'Playwright'),
            ('pydoll.playwright._playwright', 'BrowserType'),
            ('pydoll.playwright._playwright', 'Selectors'),
            ('pydoll.playwright._playwright', 'PlaywrightContextManager'),
            ('pydoll.playwright._browser', 'Browser'),
            ('pydoll.playwright._browser_context', 'BrowserContext'),
            ('pydoll.playwright._page', 'Page'),
            ('pydoll.playwright._frame', 'Frame'),
            ('pydoll.playwright._locator', 'Locator'),
            ('pydoll.playwright._locator', 'FrameLocator'),
            ('pydoll.playwright._element_handle', 'JSHandle'),
            ('pydoll.playwright._element_handle', 'ElementHandle'),
            ('pydoll.playwright._input', 'Keyboard'),
            ('pydoll.playwright._input', 'Mouse'),
            ('pydoll.playwright._input', 'Touchscreen'),
            ('pydoll.playwright._network', 'Request'),
            ('pydoll.playwright._network', 'Response'),
            ('pydoll.playwright._network', 'Route'),
            ('pydoll.playwright._network', 'APIResponse'),
            ('pydoll.playwright._dialog', 'Dialog'),
            ('pydoll.playwright._dialog', 'ConsoleMessage'),
            ('pydoll.playwright._dialog', 'FileChooser'),
            ('pydoll.playwright._dialog', 'Download'),
            ('pydoll.playwright._events', 'EventInfo'),
        ],
        constructible=set(),
        extra_footer=textwrap.dedent(
            '''
            def sync_playwright() -> PlaywrightContextManager:
                """``with sync_playwright() as p:`` entry point."""
                from pydoll.playwright._playwright import async_playwright  # noqa: PLC0415

                return PlaywrightContextManager(async_playwright())
            '''
        ),
    ),
]


@dataclass
class Method:
    name: str
    node: ast.FunctionDef | ast.AsyncFunctionDef
    is_async: bool
    kind: str
    owner: str
    overloads: list[ast.FunctionDef | ast.AsyncFunctionDef] = field(default_factory=list)
    setter: ast.FunctionDef | None = None


@dataclass
class Naming:
    """How annotation names are spelled in one generated module.

    ``aliases`` maps a module-level alias of an implementation class (such as
    ``KeyboardAPI``) to the facade name the generated module defines.
    """

    facade_names: set[str]
    aliases: dict[str, str]

    def rewrite(self, text: str) -> str:
        for alias, facade_name in self.aliases.items():
            text = re.sub(rf'\b{alias}\b', facade_name, text)
        return text


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


def _pydoll_bases(cls: type) -> list[type]:
    return [
        base for base in cls.__mro__ if base is not object and base.__module__.startswith('pydoll')
    ]


def _takes_async_callback(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Whether a signature types one of its handler parameters as returning an awaitable."""
    arguments = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
    for argument in arguments:
        if argument.arg not in HANDLER_PARAMS or argument.annotation is None:
            continue
        annotation = ast.unparse(argument.annotation)
        if any(marker in annotation for marker in ASYNC_CALLBACK_MARKERS):
            return True
    return False


def _collect_methods(cls: type) -> list[Method]:
    """Public methods of ``cls`` and its pydoll bases, subclass definitions winning."""
    methods: dict[str, Method] = {}
    for base in _pydoll_bases(cls):
        overloads: dict[str, list[ast.FunctionDef | ast.AsyncFunctionDef]] = {}
        for node in _class_node(base).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                'overload' in _decorator_names(node)
            ):
                if not _takes_async_callback(node):
                    overloads.setdefault(node.name, []).append(node)
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
                name,
                node,
                isinstance(node, ast.AsyncFunctionDef),
                kind,
                base.__name__,
                overloads.get(name, []) if kind == 'method' else [],
            )
        for node in _class_node(base).body:
            if isinstance(node, ast.FunctionDef) and 'setter' in _decorator_names(node):
                getter = methods.get(node.name)
                if getter is not None and getter.kind == 'property' and getter.setter is None:
                    getter.setter = node
    return list(methods.values())


def _class_attributes(cls: type) -> list[str]:
    """Public names assigned in the class body of ``cls`` or its pydoll bases."""
    found: list[str] = []
    for base in _pydoll_bases(cls):
        for node in _class_node(base).body:
            target: ast.expr | None = None
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                target = node.target
            if (
                isinstance(target, ast.Name)
                and not target.id.startswith('_')
                and target.id not in found
                and hasattr(base, target.id)
            ):
                found.append(target.id)
    return found


def _instance_attributes(cls: type, known: set[str]) -> list[tuple[str, str]]:
    """Public ``self.name = ...`` assignments in ``__init__`` across pydoll bases."""
    found: dict[str, str] = {}
    for base in _pydoll_bases(cls):
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


def _aenter_node(cls: type) -> ast.AsyncFunctionDef | None:
    for base in _pydoll_bases(cls):
        for node in _class_node(base).body:
            if isinstance(node, ast.AsyncFunctionDef) and node.name == '__aenter__':
                return node
    return None


def _enter_annotation(cls: type, facade_name: str, naming: Naming) -> str:
    """The facade type ``__enter__`` returns, derived from ``__aenter__``.

    An implementation that returns itself (annotated with its own name, a base
    class or ``Self``) enters as the facade; anything else keeps the annotation.
    """
    node = _aenter_node(cls)
    if node is None or node.returns is None:
        return facade_name
    text = naming.rewrite(_annotation_text(node.returns))
    own_names = {base.__name__ for base in cls.__mro__}
    if text == 'Self' or (text in own_names and text not in naming.facade_names):
        return facade_name
    return text


def _annotation_text(node: ast.expr) -> str:
    text = ast.unparse(node)
    if text.startswith("'") or text.startswith('"'):
        text = text.strip('\'"')
    return text


def _signature_text(node: ast.FunctionDef | ast.AsyncFunctionDef, naming: Naming) -> str:
    return naming.rewrite(ast.unparse(node.args))


def _call_args(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Forward every parameter to the implementation, wrapping callbacks."""
    args = node.args
    parts: list[str] = []
    positional = [*args.posonlyargs, *args.args]
    for index, argument in enumerate(positional):
        if index == 0 and argument.arg in {'self', 'cls'}:
            continue
        value = _wrap(argument.arg)
        by_position = argument in args.posonlyargs or args.vararg is not None
        parts.append(value if by_position else f'{argument.arg}={value}')
    if args.vararg:
        parts.append(_wrap_varargs(args.vararg.arg))
    for argument in args.kwonlyargs:
        parts.append(f'{argument.arg}={_wrap(argument.arg)}')
    if args.kwarg:
        parts.append(_wrap_kwargs(args.kwarg.arg))
    return ', '.join(parts)


def _wrap(name: str) -> str:
    if name in HANDLER_PARAMS:
        return f'mapping.wrap_handler({name})'
    if name in PREDICATE_PARAMS:
        return f'mapping.wrap_predicate({name})'
    return f'mapping.to_impl({name})'


def _wrap_varargs(name: str) -> str:
    return f'*[mapping.to_impl(positional) for positional in {name}]'


def _wrap_kwargs(name: str) -> str:
    return f'**{{kwarg: mapping.to_impl(kwarg_value) for kwarg, kwarg_value in {name}.items()}}'


def _returns(node: ast.FunctionDef | ast.AsyncFunctionDef, method: Method, naming: Naming) -> str:
    if node.returns is None:
        return ''
    returns = node.returns
    if method.kind == 'asynccontextmanager':
        inner = returns
        if (
            isinstance(returns, ast.Subscript)
            and isinstance(returns.value, ast.Name)
            and returns.value.id in {'AsyncGenerator', 'AsyncIterator'}
        ):
            inner = returns.slice.elts[0] if isinstance(returns.slice, ast.Tuple) else returns.slice
        return f' -> AbstractContextManager[{naming.rewrite(_annotation_text(inner))}]'
    return f' -> {naming.rewrite(_annotation_text(returns))}'


def _docstring(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> str:
    doc = ast.get_docstring(node, clean=False)
    if not doc:
        return ''
    for old, new in DOCSTRING_REWRITES:
        doc = doc.replace(old, new)
    return '"""' + doc.replace('\\', '\\\\') + '"""'


def _emit_method(method: Method, facade_name: str, naming: Naming) -> str:
    node = method.node
    typed_node = method.overloads[0] if len(method.overloads) == 1 else node
    signature = _signature_text(typed_node, naming)
    returns = _returns(typed_node, method, naming)
    doc = _docstring(node)
    lines: list[str] = []
    body_doc = f'        {doc}\n' if doc else ''
    receiver = "cast('Any', self._impl)" if method.overloads else 'self._impl'
    call = f'{receiver}.{method.name}({_call_args(node)})'
    if method.kind == 'property':
        lines.append('    @property')
        lines.append(f'    def {method.name}(self){returns}:')
        lines.append(body_doc.rstrip('\n') if doc else '')
        expression = f'self._impl.{method.name}'
        if method.is_async:
            expression = f'self._run({expression})'
        lines.append(f'        return mapping.from_impl({expression})')
        if method.setter is not None:
            setter_args = method.setter.args.args
            value = setter_args[1].arg if len(setter_args) > 1 else 'value'
            annotation = (
                naming.rewrite(ast.unparse(setter_args[1].annotation))
                if len(setter_args) > 1 and setter_args[1].annotation is not None
                else 'Any'
            )
            lines.append('')
            lines.append(_emit_setter(method.name, value, annotation))
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
        for overload_node in method.overloads if len(method.overloads) > 1 else []:
            lines.append('    @overload')
            lines.append(
                f'    def {method.name}({_signature_text(overload_node, naming)})'
                f'{_returns(overload_node, method, naming)}: ...'
            )
        lines.append(f'    def {method.name}({signature}){returns}:')
        lines.append(body_doc.rstrip('\n') if doc else '')
        expression = f'self._run({call})' if method.is_async else call
        if returns == ' -> None':
            lines.append(f'        {expression}')
        else:
            lines.append(f'        return mapping.from_impl({expression})')
    return '\n'.join(line for line in lines if line) + '\n'


def _emit_setter(name: str, value: str, annotation: str) -> str:
    return (
        f'    @{name}.setter\n'
        f'    def {name}(self, {value}: {annotation}) -> None:\n'
        f'        self._impl.{name} = mapping.to_impl({value})'
    )


def _return_line(expression: str) -> str:
    return f'        return mapping.from_impl({expression})'


def _call_args_static(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = node.args
    parts = [
        f'{argument.arg}={_wrap(argument.arg)}' for argument in [*args.posonlyargs, *args.args]
    ]
    if args.vararg:
        parts.append(_wrap_varargs(args.vararg.arg))
    parts.extend(f'{argument.arg}={_wrap(argument.arg)}' for argument in args.kwonlyargs)
    if args.kwarg:
        parts.append(_wrap_kwargs(args.kwarg.arg))
    return ', '.join(parts)


def _emit_init(cls: type, facade_name: str, naming: Naming) -> str:
    node = None
    for base in _pydoll_bases(cls):
        for candidate in _class_node(base).body:
            if isinstance(candidate, ast.FunctionDef) and candidate.name == '__init__':
                node = candidate
                break
        if node is not None:
            break
    if node is None:
        return ''
    signature = _signature_text(node, naming)
    doc = _docstring(node)
    lines = [f'    def __init__({signature}) -> None:']
    if doc:
        lines.append(f'        {doc}')
    lines.append(f'        super().__init__(_{facade_name}Impl({_call_args(node)}))')
    return '\n'.join(lines) + '\n'


def _emit_class(module_name: str, class_name: str, target: Target, naming: Naming) -> str:
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    facade_name = class_name
    node = _class_node(cls)
    doc = _docstring(node)
    type_params = _generic_parameters(node)
    bases = 'SyncBase' if not type_params else f'SyncBase, Generic[{", ".join(type_params)}]'
    lines = [f'class {facade_name}({bases}):']
    if doc:
        lines.append(f'    {doc}')
    lines.append(f'    _impl: _{facade_name}Impl')
    methods = _collect_methods(cls)
    method_names = {method.name for method in methods}
    for attribute in _class_attributes(cls):
        if attribute not in method_names:
            lines.append(f'    {attribute} = _{facade_name}Impl.{attribute}')
    lines.append('')
    if class_name in target.constructible:
        lines.append(_emit_init(cls, facade_name, naming))
    if _aenter_node(cls) is not None:
        lines.append(
            f'    def __enter__(self) -> {_enter_annotation(cls, facade_name, naming)}:\n'
            '        return mapping.from_impl(self._run(self._impl.__aenter__()))\n'
        )
        lines.append(
            '    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> Any:\n'
            '        return self._run(self._impl.__aexit__(exc_type, exc, tb))\n'
        )
    for attribute, annotation in _instance_attributes(cls, naming.facade_names):
        if attribute in method_names:
            continue
        lines.append(
            f'    @property\n'
            f'    def {attribute}(self) -> {annotation}:\n'
            f'        return mapping.from_impl(self._impl.{attribute})\n\n'
            + _emit_setter(attribute, 'value', annotation)
            + '\n'
        )
    for method in methods:
        lines.append(_emit_method(method, facade_name, naming))
    return '\n'.join(lines).rstrip() + '\n'


def _import_line(module_name: str, class_name: str) -> str:
    return f'from {module_name} import {class_name} as _{class_name}Impl'


def _generic_parameters(node: ast.ClassDef) -> list[str]:
    """Type variable names of a ``Generic[...]`` base, so the facade stays generic too.

    The type variables themselves are copied from the source module by
    ``_type_checking_imports``, so they exist at module level before the class.
    """
    for base in node.bases:
        if (
            isinstance(base, ast.Subscript)
            and isinstance(base.value, ast.Name)
            and base.value.id == 'Generic'
        ):
            inner = base.slice
            elements = inner.elts if isinstance(inner, ast.Tuple) else [inner]
            return [ast.unparse(element) for element in elements]
    return []


def _source_modules(target: Target) -> list[str]:
    """Modules of every generated class and of their pydoll base classes."""
    names: list[str] = []
    for module_name, class_name in target.classes:
        cls = getattr(importlib.import_module(module_name), class_name)
        for base in _pydoll_bases(cls):
            if base.__module__ not in names:
                names.append(base.__module__)
    return names


def _naming(target: Target) -> Naming:
    """Facade names plus every alias a source module gives an implementation class."""
    implementations = {
        getattr(importlib.import_module(module_name), class_name): class_name
        for module_name, class_name in target.classes
    }
    aliases: dict[str, str] = {}
    for module_name in _source_modules(target):
        for name, value in vars(importlib.import_module(module_name)).items():
            if name.startswith('_') or not isinstance(value, type):
                continue
            facade_name = implementations.get(value)
            if facade_name is not None and name != facade_name:
                aliases[name] = facade_name
    return Naming(facade_names=set(implementations.values()), aliases=aliases)


def _type_checking_imports(target: Target, naming: Naming) -> list[str]:
    """Import statements and module-level type definitions the annotations rely on.

    Every source module (including base-class modules) contributes its imports,
    top-level and ``TYPE_CHECKING``-only alike, because defaults and annotations
    are copied verbatim. Names that a generated facade defines, and aliases of
    an implementation class (rewritten to the facade name), are dropped from
    the imports so the facade wins.
    """
    hidden = naming.facade_names | set(naming.aliases)
    seen: list[str] = []
    for module_name in _source_modules(target):
        module = importlib.import_module(module_name)
        tree = ast.parse(inspect.getsource(module))
        nodes: list[ast.stmt] = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                nodes.append(node)
            elif isinstance(node, ast.If) and _is_type_checking(node.test):
                nodes.extend(
                    child for child in node.body if isinstance(child, (ast.Import, ast.ImportFrom))
                )
            elif _is_type_definition(node):
                nodes.append(node)
            elif isinstance(node, ast.ClassDef) and node.name not in hidden:
                if (module_name, node.name) not in target.classes:
                    nodes.append(
                        ast.ImportFrom(
                            module=module_name, names=[ast.alias(name=node.name)], level=0
                        )
                    )
        for node in nodes:
            if isinstance(node, ast.ImportFrom):
                node.names = [
                    alias for alias in node.names if (alias.asname or alias.name) not in hidden
                ]
                if not node.names:
                    continue
            text = ast.unparse(node)
            if 'from __future__' in text or text in seen:
                continue
            seen.append(text)
    return seen


def _is_type_definition(node: ast.stmt) -> bool:
    """``T = TypeVar(...)`` and ``Name: TypeAlias = ...`` statements."""
    if isinstance(node, ast.AnnAssign) and isinstance(node.annotation, ast.Name):
        return node.annotation.id == 'TypeAlias'
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
        func = node.value.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, 'attr', '')
        return name == 'TypeVar'
    return False


def _is_type_checking(test: ast.expr) -> bool:
    return (isinstance(test, ast.Name) and test.id == 'TYPE_CHECKING') or (
        isinstance(test, ast.Attribute) and test.attr == 'TYPE_CHECKING'
    )


def render(target: Target) -> str:
    naming = _naming(target)
    imports: list[str] = []
    bodies: list[str] = []
    registrations: list[str] = []
    for module_name, class_name in target.classes:
        imports.append(_import_line(module_name, class_name))
        bodies.append(_emit_class(module_name, class_name, target, naming))
        registrations.append(f'mapping.register(_{class_name}Impl, {class_name})')
    header = textwrap.dedent(
        f'''\
        """{target.module_docstring}

        Regenerate with ``python scripts/generate_sync_api.py``.
        """

        # ruff: noqa
        # fmt: off
        from __future__ import annotations

        from contextlib import AbstractContextManager
        from typing import Any, Generic, cast, overload

        from pydoll.sync._runtime import SyncBase, mapping, run_sync
        '''
    )
    source_imports = '\n'.join(_type_checking_imports(target, naming))
    parts = [header, '\n'.join(imports), '', source_imports, '', target.extra_header]
    parts.extend(bodies)
    parts.append('\n'.join(registrations))
    parts.append(target.extra_footer)
    parts.append(
        '__all__ = ['
        + ', '.join(f"'{name}'" for _, name in target.classes)
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
