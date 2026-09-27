"""Integration tests for the injected selector/actionability engine in real Chrome.

The engine is exercised through the public ``query_script``/``execute_script``
primitives, exactly as the Locator layer drives it.
"""

from __future__ import annotations

import pytest

from pydoll.exceptions import ScriptException
from pydoll.playwright._injected import inline_engine_call as engine_call

QUERY_ALL = engine_call('return engine.querySelectorAll(a0, this);')
STATE = engine_call('return engine.elementState(this, a0);')
CHECK_STATES = engine_call('return engine.checkStates(this, a0);')
HIT_TARGET = engine_call('return engine.hitCheck(a0, this);')
ROLE = engine_call('return engine.ariaRole(this);')
NAME = engine_call('return engine.accessibleName(this, false);')


async def ids(root, selector: str) -> list:
    elements = await root.query_script(QUERY_ALL, arguments=[{'value': selector}])
    return [element.get_attribute('id') or element.get_attribute('data-testid') for element in elements]


async def value_of(element, script: str, *args, await_promise: bool = False):
    response = await element.execute_script(
        script,
        arguments=[{'value': arg} for arg in args],
        return_by_value=True,
        await_promise=await_promise,
    )
    details = response['result'].get('exceptionDetails')
    if details:
        raise ScriptException(details.get('exception', {}).get('description', details.get('text', '')))
    return response['result']['result'].get('value')


class TestSelectorEngines:
    @pytest.mark.asyncio
    async def test_css_xpath_and_id_engines(self, engine_tab):
        assert await ids(engine_tab, '#list li') == ['item', 'item', 'item']
        assert await ids(engine_tab, 'css=#p-hello') == ['p-hello']
        assert await ids(engine_tab, 'xpath=//p[@id="p-hello"]') == ['p-hello']
        assert await ids(engine_tab, '//h2') == ['h2-features']
        assert await ids(engine_tab, 'id=title') == ['title']

    @pytest.mark.asyncio
    async def test_css_pierces_shadow_dom(self, engine_tab):
        assert await ids(engine_tab, '#shadow-btn') == ['shadow-btn']
        assert await ids(engine_tab, 'internal:testid=[data-testid="shadow-item"s]') == ['shadow-btn']

    @pytest.mark.asyncio
    async def test_text_engine_lax_matches_substring_case_insensitive(self, engine_tab):
        assert await ids(engine_tab, 'text=hello world') == ['p-hello', 'p-hello-again']
        assert await ids(engine_tab, 'internal:text="hello"i') == ['p-hello', 'p-hello-again']

    @pytest.mark.asyncio
    async def test_text_engine_strict_matches_normalized_full_text(self, engine_tab):
        assert await ids(engine_tab, 'internal:text="Hello World"s') == ['p-hello']
        assert await ids(engine_tab, 'internal:text="Hello"s') == []
        assert await ids(engine_tab, 'text="Hello World"') == ['p-hello']

    @pytest.mark.asyncio
    async def test_text_engine_regex_and_button_values(self, engine_tab):
        assert await ids(engine_tab, 'internal:text=/^hello\\s+world$/i') == ['p-hello']
        assert await ids(engine_tab, 'internal:text="Send now"s') == ['input-submit']

    @pytest.mark.asyncio
    async def test_text_engine_prefers_deepest_matching_element(self, engine_tab):
        assert await ids(engine_tab, 'internal:text="inner text"i') == ['inner-span']
        assert await ids(engine_tab, 'internal:text="Deep content"i') == ['deep-div']

    @pytest.mark.asyncio
    async def test_chaining_nth_has_text_and_has(self, engine_tab):
        assert await ids(engine_tab, '#list li >> nth=1') == ['item']
        assert await ids(engine_tab, '.card >> internal:has-text="Card B"i') == ['card-2']
        assert await ids(engine_tab, '.card >> internal:has-not-text="Card B"i') == ['card-1', 'card-3']
        assert await ids(engine_tab, '.card >> internal:has="button"') == ['card-1', 'card-3']
        assert await ids(engine_tab, '.card >> internal:has-not="button"') == ['card-2']
        assert await ids(engine_tab, '.card >> nth=-1') == ['card-3']

    @pytest.mark.asyncio
    async def test_and_or_and_chain(self, engine_tab):
        assert await ids(engine_tab, '.card >> internal:and="#card-3"') == ['card-3']
        assert await ids(engine_tab, '#card-1 >> internal:or="#card-3"') == ['card-1', 'card-3']
        assert await ids(engine_tab, '#cards >> internal:chain="article >> nth=0"') == ['card-1']

    @pytest.mark.asyncio
    async def test_visible_engine(self, engine_tab):
        assert await ids(engine_tab, '#btn-hidden >> visible=true') == []
        assert await ids(engine_tab, '#btn-hidden >> visible=false') == ['btn-hidden']
        assert await ids(engine_tab, '#pw-invisible >> visible=true') == []
        assert await ids(engine_tab, '#sized-zero >> visible=true') == []
        assert await ids(engine_tab, '#btn-save >> visible=true') == ['btn-save']

    @pytest.mark.asyncio
    async def test_label_placeholder_alt_title_engines(self, engine_tab):
        assert await ids(engine_tab, 'internal:label="Full name"i') == ['name-input']
        assert await ids(engine_tab, 'internal:label="Email address"i') == ['email-input']
        assert await ids(engine_tab, 'internal:label="Accept"i') == ['cb-checked']
        assert await ids(engine_tab, 'internal:attr=[placeholder="search"i]') == ['placeholder-input']
        assert await ids(engine_tab, 'internal:attr=[alt="Company logo"s]') == ['img-logo']
        assert await ids(engine_tab, 'internal:attr=[title="tooltip"i]') == ['span-title']

    @pytest.mark.asyncio
    async def test_test_id_engine(self, engine_tab):
        assert await ids(engine_tab, 'internal:testid=[data-testid="item"s]') == ['item', 'item', 'item']
        assert await ids(engine_tab, 'internal:testid=[data-testid="ITEM"s]') == []

    @pytest.mark.asyncio
    async def test_unknown_engine_raises(self, engine_tab):
        with pytest.raises(ScriptException, match='Unknown engine'):
            await ids(engine_tab, 'bogus=thing')


