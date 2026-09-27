"""The generated sync facades must match what the generator produces today.

If this fails, run ``python scripts/generate_sync_api.py`` and commit the result.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def _load_generator():
    spec = importlib.util.spec_from_file_location('generate_sync_api', ROOT / 'scripts' / 'generate_sync_api.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules['generate_sync_api'] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('index', range(1), ids=['pydoll.sync'])
def test_generated_module_is_current(index: int) -> None:
    generator = _load_generator()
    target = generator.TARGETS[index]
    assert target.output.read_text(encoding='utf-8') == generator.render(target), (
        f'{target.output.relative_to(ROOT)} is stale; run scripts/generate_sync_api.py'
    )


def test_generated_facades_cover_async_methods() -> None:
    from pydoll.browser.tab import Tab
    from pydoll.elements.web_element import WebElement
    from pydoll.sync import Tab as SyncTab
    from pydoll.sync import WebElement as SyncWebElement

    for impl, facade in ((Tab, SyncTab), (WebElement, SyncWebElement)):
        missing = [
            name
            for name in dir(impl)
            if not name.startswith('_') and callable(getattr(impl, name, None)) and not hasattr(facade, name)
        ]
        assert missing == [], f'{facade.__name__} lacks {missing}'


def test_sync_methods_are_plain_functions() -> None:
    import inspect

    from pydoll.sync import Tab

    assert not inspect.iscoroutinefunction(Tab.go_to)
    assert inspect.signature(Tab.go_to).parameters['timeout'].default == 300
    assert isinstance(inspect.getattr_static(Tab, 'title'), property)
