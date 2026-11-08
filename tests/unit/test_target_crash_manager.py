from __future__ import annotations

import pytest

from pydoll.connection.managers import TargetCrashManager
from pydoll.exceptions import TargetCrashed
from pydoll.protocol.browser.methods import BrowserMethod
from pydoll.protocol.dom.methods import DomMethod
from pydoll.protocol.inspector.events import InspectorEvent
from pydoll.protocol.network.methods import NetworkMethod
from pydoll.protocol.page.events import PageEvent
from pydoll.protocol.page.methods import PageMethod
from pydoll.protocol.runtime.methods import RuntimeMethod
from pydoll.protocol.target.methods import TargetMethod


def test_starts_alive_and_accepts_every_command():
    manager = TargetCrashManager()
    assert manager.crashed is False
    manager.check({'method': RuntimeMethod.EVALUATE})


def test_crash_event_marks_the_target_crashed_and_reports_it_once():
    manager = TargetCrashManager()
    assert manager.track({'method': InspectorEvent.TARGET_CRASHED, 'params': {}}) is True
    assert manager.crashed is True


def test_reload_after_crash_clears_the_crash():
    manager = TargetCrashManager()
    manager.track({'method': InspectorEvent.TARGET_CRASHED, 'params': {}})
    assert manager.track({'method': InspectorEvent.TARGET_RELOADED_AFTER_CRASH}) is False
    assert manager.crashed is False


def test_events_of_a_child_session_leave_the_target_alone():
    manager = TargetCrashManager()
    event = {'method': InspectorEvent.TARGET_CRASHED, 'params': {}, 'sessionId': 'IFRAME'}
    assert manager.track(event) is False
    assert manager.crashed is False


def test_other_events_change_nothing():
    manager = TargetCrashManager()
    assert manager.track({'method': PageEvent.LOAD_EVENT_FIRED, 'params': {}}) is False
    assert manager.crashed is False


@pytest.mark.parametrize(
    'method',
    [RuntimeMethod.EVALUATE, PageMethod.ENABLE, NetworkMethod.ENABLE, DomMethod.GET_DOCUMENT],
)
def test_a_crashed_target_refuses_commands_that_need_its_renderer(method):
    manager = TargetCrashManager()
    manager.track({'method': InspectorEvent.TARGET_CRASHED, 'params': {}})
    with pytest.raises(TargetCrashed):
        manager.check({'method': method})


@pytest.mark.parametrize(
    'method',
    [
        PageMethod.NAVIGATE,
        PageMethod.RELOAD,
        PageMethod.CLOSE,
        NetworkMethod.SET_COOKIE,
        BrowserMethod.GET_VERSION,
        'Page.navigate',
        TargetMethod.GET_TARGETS,
    ],
)
def test_a_crashed_target_still_takes_commands_the_browser_answers(method):
    manager = TargetCrashManager()
    manager.track({'method': InspectorEvent.TARGET_CRASHED, 'params': {}})
    manager.check({'method': method})


def test_a_crashed_target_lets_child_session_commands_through():
    manager = TargetCrashManager()
    manager.track({'method': InspectorEvent.TARGET_CRASHED, 'params': {}})
    manager.check({'method': RuntimeMethod.EVALUATE, 'sessionId': 'IFRAME'})


def _crashed_manager() -> TargetCrashManager:
    manager = TargetCrashManager()
    manager.track({'method': InspectorEvent.TARGET_CRASHED, 'params': {}})
    return manager


@pytest.mark.parametrize(
    'method', [PageMethod.NAVIGATE, PageMethod.RELOAD, PageMethod.NAVIGATE_TO_HISTORY_ENTRY]
)
def test_a_successful_navigation_recovers_a_crashed_target(method):
    manager = _crashed_manager()
    manager.observe_answer({'method': method}, {'id': 1, 'result': {'frameId': 'F'}})
    assert manager.crashed is False


def test_a_navigation_that_failed_leaves_the_target_crashed():
    manager = _crashed_manager()
    manager.observe_answer(
        {'method': PageMethod.NAVIGATE},
        {'id': 1, 'result': {'frameId': 'F', 'errorText': 'net::ERR_NAME_NOT_RESOLVED'}},
    )
    assert manager.crashed is True


def test_other_answers_leave_the_target_crashed():
    manager = _crashed_manager()
    manager.observe_answer({'method': PageMethod.GET_NAVIGATION_HISTORY}, {'id': 1, 'result': {}})
    manager.observe_answer(
        {'method': PageMethod.NAVIGATE, 'sessionId': 'IFRAME'}, {'id': 2, 'result': {}}
    )
    assert manager.crashed is True
