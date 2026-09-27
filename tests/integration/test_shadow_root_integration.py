"""Integration tests for Shadow DOM support (open, closed, nested)."""

from pathlib import Path

import pytest

from pydoll.elements.shadow_root import ShadowRoot
from pydoll.elements.web_element import WebElement
from pydoll.exceptions import ShadowRootNotFound
from pydoll.protocol.dom.types import ShadowRootType

TEST_PAGE = f'file://{(Path(__file__).parent / "pages" / "shadow_dom_test.html").absolute()}'


class TestOpenShadowRoot:
    """Tests for open shadow root access and element finding."""

    @pytest.mark.asyncio
    async def test_get_shadow_root_open(self, tab):
        await tab.go_to(TEST_PAGE)

        host = await tab.find(id='open-host', timeout=5)
        shadow = await host.get_shadow_root()

        assert isinstance(shadow, ShadowRoot)
        assert shadow.mode == ShadowRootType.OPEN
        assert shadow.host_element is host

    @pytest.mark.asyncio
    async def test_find_elements_in_open_shadow(self, tab):
        await tab.go_to(TEST_PAGE)

        host = await tab.find(id='open-host', timeout=5)
        shadow = await host.get_shadow_root()

        text_el = await shadow.query('.open-text')
        assert isinstance(text_el, WebElement)
        text = await text_el.text()
        assert text == 'Open shadow content'

        btn = await shadow.query('#open-btn')
        assert btn is not None

    @pytest.mark.asyncio
    async def test_query_in_open_shadow(self, tab):
        await tab.go_to(TEST_PAGE)

        host = await tab.find(id='open-host', timeout=5)
        shadow = await host.get_shadow_root()

        input_el = await shadow.query('input[type="email"]')
        assert input_el is not None

    @pytest.mark.asyncio
    async def test_find_all_in_open_shadow(self, tab):
        await tab.go_to(TEST_PAGE)

        host = await tab.find(id='open-host', timeout=5)
        shadow = await host.get_shadow_root()

        buttons = await shadow.query('.shadow-btn', find_all=True)
        assert len(buttons) == 1

    @pytest.mark.asyncio
    async def test_inner_html_open(self, tab):
        await tab.go_to(TEST_PAGE)

        host = await tab.find(id='open-host', timeout=5)
        shadow = await host.get_shadow_root()

        html = await shadow.inner_html()
        assert 'Open shadow content' in html


class TestClosedShadowRoot:
    """Tests for closed shadow root access via CDP bypass."""

    @pytest.mark.asyncio
    async def test_get_shadow_root_closed(self, tab):
        await tab.go_to(TEST_PAGE)

        host = await tab.find(id='closed-host', timeout=5)
        shadow = await host.get_shadow_root()

        assert isinstance(shadow, ShadowRoot)
        assert shadow.mode == ShadowRootType.CLOSED

    @pytest.mark.asyncio
    async def test_find_elements_in_closed_shadow(self, tab):
        await tab.go_to(TEST_PAGE)

        host = await tab.find(id='closed-host', timeout=5)
        shadow = await host.get_shadow_root()

        text_el = await shadow.query('.closed-text')
        assert isinstance(text_el, WebElement)
        text = await text_el.text()
        assert text == 'Closed shadow content'

    @pytest.mark.asyncio
    async def test_query_in_closed_shadow(self, tab):
        await tab.go_to(TEST_PAGE)

        host = await tab.find(id='closed-host', timeout=5)
        shadow = await host.get_shadow_root()

        btn = await shadow.query('#closed-btn')
        assert btn is not None

        input_el = await shadow.query('input[type="password"]')
        assert input_el is not None

    @pytest.mark.asyncio
    async def test_inner_html_closed(self, tab):
        await tab.go_to(TEST_PAGE)

        host = await tab.find(id='closed-host', timeout=5)
        shadow = await host.get_shadow_root()

        html = await shadow.inner_html()
        assert 'Closed shadow content' in html


class TestNestedShadowRoots:
    """Tests for nested shadow roots (open -> closed)."""

    @pytest.mark.asyncio
    async def test_nested_open_then_closed(self, tab):
        await tab.go_to(TEST_PAGE)

        nested_host = await tab.find(id='nested-host', timeout=5)
        outer_shadow = await nested_host.get_shadow_root()
        assert outer_shadow.mode == ShadowRootType.OPEN

        outer_text = await outer_shadow.query('.outer-text')
        text = await outer_text.text()
        assert text == 'Outer shadow'

        inner_host = await outer_shadow.query('#inner-host')
        inner_shadow = await inner_host.get_shadow_root()
        assert inner_shadow.mode == ShadowRootType.CLOSED

        inner_text = await inner_shadow.query('.inner-text')
        text = await inner_text.text()
        assert text == 'Inner closed shadow'

        deep_btn = await inner_shadow.query('#deep-btn')
        assert deep_btn is not None


class TestShadowRootNotPresent:
    """Tests for elements without shadow roots."""

    @pytest.mark.asyncio
    async def test_no_shadow_root_raises(self, tab):
        await tab.go_to(TEST_PAGE)

        h1 = await tab.find(tag_name='h1', timeout=5)
        with pytest.raises(ShadowRootNotFound):
            await h1.get_shadow_root()


class TestHumanizedInputInShadowDom:
    @pytest.mark.asyncio
    async def test_humanized_click_reaches_a_button_inside_a_shadow_root(self, tab):
        await tab.go_to(TEST_PAGE)
        await tab.execute_script(
            'window.__moves = 0; document.addEventListener("mousemove", () => { window.__moves++; });'
            'window.__clicks = 0; document.getElementById("open-host").shadowRoot'
            '.getElementById("open-btn").addEventListener("click", () => { window.__clicks++; })'
        )
        host = await tab.find(id='open-host')
        shadow = await host.get_shadow_root()
        button = await shadow.query('#open-btn')

        assert button._input_mouse() is tab.mouse
        await button.click(humanize=True)

        counts = await tab.execute_script(
            'return [window.__moves, window.__clicks]', return_by_value=True
        )
        moves, clicks = counts['result']['result']['value']
        assert moves > 2
        assert clicks == 1
