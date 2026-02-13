"""
Integration tests for Tab and Request classes.

This module tests the integration between the Tab class and the Request class,
focusing on the 'request' property and how they work together for HTTP requests.
"""

import pytest
import pytest_asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from pydoll.browser.tab import Tab
from pydoll.browser.requests.request import Request
from pydoll.browser.requests.response import Response
from pydoll.protocol.fetch.types import HeaderEntry
from pydoll.protocol.network.types import CookieParam


@pytest_asyncio.fixture
async def mock_connection_handler():
    """Mock connection handler for Tab tests."""
    with patch('pydoll.connection.ConnectionHandler', autospec=True) as mock:
        handler = mock.return_value
        handler.execute_command = AsyncMock()
        handler.register_callback = AsyncMock()
        handler.remove_callback = AsyncMock()
        handler.clear_callbacks = AsyncMock()
        handler.network_logs = []
        handler.dialog = None
        yield handler


@pytest_asyncio.fixture
async def mock_browser():
    """Mock browser instance."""
    browser = MagicMock()
    browser.close_tab = AsyncMock()
    return browser


@pytest_asyncio.fixture
async def tab(mock_browser, mock_connection_handler):
    """Tab fixture with mocked dependencies."""
    # Generate unique target_id for each test to avoid singleton conflicts
    unique_target_id = f'test-target-{uuid.uuid4().hex[:8]}'
    
    with patch('pydoll.browser.tab.ConnectionHandler', return_value=mock_connection_handler):
        tab_instance = Tab(
            browser=mock_browser,
            connection_port=9222,
            target_id=unique_target_id,
            browser_context_id='test-context-id'
        )
        
        # Mock network events properties
        tab_instance._network_events_enabled = False
        tab_instance._page_events_enabled = False
        tab_instance._dom_events_enabled = False
        tab_instance._runtime_events_enabled = False
        tab_instance._fetch_events_enabled = False
        tab_instance._intercept_file_chooser_dialog_enabled = False
        
        yield tab_instance


@pytest_asyncio.fixture
def cleanup_tab_registry():
    """No-op: singleton removed; keep fixture for compatibility."""
    yield


class TestTabRequestProperty:
    """Test the request property on Tab class."""

    def test_request_property_lazy_initialization(self, tab):
        """Test that request property creates Request instance lazily."""
        # Initially _request should be None
        assert tab._request is None
        
        # First access should create the Request instance
        request_instance = tab.request
        assert request_instance is not None
        assert isinstance(request_instance, Request)
        assert tab._request is request_instance
        
        # Second access should return the same instance
        request_instance2 = tab.request
        assert request_instance2 is request_instance

    def test_request_property_binds_to_tab(self, tab):
        """Test that Request instance is properly bound to the Tab."""
        request_instance = tab.request
        
        # Request should have reference to the tab
        assert request_instance.tab is tab

    def test_request_property_type_annotation(self, tab):
        """Test that request property returns correct type."""
        request_instance = tab.request
        assert isinstance(request_instance, Request)

    def test_multiple_tabs_have_separate_requests(self, mock_browser, mock_connection_handler):
        """Test that different Tab instances have separate Request instances."""
        # Create two different tabs
        with patch('pydoll.browser.tab.ConnectionHandler', return_value=mock_connection_handler):
            tab1 = Tab(
                browser=mock_browser,
                connection_port=9222,
                target_id="test-target-1",
                browser_context_id='test-context-1'
            )
            
            tab2 = Tab(
                browser=mock_browser,
                connection_port=9222,
                target_id="test-target-2",
                browser_context_id='test-context-2'
            )
            
            # Each tab should have its own Request instance
            request1 = tab1.request
            request2 = tab2.request
            
            assert request1 is not request2
            assert request1.tab is tab1
            assert request2.tab is tab2


