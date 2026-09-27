"""Locator, ElementHandle, keyboard and mouse behaviour against real Chrome."""

from __future__ import annotations

import re

import pytest

from _pages import page_url
from pydoll.playwright.async_api import Error, TimeoutError


@pytest.fixture
def engine_page_url():
    return page_url('playwright_engine.html')


class TestResolution:
    @pytest.mark.asyncio
    async def test_count_all_nth_first_last(self, page, engine_page_url):
        await page.goto(engine_page_url)
        items = page.locator('#list li')
        assert await items.count() == 3
        assert await items.first.text_content() == 'one'
        assert await items.last.text_content() == 'three'
        assert await items.nth(1).text_content() == 'two'
        assert [await item.text_content() for item in await items.all()] == ['one', 'two', 'three']
        assert await items.all_text_contents() == ['one', 'two', 'three']
        assert await items.all_inner_texts() == ['one', 'two', 'three']

    @pytest.mark.asyncio
    async def test_strict_mode_violation(self, page, engine_page_url):
        await page.goto(engine_page_url)
        with pytest.raises(Error, match='strict mode violation'):
            await page.locator('#list li').text_content()
        assert await page.text_content('#list li') == 'one'

    @pytest.mark.asyncio
    async def test_get_by_helpers(self, page, engine_page_url):
        await page.goto(engine_page_url)
        assert await page.get_by_role('button', name='Save').get_attribute('id') == 'btn-save'
        assert await page.get_by_role('heading', level=2).text_content() == 'Features'
        assert await page.get_by_label('Full name').get_attribute('id') == 'name-input'
        assert await page.get_by_placeholder('search').get_attribute('id') == 'placeholder-input'
        assert await page.get_by_alt_text('Company logo').get_attribute('id') == 'img-logo'
        assert await page.get_by_title('Tooltip').get_attribute('id') == 'span-title'
        assert await page.get_by_test_id('shadow-item').text_content() == 'Shadow Button'
        assert await page.get_by_text('Hello World', exact=True).get_attribute('id') == 'p-hello'
        assert await page.get_by_text(re.compile(r'hello world again')).get_attribute('id') == 'p-hello-again'
        assert await page.get_by_role('checkbox', checked=True).first.get_attribute('id') == 'cb-checked'

    @pytest.mark.asyncio
    async def test_chaining_filter_and_or(self, page, engine_page_url):
        await page.goto(engine_page_url)
        cards = page.locator('.card')
        assert await cards.filter(has_text='Card B').get_attribute('id') == 'card-2'
        assert await cards.filter(has=page.locator('button')).count() == 2
        assert await cards.filter(has_not=page.locator('button')).get_attribute('id') == 'card-2'
        assert await cards.filter(has_not_text='Card B').count() == 2
        assert await cards.locator('h4').nth(2).text_content() == 'Card C'
        assert await page.locator('#card-1').or_(page.locator('#card-3')).count() == 2
        assert await cards.and_(page.locator('#card-3')).get_attribute('id') == 'card-3'
        assert await page.locator('#cards').locator(page.locator('article')).count() == 3
        assert await page.locator('#btn-hidden').filter(visible=True).count() == 0

    @pytest.mark.asyncio
    async def test_element_handles(self, page, engine_page_url):
        await page.goto(engine_page_url)
        handle = await page.locator('#btn-save').element_handle()
        assert await handle.inner_text() == 'Save'
        assert await handle.evaluate('(e, s) => e.id + s', '!') == 'btn-save!'
        handles = await page.locator('.card').element_handles()
        assert len(handles) == 3
        inner = await handles[0].query_selector('h4')
        assert inner is not None
        assert await inner.text_content() == 'Card A'
        assert await handles[0].eval_on_selector_all('button', 'b => b.length') == 1
        assert await handle.bounding_box() is not None
        assert (await page.locator('#btn-hidden').bounding_box()) is None

    @pytest.mark.asyncio
    async def test_state_readers(self, page, engine_page_url):
        await page.goto(engine_page_url)
        assert await page.locator('#btn-save').is_visible()
        assert await page.locator('#btn-hidden').is_hidden()
        assert not await page.locator('#nope').is_visible()
        assert await page.locator('#nope').is_hidden()
        assert await page.locator('#btn-disabled').is_disabled()
        assert await page.locator('#btn-save').is_enabled()
        assert await page.locator('#readonly-input').is_editable() is False
        assert await page.locator('#name-input').is_editable()
        assert await page.locator('#cb-checked').is_checked()
        assert not await page.locator('#cb-unchecked').is_checked()
        assert await page.locator('#p-hello').inner_html() == 'Hello   World'
        assert await page.locator('#select-single').input_value() == 'b'

    @pytest.mark.asyncio
    async def test_wait_for_and_timeout_call_log(self, page, engine_page_url):
        await page.goto(engine_page_url)
        await page.locator('#btn-save').wait_for()
        await page.locator('#btn-hidden').wait_for(state='hidden')
        with pytest.raises(TimeoutError) as info:
            await page.locator('#btn-hidden').click(timeout=300)
        message = str(info.value)
        assert 'Timeout 300ms exceeded' in message
        assert 'element is not visible' in message
        with pytest.raises(TimeoutError, match='element is not enabled'):
            await page.locator('#btn-disabled').click(timeout=300)
        with pytest.raises(TimeoutError, match='intercepts pointer events'):
            await page.locator('#covered').click(timeout=300)


