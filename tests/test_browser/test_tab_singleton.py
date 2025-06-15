"""
Tests for Tab singleton pattern based on target_id.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from pydoll.browser.tab import Tab


class TestTabSingleton:
    """Tests for Tab singleton behavior."""

    def setup_method(self):
        """Clear instance registry before each test."""
        Tab._instances.clear()

    def teardown_method(self):
        """Clear instance registry after each test."""
        Tab._instances.clear()

    def test_same_target_id_returns_same_instance(self):
        """Test that same target_id returns the same instance."""
        # Arrange
        browser = Mock()
        connection_port = 9222
        target_id = "target-123"
        browser_context_id = "context-456"

        # Act
        tab1 = Tab(browser, connection_port, target_id, browser_context_id)
        tab2 = Tab(browser, connection_port, target_id, browser_context_id)

        # Assert
        assert tab1 is tab2
        assert tab1._target_id == target_id
        assert tab2._target_id == target_id

    def test_different_target_ids_return_different_instances(self):
        """Test that different target_ids return different instances."""
        # Arrange
        browser = Mock()
        connection_port = 9222
        target_id1 = "target-123"
        target_id2 = "target-456"

        # Act
        tab1 = Tab(browser, connection_port, target_id1)
        tab2 = Tab(browser, connection_port, target_id2)

        # Assert
        assert tab1 is not tab2
        assert tab1._target_id == target_id1
        assert tab2._target_id == target_id2

    def test_get_instance_returns_existing_instance(self):
        """Test that get_instance returns existing instance."""
        # Arrange
        browser = Mock()
        connection_port = 9222
        target_id = "target-123"

        # Act
        tab = Tab(browser, connection_port, target_id)
        retrieved_tab = Tab.get_instance(target_id)

        # Assert
        assert retrieved_tab is tab

    def test_get_instance_returns_none_for_nonexistent_target(self):
        """Test that get_instance returns None for non-existent target_id."""
        # Act
        retrieved_tab = Tab.get_instance("nonexistent-target")

        # Assert
        assert retrieved_tab is None

    def test_get_all_instances_returns_all_active_instances(self):
        """Test that get_all_instances returns all active instances."""
        # Arrange
        browser = Mock()
        connection_port = 9222
        target_id1 = "target-123"
        target_id2 = "target-456"

        # Act
        tab1 = Tab(browser, connection_port, target_id1)
        tab2 = Tab(browser, connection_port, target_id2)
        all_instances = Tab.get_all_instances()

        # Assert
        assert len(all_instances) == 2
        assert all_instances[target_id1] is tab1
        assert all_instances[target_id2] is tab2

    def test_remove_instance_removes_from_registry(self):
        """Test that _remove_instance removes instance from registry."""
        # Arrange
        browser = Mock()
        connection_port = 9222
        target_id = "target-123"

        # Act
        tab = Tab(browser, connection_port, target_id)
        assert Tab.get_instance(target_id) is tab

        Tab._remove_instance(target_id)
        retrieved_tab = Tab.get_instance(target_id)

        # Assert
        assert retrieved_tab is None
        assert len(Tab.get_all_instances()) == 0

    @pytest.mark.asyncio
    async def test_close_removes_instance_from_registry(self):
        """Test that close() removes instance from registry."""
        # Arrange
        browser = Mock()
        connection_port = 9222
        target_id = "target-123"
        
        tab = Tab(browser, connection_port, target_id)
        tab._execute_command = AsyncMock(return_value={'result': 'success'})

        # Verify instance is in registry
        assert Tab.get_instance(target_id) is tab

        # Act
        await tab.close()

        # Assert
        assert Tab.get_instance(target_id) is None
        assert len(Tab.get_all_instances()) == 0

    def test_existing_instance_properties_are_updated(self):
        """Test that existing instance properties are updated."""
        # Arrange
        browser1 = Mock()
        browser2 = Mock()
        connection_port1 = 9222
        connection_port2 = 9223
        target_id = "target-123"
        context1 = "context-1"
        context2 = "context-2"

        # Act
        tab1 = Tab(browser1, connection_port1, target_id, context1)
        tab2 = Tab(browser2, connection_port2, target_id, context2)

        # Assert
        assert tab1 is tab2
        assert tab1._browser is browser2  # Updated
        assert tab1._connection_port == connection_port2  # Updated
        assert tab1._browser_context_id == context2  # Updated

    def test_initialization_is_skipped_for_existing_instance(self):
        """Test that __init__ is skipped for existing instances."""
        # Arrange
        browser = Mock()
        connection_port = 9222
        target_id = "target-123"

        # Act
        tab1 = Tab(browser, connection_port, target_id)
        original_initialized = tab1._initialized
        
        # Modify a property to verify __init__ is not executed again
        tab1._page_events_enabled = True
        
        tab2 = Tab(browser, connection_port, target_id)

        # Assert
        assert tab1 is tab2
        assert tab1._initialized == original_initialized
        assert tab1._page_events_enabled is True  # Not reset

    def test_remove_nonexistent_instance_does_not_raise_error(self):
        """Test that removing non-existent instance does not raise error."""
        # Act & Assert - should not raise exception
        Tab._remove_instance("nonexistent-target") 