class TestTabRequestIntegration:
    """Test integration scenarios between Tab and Request."""

    @pytest.mark.asyncio
    async def test_request_uses_tab_network_events(self, tab):
        """Test that Request properly uses Tab's network event system."""
        request_instance = tab.request
        
        # Mock network events methods
        tab.enable_network_events = AsyncMock()
        tab.disable_network_events = AsyncMock()
        tab.on = AsyncMock(side_effect=lambda *a, **kw: len(tab.on.call_args_list))
        tab.remove_callback = AsyncMock()

        # Mock tab execute command for HTTP request
        tab._execute_command = AsyncMock()
        mock_result = {
            'result': {
                'result': {
                    'value': {
                        'status': 200,
                        'content': [72, 101, 108, 108, 111],  # "Hello" as bytes
                        'text': 'Hello',
                        'json': {'message': 'success'},
                        'url': 'https://example.com'
                    }
                }
            }
        }
        tab._execute_command.return_value = mock_result
        
        # Mock helper methods to avoid actual network processing
        with patch.object(request_instance, '_extract_received_headers') as mock_extract_headers, \
             patch.object(request_instance, '_extract_sent_headers') as mock_extract_sent, \
             patch.object(request_instance, '_extract_set_cookies') as mock_extract_cookies:
            
            mock_extract_headers.return_value = [HeaderEntry(name='Content-Type', value='application/json')]
            mock_extract_sent.return_value = [HeaderEntry(name='User-Agent', value='Test-Agent')]
            mock_extract_cookies.return_value = [CookieParam(name='session', value='abc123')]
            
            # Make a request
            response = await request_instance.get('https://example.com')
            
            # Verify response
            assert isinstance(response, Response)
            assert response.status_code == 200
            assert response.text == 'Hello'
            
            # Verify that tab's execute_command was called
            tab._execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_enables_network_events_when_needed(self, tab):
        """Test that Request enables network events on tab when not already enabled."""
        request_instance = tab.request
        
        # Tab initially has network events disabled
        tab._network_events_enabled = False
        tab.enable_network_events = AsyncMock()
        tab.disable_network_events = AsyncMock()
        tab.on = AsyncMock(side_effect=lambda *a, **kw: len(tab.on.call_args_list))
        tab.remove_callback = AsyncMock()

        # Mock tab execute command
        tab._execute_command = AsyncMock()
        mock_result = {
            'result': {
                'result': {
                    'value': {
                        'status': 200,
                        'content': [],
                        'text': 'OK',
                        'json': None,
                        'url': 'https://example.com'
                    }
                }
            }
        }
        tab._execute_command.return_value = mock_result

        # Mock helper methods
        with patch.object(request_instance, '_extract_received_headers') as mock_extract_headers, \
             patch.object(request_instance, '_extract_sent_headers') as mock_extract_sent, \
             patch.object(request_instance, '_extract_set_cookies') as mock_extract_cookies:

            mock_extract_headers.return_value = []
            mock_extract_sent.return_value = []
            mock_extract_cookies.return_value = []

            # Make a request
            await request_instance.get('https://example.com')

            # Verify network events were enabled and callbacks were registered
            tab.enable_network_events.assert_called_once()
            assert tab.on.call_count == 4  # Four network events should be registered

    @pytest.mark.asyncio
    async def test_request_clears_callbacks_after_completion(self, tab):
        """Test that Request clears callbacks after request completion."""
        request_instance = tab.request
        
        # Mock tab methods
        tab._network_events_enabled = False
        tab.enable_network_events = AsyncMock()
        tab.disable_network_events = AsyncMock()
        tab.on = AsyncMock(side_effect=lambda *a, **kw: len(tab.on.call_args_list))
        tab.remove_callback = AsyncMock()
        tab._execute_command = AsyncMock()

        mock_result = {
            'result': {
                'result': {
                    'value': {
                        'status': 200,
                        'content': [],
                        'text': 'OK',
                        'json': None,
                        'url': 'https://example.com'
                    }
                }
            }
        }
        tab._execute_command.return_value = mock_result

        # Mock helper methods
        with patch.object(request_instance, '_extract_received_headers') as mock_extract_headers, \
             patch.object(request_instance, '_extract_sent_headers') as mock_extract_sent, \
             patch.object(request_instance, '_extract_set_cookies') as mock_extract_cookies:

            mock_extract_headers.return_value = []
            mock_extract_sent.return_value = []
            mock_extract_cookies.return_value = []

            # Make a request
            await request_instance.get('https://example.com')

            # Verify callbacks were removed surgically (4 callbacks registered)
            assert tab.remove_callback.call_count == 4

    @pytest.mark.asyncio
    async def test_request_clears_callbacks_on_error(self, tab):
        """Test that Request clears callbacks even when request fails."""
        request_instance = tab.request
        
        # Mock tab methods
        tab._network_events_enabled = False
        tab.enable_network_events = AsyncMock()
        tab.disable_network_events = AsyncMock()
        tab.on = AsyncMock(side_effect=lambda *a, **kw: len(tab.on.call_args_list))
        tab.remove_callback = AsyncMock()

        # Make tab._execute_command raise an exception
        tab._execute_command = AsyncMock(side_effect=Exception("Network error"))

        # Make a request that should fail
        with pytest.raises(Exception):  # Should raise HTTPError wrapping the original exception
            await request_instance.get('https://example.com')

        # Verify callbacks were still removed despite the error
        assert tab.remove_callback.call_count == 4

    @pytest.mark.asyncio
    async def test_request_http_methods_integration(self, tab):
        """Test that all HTTP methods work through the Tab's request property."""
        request_instance = tab.request
        
        # Mock tab methods
        tab._network_events_enabled = False
        tab.enable_network_events = AsyncMock()
        tab.disable_network_events = AsyncMock()
        tab.on = AsyncMock(side_effect=lambda *a, **kw: len(tab.on.call_args_list))
        tab.remove_callback = AsyncMock()
        tab._execute_command = AsyncMock()

        mock_result = {
            'result': {
                'result': {
                    'value': {
                        'status': 200,
                        'content': [],
                        'text': 'OK',
                        'json': None,
                        'url': 'https://example.com'
                    }
                }
            }
        }
        tab._execute_command.return_value = mock_result

        # Mock helper methods
        with patch.object(request_instance, '_extract_received_headers') as mock_extract_headers, \
             patch.object(request_instance, '_extract_sent_headers') as mock_extract_sent, \
             patch.object(request_instance, '_extract_set_cookies') as mock_extract_cookies:

            mock_extract_headers.return_value = []
            mock_extract_sent.return_value = []
            mock_extract_cookies.return_value = []

            # Test all HTTP methods
            methods_to_test = [
                ('get', lambda: request_instance.get('https://example.com')),
                ('post', lambda: request_instance.post('https://example.com', data={'key': 'value'})),
                ('put', lambda: request_instance.put('https://example.com', json={'update': True})),
                ('patch', lambda: request_instance.patch('https://example.com', json={'patch': True})),
                ('delete', lambda: request_instance.delete('https://example.com')),
                ('head', lambda: request_instance.head('https://example.com')),
                ('options', lambda: request_instance.options('https://example.com')),
            ]

            for method_name, method_call in methods_to_test:
                # Reset mocks
                tab._execute_command.reset_mock()
                tab.remove_callback.reset_mock()

                # Execute method
                response = await method_call()

                # Verify response
                assert isinstance(response, Response)
                assert response.status_code == 200

                # Verify tab's execute_command was called
                tab._execute_command.assert_called_once()
                # Verify callbacks were removed surgically (4 per request)
                assert tab.remove_callback.call_count == 4

    def test_request_property_singleton_behavior(self, tab):
        """Test that request property maintains singleton behavior per tab."""
        # Multiple accesses should return the same instance
        request1 = tab.request
        request2 = tab.request
        request3 = tab.request
        
        assert request1 is request2
        assert request2 is request3
        assert isinstance(request1, Request)

    @pytest.mark.asyncio
    async def test_tab_request_maintains_state(self, tab):
        """Test that Tab's request instance maintains its state across calls."""
        request_instance = tab.request
        
        # Simulate some state changes in the request instance
        request_instance._network_events_enabled = True
        request_instance._requests_sent = ['mock_request']
        request_instance._requests_received = ['mock_response']
        
        # Access request property again
        same_request = tab.request
        
        # Should be the same instance with preserved state
        assert same_request is request_instance
        assert same_request._network_events_enabled is True
        assert same_request._requests_sent == ['mock_request']
        assert same_request._requests_received == ['mock_response']