class TestActions:
    @pytest.mark.asyncio
    async def test_click_variants(self, page):
        await page.goto(page_url('playwright_events.html'))
        await page.locator('#mouse').click()
        assert await page.text_content('#mouse') == '0:1'
        await page.locator('#mouse').click(button='right')
        assert await page.text_content('#mouse') == 'context'
        await page.locator('#mouse').dblclick()
        assert await page.text_content('#mouse') == 'dbl:2'
        await page.locator('#mouse').click(position={'x': 5, 'y': 5}, delay=20)
        assert await page.text_content('#mouse') == '0:1'
        await page.locator('#mouse').click(force=True)
        await page.locator('#mouse').click(trial=True)

    @pytest.mark.asyncio
    async def test_hover_and_scroll_into_view(self, page):
        await page.goto(page_url('playwright_events.html'))
        await page.locator('#hover-target').hover()
        assert await page.text_content('#hover-result') == 'hovered'
        await page.locator('#deep-btn').click()
        assert await page.evaluate('() => document.getElementById("scroll-box").scrollTop') > 0

    @pytest.mark.asyncio
    async def test_fill_clear_type_press(self, page):
        await page.goto(page_url('playwright_events.html'))
        await page.locator('#name').fill('Ana')
        assert await page.input_value('#name') == 'Ana'
        await page.locator('#name').press('End')
        await page.locator('#name').press_sequentially(' Lima')
        assert await page.input_value('#name') == 'Ana Lima'
        await page.locator('#name').press('Enter')
        assert await page.text_content('#submitted') == 'submitted:Ana Lima'
        await page.locator('#name').clear()
        assert await page.input_value('#name') == ''
        await page.fill('#name', 'x')
        await page.locator('#name').press('Control+A')
        await page.keyboard.press('Backspace')
        assert await page.input_value('#name') == ''

    @pytest.mark.asyncio
    async def test_fill_rejects_non_editable(self, page, engine_page_url):
        await page.goto(engine_page_url)
        with pytest.raises(Error, match='cannot be filled|not an <input>'):
            await page.locator('#file-input, #title').first.fill('x', timeout=500)

    @pytest.mark.asyncio
    async def test_fill_special_inputs_and_contenteditable(self, page, engine_page_url):
        await page.goto(engine_page_url)
        await page.fill('#number-input', '42')
        assert await page.input_value('#number-input') == '42'
        await page.fill('#date-input', '2024-05-06')
        assert await page.input_value('#date-input') == '2024-05-06'
        await page.fill('#color-input', '#ff0000')
        assert await page.input_value('#color-input') == '#ff0000'
        await page.fill('#editable', 'edited')
        assert await page.text_content('#editable') == 'edited'
        with pytest.raises(Error, match='Cannot type text into input\\[type=number\\]'):
            await page.fill('#number-input', 'abc', timeout=500)

    @pytest.mark.asyncio
    async def test_check_uncheck_select_option(self, page, engine_page_url):
        await page.goto(engine_page_url)
        await page.locator('#cb-unchecked').check()
        assert await page.is_checked('#cb-unchecked')
        await page.locator('#cb-unchecked').check()
        await page.locator('#cb-unchecked').uncheck()
        assert not await page.is_checked('#cb-unchecked')
        await page.locator('#cb-unchecked').set_checked(True)
        assert await page.is_checked('#cb-unchecked')
        assert await page.select_option('#select-single', 'a') == ['a']
        assert await page.select_option('#select-single', label='Beta') == ['b']
        assert await page.select_option('#select-single', index=0) == ['a']
        assert await page.locator('#select-multi').select_option(['x', 'z']) == ['x', 'z']
        assert await page.locator('#select-multi').evaluate(
            's => [...s.selectedOptions].map(o => o.value)'
        ) == ['x', 'z']
        with pytest.raises(TimeoutError, match='did not find some options'):
            await page.select_option('#select-single', 'zzz', timeout=300)

    @pytest.mark.asyncio
    async def test_set_input_files(self, page, tmp_path):
        await page.goto(page_url('playwright_events.html'))
        file_one = tmp_path / 'one.txt'
        file_one.write_text('1')
        await page.set_input_files('#file-input', file_one)
        assert await page.text_content('#file-result') == 'one.txt'
        await page.locator('#file-input-multi').set_input_files([file_one, {'name': 'two.txt', 'mimeType': 'text/plain', 'buffer': b'2'}])
        assert await page.text_content('#file-result') == 'one.txt,two.txt'
        with pytest.raises(Error, match='File not found'):
            await page.set_input_files('#file-input', tmp_path / 'missing.txt', timeout=500)

    @pytest.mark.asyncio
    async def test_drag_and_drop_and_dispatch_event(self, page):
        await page.goto(page_url('playwright_events.html'))
        await page.locator('#drag-source').drag_to(page.locator('#drop-target'))
        assert (await page.text_content('#drop-result')).startswith('dropped')
        await page.locator('#mouse').dispatch_event('click', {'button': 2})
        assert await page.text_content('#mouse') == '2:0'

    @pytest.mark.asyncio
    async def test_focus_blur_and_select_text(self, page):
        await page.goto(page_url('playwright_events.html'))
        await page.locator('#name').focus()
        assert await page.evaluate('() => document.activeElement.id') == 'name'
        await page.locator('#name').blur()
        assert await page.evaluate('() => document.activeElement.id') != 'name'
        await page.fill('#name', 'select me')
        await page.locator('#name').select_text()
        assert await page.evaluate('() => { const e = document.getElementById("name"); return e.selectionEnd - e.selectionStart }') == 9