class TestRoleEngine:
    @pytest.mark.asyncio
    async def test_implicit_and_explicit_roles(self, engine_tab):
        assert await ids(engine_tab, 'internal:role=link') == ['link-docs']
        buttons = await ids(engine_tab, 'internal:role=button')
        assert 'btn-submit' in buttons
        assert 'div-button' in buttons
        assert 'shadow-btn' in buttons
        assert 'btn-hidden' not in buttons
        assert 'btn-aria-hidden' not in buttons
        assert 'anchor-no-href' not in buttons

    @pytest.mark.asyncio
    async def test_include_hidden(self, engine_tab):
        buttons = await ids(engine_tab, 'internal:role=button[include-hidden=true]')
        assert 'btn-hidden' in buttons
        assert 'btn-aria-hidden' in buttons

    @pytest.mark.asyncio
    async def test_name_substring_exact_and_regex(self, engine_tab):
        assert await ids(engine_tab, 'internal:role=button[name="sav"i]') == ['btn-save']
        assert await ids(engine_tab, 'internal:role=button[name="sav"s]') == []
        assert await ids(engine_tab, 'internal:role=button[name="Save"s]') == ['btn-save']
        assert await ids(engine_tab, 'internal:role=link[name=/docs$/]') == ['link-docs']
        assert await ids(engine_tab, 'internal:role=button[name="New: Item"s]') == ['badge-btn']

    @pytest.mark.asyncio
    async def test_heading_levels(self, engine_tab):
        assert await ids(engine_tab, 'internal:role=heading[level=2]') == ['h2-features']
        level_four = await ids(engine_tab, 'internal:role=heading[level=4]')
        assert level_four[0] == 'aria-heading'
        assert len(level_four) == 4
        assert 'title' in await ids(engine_tab, 'internal:role=heading[level=1]')

    @pytest.mark.asyncio
    async def test_checked_pressed_disabled(self, engine_tab):
        assert await ids(engine_tab, 'internal:role=checkbox[checked=true]') == ['cb-checked', 'aria-cb']
        assert await ids(engine_tab, 'internal:role=checkbox[checked=false]') == ['cb-unchecked']
        assert await ids(engine_tab, 'internal:role=button[pressed=true]') == ['btn-save']
        disabled = await ids(engine_tab, 'internal:role=button[disabled=true]')
        assert set(disabled) == {'btn-disabled', 'btn-in-disabled-fieldset'}

    @pytest.mark.asyncio
    async def test_accessible_names_from_labels_and_attributes(self, engine_tab):
        cases = {
            'name-input': 'Full name',
            'email-input': 'Email address',
            'placeholder-input': 'Search here',
            'labelledby-input': 'First Second',
            'cb-checked': 'Accept terms',
            'img-logo': 'Company logo',
            'input-submit': 'Send now',
            'link-docs': 'Read the docs',
        }
        for element_id, expected in cases.items():
            element = await engine_tab.find(id=element_id)
            assert await value_of(element, NAME) == expected, element_id

    @pytest.mark.asyncio
    async def test_presentation_image_and_wrapping_label_roles(self, engine_tab):
        img = await engine_tab.find(id='img-presentation')
        assert await value_of(img, ROLE) == 'presentation'
        assert await ids(engine_tab, 'internal:role=img') == ['img-logo']
        assert await ids(engine_tab, 'internal:role=textbox[name="Email"i]') == ['email-input']
        assert await ids(engine_tab, 'internal:role=combobox') == ['select-single']
        assert await ids(engine_tab, 'internal:role=listbox') == ['select-multi']

    @pytest.mark.asyncio
    async def test_invalid_role_attribute_raises(self, engine_tab):
        with pytest.raises(ScriptException, match='only supported for roles'):
            await ids(engine_tab, 'internal:role=link[checked=true]')


