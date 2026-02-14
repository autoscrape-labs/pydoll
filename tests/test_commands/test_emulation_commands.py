"""
Tests for EmulationCommands class.

This module contains tests for all EmulationCommands methods,
verifying that they generate the correct CDP commands with proper parameters.
"""

from pydoll.commands.emulation_commands import EmulationCommands
from pydoll.protocol.emulation.methods import EmulationMethod
from pydoll.protocol.emulation.types import UserAgentBrandVersion, UserAgentMetadata


def test_set_user_agent_override_minimal():
    """Test set_user_agent_override with only required parameter."""
    result = EmulationCommands.set_user_agent_override(user_agent='Test/1.0')
    assert result['method'] == EmulationMethod.SET_USER_AGENT_OVERRIDE
    assert result['params']['userAgent'] == 'Test/1.0'
    assert 'acceptLanguage' not in result['params']
    assert 'platform' not in result['params']
    assert 'userAgentMetadata' not in result['params']


def test_set_user_agent_override_with_accept_language():
    """Test set_user_agent_override with acceptLanguage parameter."""
    result = EmulationCommands.set_user_agent_override(
        user_agent='Test/1.0',
        accept_language='en-US,en;q=0.9',
    )
    assert result['params']['userAgent'] == 'Test/1.0'
    assert result['params']['acceptLanguage'] == 'en-US,en;q=0.9'


def test_set_user_agent_override_with_platform():
    """Test set_user_agent_override with platform parameter."""
    result = EmulationCommands.set_user_agent_override(
        user_agent='Test/1.0',
        platform='Win32',
    )
    assert result['params']['userAgent'] == 'Test/1.0'
    assert result['params']['platform'] == 'Win32'


def test_set_user_agent_override_with_metadata():
    """Test set_user_agent_override with full userAgentMetadata."""
    metadata = UserAgentMetadata(
        platform='Windows',
        platformVersion='15.0.0',
        architecture='x86',
        model='',
        mobile=False,
        brands=[
            UserAgentBrandVersion(brand='Not/A)Brand', version='20'),
            UserAgentBrandVersion(brand='Chromium', version='120'),
            UserAgentBrandVersion(brand='Google Chrome', version='120'),
        ],
        fullVersionList=[
            UserAgentBrandVersion(brand='Not/A)Brand', version='20.0.0.0'),
            UserAgentBrandVersion(brand='Chromium', version='120.0.6099.109'),
            UserAgentBrandVersion(brand='Google Chrome', version='120.0.6099.109'),
        ],
        bitness='64',
        wow64=False,
    )
    result = EmulationCommands.set_user_agent_override(
        user_agent='Mozilla/5.0 Chrome/120.0.6099.109',
        platform='Win32',
        user_agent_metadata=metadata,
    )
    assert result['method'] == EmulationMethod.SET_USER_AGENT_OVERRIDE
    assert result['params']['userAgent'] == 'Mozilla/5.0 Chrome/120.0.6099.109'
    assert result['params']['platform'] == 'Win32'
    assert result['params']['userAgentMetadata']['platform'] == 'Windows'
    assert result['params']['userAgentMetadata']['mobile'] is False
    assert len(result['params']['userAgentMetadata']['brands']) == 3
    assert result['params']['userAgentMetadata']['brands'][1]['brand'] == 'Chromium'


def test_set_user_agent_override_with_all_params():
    """Test set_user_agent_override with all parameters set."""
    metadata = UserAgentMetadata(
        platform='Android',
        platformVersion='14.0.0',
        architecture='arm',
        model='Pixel 7',
        mobile=True,
        bitness='64',
        wow64=False,
    )
    result = EmulationCommands.set_user_agent_override(
        user_agent='Mozilla/5.0 (Linux; Android 14)',
        accept_language='pt-BR,pt;q=0.9',
        platform='Linux armv81',
        user_agent_metadata=metadata,
    )
    assert result['params']['userAgent'] == 'Mozilla/5.0 (Linux; Android 14)'
    assert result['params']['acceptLanguage'] == 'pt-BR,pt;q=0.9'
    assert result['params']['platform'] == 'Linux armv81'
    assert result['params']['userAgentMetadata']['mobile'] is True
    assert result['params']['userAgentMetadata']['model'] == 'Pixel 7'


def test_set_user_agent_override_none_params_excluded():
    """Test that None parameters are not included in the command."""
    result = EmulationCommands.set_user_agent_override(
        user_agent='Test/1.0',
        accept_language=None,
        platform=None,
        user_agent_metadata=None,
    )
    assert 'acceptLanguage' not in result['params']
    assert 'platform' not in result['params']
    assert 'userAgentMetadata' not in result['params']