class TestKeyboardAndMouse:
    @pytest.mark.asyncio
    async def test_keyboard_events_carry_key_code_and_modifiers(self, page):
        await page.goto(page_url('playwright_events.html'))
        await page.keyboard.press('a')
        await page.keyboard.press('Shift+A')
        await page.keyboard.press('Control+ArrowDown')
        await page.keyboard.press('Digit1')
        assert await page.text_content('#keys') == 'a:KeyA:;Shift:ShiftLeft:s;A:KeyA:s;Control:ControlLeft:c;ArrowDown:ArrowDown:c;1:Digit1:;'

    @pytest.mark.asyncio
    async def test_keyboard_type_and_insert_text(self, page):
        await page.goto(page_url('playwright_events.html'))
        await page.focus('#name')
        await page.keyboard.type('héllo €')
        await page.keyboard.insert_text('!')
        assert await page.input_value('#name') == 'héllo €!'

    @pytest.mark.asyncio
    async def test_mouse_click_wheel_and_touch(self, page):
        await page.goto(page_url('playwright_events.html'))
        box = await page.locator('#mouse').bounding_box()
        assert box is not None
        await page.mouse.click(box['x'] + 5, box['y'] + 5)
        assert await page.text_content('#mouse') == '0:1'
        await page.mouse.dblclick(box['x'] + 5, box['y'] + 5)
        assert await page.text_content('#mouse') == 'dbl:2'
        scroll_box = await page.locator('#scroll-box').bounding_box()
        assert scroll_box is not None
        await page.mouse.move(scroll_box['x'] + 10, scroll_box['y'] + 10)
        await page.mouse.wheel(0, 100)
        await page.wait_for_function('() => document.getElementById("wheel-result").textContent === "wheel:1"')
        await page.mouse.move(0, 0, steps=3)
        await page.mouse.down()
        await page.mouse.up()


class TestFrames:
    @pytest.mark.asyncio
    async def test_frame_locator_and_frames(self, page):
        await page.goto(page_url('test_iframe_simple.html'))
        inner = page.frame_locator('#simple-iframe')
        assert await inner.locator('#iframe-heading').text_content() == 'Iframe Content'
        await inner.locator('#iframe-input').fill('inside')
        assert await inner.locator('#iframe-input').input_value() == 'inside'
        await inner.get_by_role('button', name='Submit').click()
        assert await inner.locator('#iframe-input').count() == 1
        assert await inner.owner.get_attribute('id') == 'simple-iframe'
        await page.wait_for_function('() => window.frames.length === 1')
        assert len(page.frames) == 2
        child = page.frames[1]
        assert child.parent_frame is page.main_frame
        assert child.url.endswith('test_iframe_content.html')
        assert await child.text_content('#iframe-heading') == 'Iframe Content'
        assert await child.evaluate('() => document.title') == await child.title()
        element = await page.query_selector('#simple-iframe')
        assert element is not None
        content_frame = await element.content_frame()
        assert content_frame is not None
        assert await content_frame.locator('#iframe-heading').text_content() == 'Iframe Content'

    @pytest.mark.asyncio
    async def test_nested_frames(self, page):
        await page.goto(page_url('test_iframe_nested.html'))
        text = await page.frame_locator('iframe').first.frame_locator('iframe').first.locator('body').text_content()
        assert text and text.strip()
