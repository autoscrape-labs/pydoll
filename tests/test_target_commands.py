from pydoll.protocol.commands import TargetCommands


def test_activate_target():
    target_id = 'test_target_id'
    expected_result = {
        'method': 'Target.attachToTarget',
        'params': {'targetId': target_id},
    }
    assert TargetCommands.activate_target(target_id) == expected_result


def test_attach_to_target():
    target_id = 'test_target_id'
    expected_result = {
        'method': 'Target.attachToTarget',
        'params': {'targetId': target_id},
    }
    assert TargetCommands.attach_to_target(target_id) == expected_result


def test_close_target():
    target_id = 'test_target_id'
    expected_result = {
        'method': 'Target.closeTarget',
        'params': {'targetId': target_id},
    }
    assert TargetCommands.close_target(target_id) == expected_result


def test_create_target():
    url = 'http://example.com'
    expected_result = {'method': 'Target.createTarget', 'params': {'url': url}}
    assert TargetCommands.create_target(url) == expected_result


def test_get_targets():
    expected_result = {'method': 'Target.getTargets', 'params': {}}
    assert TargetCommands.get_targets() == expected_result