class TestElementStates:
    @pytest.mark.asyncio
    async def test_visible_hidden_enabled_disabled(self, engine_tab):
        visible = await engine_tab.find(id='btn-save')
        hidden = await engine_tab.find(id='btn-hidden')
        disabled = await engine_tab.find(id='btn-disabled')

        assert (await value_of(visible, STATE, 'visible'))['matches'] is True
        assert (await value_of(hidden, STATE, 'visible'))['matches'] is False
        assert (await value_of(hidden, STATE, 'hidden'))['matches'] is True
        assert (await value_of(visible, STATE, 'enabled'))['matches'] is True
        assert (await value_of(disabled, STATE, 'enabled'))['received'] == 'disabled'

    @pytest.mark.asyncio
    async def test_editable_checked_and_label_retargeting(self, engine_tab):
        readonly = await engine_tab.find(id='readonly-input')
        editable = await engine_tab.find(id='name-input')
        checkbox = await engine_tab.find(id='cb-checked')
        label = await engine_tab.find(id='wrapping-label')

        assert (await value_of(readonly, STATE, 'editable'))['received'] == 'readOnly'
        assert (await value_of(editable, STATE, 'editable'))['matches'] is True
        assert (await value_of(checkbox, STATE, 'checked'))['matches'] is True
        assert (await value_of(checkbox, STATE, 'unchecked'))['matches'] is False
        assert (await value_of(label, STATE, 'editable'))['matches'] is True

    @pytest.mark.asyncio
    async def test_editable_on_non_form_element_raises(self, engine_tab):
        heading = await engine_tab.find(id='title')
        with pytest.raises(ScriptException, match='aria-readonly'):
            await value_of(heading, STATE, 'editable')

    @pytest.mark.asyncio
    async def test_check_element_states_reports_first_missing_state(self, engine_tab):
        hidden = await engine_tab.find(id='btn-hidden')
        disabled = await engine_tab.find(id='btn-disabled')
        fine = await engine_tab.find(id='btn-save')

        assert await value_of(hidden, CHECK_STATES, ['visible', 'enabled', 'stable'], await_promise=True) == {
            'missingState': 'visible'
        }
        assert await value_of(disabled, CHECK_STATES, ['visible', 'enabled', 'stable'], await_promise=True) == {
            'missingState': 'enabled'
        }
        assert await value_of(fine, CHECK_STATES, ['visible', 'enabled', 'stable'], await_promise=True) is None

    @pytest.mark.asyncio
    async def test_hit_target_detects_overlay(self, engine_tab):
        covered = await engine_tab.find(id='covered')
        free = await engine_tab.find(id='free')

        covered_box = await value_of(
            covered, 'function() { const r = this.getBoundingClientRect(); return {x: r.x + r.width / 2, y: r.y + r.height / 2}; }'
        )
        free_box = await value_of(
            free, 'function() { const r = this.getBoundingClientRect(); return {x: r.x + r.width / 2, y: r.y + r.height / 2}; }'
        )

        result = await value_of(covered, HIT_TARGET, covered_box)
        assert result['hitTargetDescription'].startswith('<div id="overlay"')
        assert await value_of(free, HIT_TARGET, free_box) == 'done'
