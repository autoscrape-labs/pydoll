from __future__ import annotations

from pydoll.commands import FetchCommands, NetworkCommands, PageCommands
from pydoll.connection.managers import DomainsManager
from pydoll.protocol.network.methods import NetworkMethod
from pydoll.protocol.page.methods import PageMethod


def _methods(manager: DomainsManager) -> list[str]:
    return [command['method'] for command in manager.missing]


def test_an_enabled_domain_is_live_so_nothing_is_missing():
    manager = DomainsManager()
    manager.record(NetworkCommands.enable())
    assert manager.missing == []


def test_a_new_session_misses_every_wanted_domain_in_order():
    manager = DomainsManager()
    manager.record(NetworkCommands.enable())
    manager.record(PageCommands.enable())
    manager.reset_session()
    assert _methods(manager) == [NetworkMethod.ENABLE, PageMethod.ENABLE]


def test_missing_commands_keep_the_parameters_they_were_enabled_with():
    fetch_enable = FetchCommands.enable(handle_auth_requests=True, url_pattern='*.png')
    manager = DomainsManager()
    manager.record(fetch_enable)
    manager.reset_session()
    assert manager.missing[0]['params'] == fetch_enable['params']


def test_changing_a_recorded_command_afterwards_does_not_change_what_is_missing():
    fetch_enable = FetchCommands.enable(handle_auth_requests=False, url_pattern='*.png')
    manager = DomainsManager()
    manager.record(fetch_enable)
    fetch_enable['params']['patterns'] = []
    manager.reset_session()
    assert manager.missing[0]['params']['patterns'] != []


def test_a_disabled_domain_is_no_longer_wanted():
    manager = DomainsManager()
    manager.record(NetworkCommands.enable())
    manager.record(PageCommands.enable())
    manager.record(PageCommands.disable())
    manager.reset_session()
    assert _methods(manager) == [NetworkMethod.ENABLE]


def test_a_forgotten_domain_is_not_missing():
    manager = DomainsManager()
    manager.record(NetworkCommands.enable())
    manager.reset_session()
    manager.forget(NetworkMethod.ENABLE)
    assert manager.missing == []


def test_a_domain_enabled_again_on_the_new_session_is_live():
    manager = DomainsManager()
    manager.record(NetworkCommands.enable())
    manager.record(PageCommands.enable())
    manager.reset_session()
    manager.record(NetworkCommands.enable())
    assert _methods(manager) == [PageMethod.ENABLE]


def test_commands_for_a_child_session_are_ignored():
    manager = DomainsManager()
    command = PageCommands.enable()
    command['sessionId'] = 'IFRAME'
    manager.record(command)
    manager.reset_session()
    assert manager.missing == []


def test_clear_forgets_every_domain():
    manager = DomainsManager()
    manager.record(NetworkCommands.enable())
    manager.clear()
    manager.reset_session()
    assert manager.missing == []


def test_a_domain_marked_live_is_no_longer_missing():
    manager = DomainsManager()
    manager.record(NetworkCommands.enable())
    manager.record(PageCommands.enable())
    manager.reset_session()

    manager.mark_live(NetworkMethod.ENABLE)

    assert _methods(manager) == [PageMethod.ENABLE]


def test_a_rejected_restore_stops_the_domain_from_being_wanted():
    manager = DomainsManager()
    manager.record(NetworkCommands.enable())
    manager.reset_session()
    restore = manager.missing[0]

    manager.reject(restore)
    manager.reset_session()

    assert manager.missing == []


def test_a_rejected_restore_keeps_a_domain_enabled_again_since_with_other_parameters():
    manager = DomainsManager()
    manager.record(NetworkCommands.enable())
    manager.reset_session()
    restore = manager.missing[0]
    manager.record(NetworkCommands.enable(max_total_buffer_size=1024))

    manager.reject(restore)
    manager.reset_session()

    assert manager.missing == [
        {'method': NetworkMethod.ENABLE, 'params': {'maxTotalBufferSize': 1024}}
    ]