class TestTabRequestEdgeCases:
    """Test edge cases for Tab-Request integration."""

    def test_request_property_after_tab_reuse(self, mock_browser, mock_connection_handler):
        """Test request property behavior when Tab instances are reused."""
        # Create tab with specific target_id
        target_id = "reusable-target-123"
        
        with patch('pydoll.browser.tab.ConnectionHandler', return_value=mock_connection_handler):
            # First tab instance
            tab1 = Tab(
                browser=mock_browser,
                connection_port=9222,
                target_id=target_id,
                browser_context_id='test-context-reuse'
            )
            request1 = tab1.request
            
            # Second tab instance with same target_id (no singleton anymore)
            tab2 = Tab(
                browser=mock_browser,
                connection_port=9222,
                target_id=target_id,
                browser_context_id='test-context-reuse'
            )
            # With no singleton, they are different instances, but independent request is allowed
            assert tab2 is not tab1
            # Request instances are created per tab; they are distinct here
            request2 = tab2.request
            assert request2 is not request1

    @pytest.mark.asyncio
    async def test_request_property_memory_efficiency(self, tab):
        """Test that request property doesn't create unnecessary instances."""
        import weakref
        
        # Get initial request instance
        request_instance = tab.request
        weak_ref = weakref.ref(request_instance)
        
        # Clear local reference
        del request_instance
        
        # Request instance should still exist because tab holds reference
        assert weak_ref() is not None
        
        # Getting request again should return same instance
        same_request = tab.request
        assert weak_ref() is same_request

    def test_request_property_with_different_tab_states(self, mock_browser, mock_connection_handler):
        """Test request property with tabs in different states."""
        # Create tabs with different configurations
        tab_configurations = [
            {'target_id': 'tab-1', 'browser_context_id': 'context-1'},
            {'target_id': 'tab-2', 'browser_context_id': 'context-2'},
            {'target_id': 'tab-3', 'browser_context_id': 'context-3'},
        ]
        
        tabs_and_requests = []
        
        with patch('pydoll.browser.tab.ConnectionHandler', return_value=mock_connection_handler):
            for config in tab_configurations:
                tab = Tab(
                    browser=mock_browser,
                    connection_port=9222,
                    **config
                )
                request = tab.request
                tabs_and_requests.append((tab, request))
        
        # Each tab should have its own request instance
        for i, (tab, request) in enumerate(tabs_and_requests):
            assert isinstance(request, Request)
            assert request.tab is tab
            
            # Compare with other tabs
            for j, (other_tab, other_request) in enumerate(tabs_and_requests):
                if i != j:
                    assert request is not other_request
                    assert tab is not other_tab