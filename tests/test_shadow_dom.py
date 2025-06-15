"""
Comprehensive tests for Shadow DOM implementation in pydoll.

Tests cover security features, proper encapsulation, error handling,
and integration with existing CDP infrastructure.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from pydoll.elements.shadow_root import ShadowRoot
from pydoll.elements.web_element import WebElement
from pydoll.connection import ConnectionHandler
from pydoll.exceptions import (
    NoShadowRootAttached,
    InvalidShadowRoot,
    ShadowRootAccessDenied,
    ShadowBoundaryViolation,
    ElementNotFound,
)


class TestShadowRootValidation:
    """Test Shadow DOM validation and security features."""

    def test_shadow_root_initialization_valid_open(self):
        """Test ShadowRoot initialization with valid open mode."""
        connection_handler = MagicMock(spec=ConnectionHandler)
        
        shadow_root = ShadowRoot(
            shadow_root_object_id="shadow-123",
            connection_handler=connection_handler,
            mode="open"
        )
        
        assert shadow_root.mode == "open"
        assert shadow_root.is_open is True
        assert shadow_root.is_closed is False
        assert shadow_root._is_valid is True

    def test_shadow_root_initialization_valid_closed(self):
        """Test ShadowRoot initialization with valid closed mode."""
        connection_handler = MagicMock(spec=ConnectionHandler)
        
        shadow_root = ShadowRoot(
            shadow_root_object_id="shadow-456",
            connection_handler=connection_handler,
            mode="closed"
        )
        
        assert shadow_root.mode == "closed"
        assert shadow_root.is_open is False
        assert shadow_root.is_closed is True

    def test_shadow_root_initialization_invalid_object_id(self):
        """Test ShadowRoot initialization with invalid object ID."""
        connection_handler = MagicMock(spec=ConnectionHandler)
        
        with pytest.raises(InvalidShadowRoot, match="Invalid shadow root object ID"):
            ShadowRoot(
                shadow_root_object_id="",
                connection_handler=connection_handler,
                mode="open"
            )
        
        with pytest.raises(InvalidShadowRoot, match="Invalid shadow root object ID"):
            ShadowRoot(
                shadow_root_object_id=None,
                connection_handler=connection_handler,
                mode="open"
            )

    def test_shadow_root_initialization_invalid_mode(self):
        """Test ShadowRoot initialization with invalid mode."""
        connection_handler = MagicMock(spec=ConnectionHandler)
        
        with pytest.raises(InvalidShadowRoot, match="Invalid shadow root mode"):
            ShadowRoot(
                shadow_root_object_id="shadow-123",
                connection_handler=connection_handler,
                mode="invalid"
            )

    def test_shadow_root_invalidation(self):
        """Test shadow root invalidation mechanism."""
        connection_handler = MagicMock(spec=ConnectionHandler)
        
        shadow_root = ShadowRoot(
            shadow_root_object_id="shadow-123",
            connection_handler=connection_handler,
            mode="open"
        )
        
        assert shadow_root._is_valid is True
        shadow_root.invalidate()
        assert shadow_root._is_valid is False


class TestSelectorSanitization:
    """Test selector sanitization and injection prevention."""
    
    def test_selector_sanitization_valid_css(self):
        """Test sanitization of valid CSS selectors."""
        connection_handler = MagicMock(spec=ConnectionHandler)
        shadow_root = ShadowRoot("shadow-123", connection_handler, "open")
        
        # Valid selectors should pass through
        assert shadow_root._sanitize_selector("button.submit", "css") == "button.submit"
        assert shadow_root._sanitize_selector("#main-form", "css") == "#main-form"
        assert shadow_root._sanitize_selector("div[data-test='value']", "css") == "div[data-test='value']"

    def test_selector_sanitization_dangerous_patterns(self):
        """Test rejection of dangerous selector patterns."""
        connection_handler = MagicMock(spec=ConnectionHandler)
        shadow_root = ShadowRoot("shadow-123", connection_handler, "open")
        
        # Should reject deprecated shadow-piercing selectors
        with pytest.raises(ValueError, match="prohibited pattern"):
            shadow_root._sanitize_selector("div ::shadow button", "css")
            
        with pytest.raises(ValueError, match="prohibited pattern"):
            shadow_root._sanitize_selector("div /deep/ button", "css")
            
        with pytest.raises(ValueError, match="prohibited pattern"):
            shadow_root._sanitize_selector("div >>> button", "css")

    def test_selector_sanitization_empty_invalid(self):
        """Test rejection of empty or invalid selectors."""
        connection_handler = MagicMock(spec=ConnectionHandler)
        shadow_root = ShadowRoot("shadow-123", connection_handler, "open")
        
        with pytest.raises(ValueError, match="non-empty string"):
            shadow_root._sanitize_selector("", "css")
            
        with pytest.raises(ValueError, match="non-empty string"):
            shadow_root._sanitize_selector(None, "css")


class TestShadowRootElementFinding:
    """Test element finding within shadow roots."""
    
    @pytest.mark.asyncio
    async def test_find_element_in_shadow_success(self):
        """Test successful element finding in shadow root."""
        connection_handler = AsyncMock(spec=ConnectionHandler)
        
        # Mock DOM command responses
        connection_handler.execute_command.side_effect = [
            # request_node response
            {"result": {"nodeId": 123}},
            # query_selector response  
            {"result": {"nodeId": 456}},
            # resolve_node response
            {"result": {"object": {"objectId": "element-789"}}}
        ]
        
        shadow_root = ShadowRoot("shadow-123", connection_handler, "open")
        
        element = await shadow_root.find_element_in_shadow("button.submit")
        
        assert isinstance(element, WebElement)
        assert connection_handler.execute_command.call_count == 3

    @pytest.mark.asyncio
    async def test_find_element_in_shadow_not_found(self):
        """Test element not found in shadow root."""
        connection_handler = AsyncMock(spec=ConnectionHandler)
        
        # Mock DOM command responses for element not found
        connection_handler.execute_command.side_effect = [
            # request_node response
            {"result": {"nodeId": 123}},
            # query_selector response (no nodeId = not found)
            {"result": {}}
        ]
        
        shadow_root = ShadowRoot("shadow-123", connection_handler, "open")
        
        with pytest.raises(ElementNotFound):
            await shadow_root.find_element_in_shadow("button.nonexistent")

    @pytest.mark.asyncio
    async def test_find_element_in_shadow_not_found_no_raise(self):
        """Test element not found with raise_exc=False."""
        connection_handler = AsyncMock(spec=ConnectionHandler)
        
        # Mock DOM command responses for element not found
        connection_handler.execute_command.side_effect = [
            # request_node response
            {"result": {"nodeId": 123}},
            # query_selector response (no nodeId = not found)
            {"result": {}}
        ]
        
        shadow_root = ShadowRoot("shadow-123", connection_handler, "open")
        
        element = await shadow_root.find_element_in_shadow(
            "button.nonexistent", 
            raise_exc=False
        )
        
        assert element is None

    @pytest.mark.asyncio
    async def test_find_element_in_shadow_invalidated(self):
        """Test finding element in invalidated shadow root."""
        connection_handler = AsyncMock(spec=ConnectionHandler)
        shadow_root = ShadowRoot("shadow-123", connection_handler, "open")
        
        shadow_root.invalidate()
        
        with pytest.raises(InvalidShadowRoot, match="invalidated"):
            await shadow_root.find_element_in_shadow("button")

    @pytest.mark.asyncio
    async def test_get_shadow_root_content_success(self):
        """Test getting shadow root HTML content."""
        connection_handler = AsyncMock(spec=ConnectionHandler)
        
        # Mock get_outer_html response
        connection_handler.execute_command.return_value = {
            "result": {"outerHTML": "<div>Shadow content</div>"}
        }
        
        shadow_root = ShadowRoot("shadow-123", connection_handler, "open")
        
        content = await shadow_root.get_shadow_root_content()
        
        assert content == "<div>Shadow content</div>"
        assert connection_handler.execute_command.called


class TestWebElementShadowRootAccess:
    """Test WebElement.get_shadow_root() method."""
    
    @pytest.mark.asyncio
    async def test_get_shadow_root_success(self):
        """Test successful shadow root access from WebElement."""
        connection_handler = AsyncMock(spec=ConnectionHandler)
        
        # Mock DOM command responses
        connection_handler.execute_command.side_effect = [
            # describe_node response with shadow root
            {
                "result": {
                    "root": {
                        "shadowRoots": [{
                            "nodeId": 456,
                            "shadowRootType": "open"
                        }]
                    }
                }
            },
            # resolve_node response
            {"result": {"object": {"objectId": "shadow-root-789"}}}
        ]
        
        element = WebElement(
            object_id="element-123",
            connection_handler=connection_handler
        )
        
        shadow_root = await element.get_shadow_root()
        
        assert isinstance(shadow_root, ShadowRoot)
        assert shadow_root.mode == "open"
        assert shadow_root.host_element == element

    @pytest.mark.asyncio
    async def test_get_shadow_root_not_attached(self):
        """Test shadow root access when none is attached."""
        connection_handler = AsyncMock(spec=ConnectionHandler)
        
        # Mock DOM command response with no shadow roots
        connection_handler.execute_command.return_value = {
            "result": {
                "root": {
                    "shadowRoots": []
                }
            }
        }
        
        element = WebElement(
            object_id="element-123",
            connection_handler=connection_handler
        )
        
        # Should return None when no shadow root is attached
        shadow_root = await element.get_shadow_root()
        assert shadow_root is None

    @pytest.mark.asyncio
    async def test_get_shadow_root_missing_node_id(self):
        """Test shadow root access with missing node ID."""
        connection_handler = AsyncMock(spec=ConnectionHandler)
        
        # Mock DOM command response with shadow root but missing nodeId
        connection_handler.execute_command.return_value = {
            "result": {
                "root": {
                    "shadowRoots": [{
                        "shadowRootType": "open"
                        # Missing nodeId
                    }]
                }
            }
        }
        
        element = WebElement(
            object_id="element-123",
            connection_handler=connection_handler
        )
        
        with pytest.raises(ShadowRootAccessDenied, match="no nodeId available"):
            await element.get_shadow_root()


class TestShadowRootSecurityFeatures:
    """Test security features and boundary enforcement."""

    def test_shadow_root_string_representations(self):
        """Test string representations for debugging."""
        connection_handler = MagicMock(spec=ConnectionHandler)
        
        shadow_root = ShadowRoot("shadow-123", connection_handler, "open")
        
        assert "open mode" in str(shadow_root)
        assert "mode=open" in repr(shadow_root)
        assert "valid" in repr(shadow_root)
        
        shadow_root.invalidate()
        assert "invalid" in repr(shadow_root)

    def test_host_element_reference(self):
        """Test host element reference functionality."""
        connection_handler = MagicMock(spec=ConnectionHandler)
        host_element = MagicMock(spec=WebElement)
        
        shadow_root = ShadowRoot(
            "shadow-123", 
            connection_handler, 
            "open",
            host_element=host_element
        )
        
        assert shadow_root.host_element == host_element

    @pytest.mark.asyncio
    async def test_security_boundary_validation(self):
        """Test that security boundaries are properly validated."""
        connection_handler = AsyncMock(spec=ConnectionHandler)
        shadow_root = ShadowRoot("shadow-123", connection_handler, "closed")
        
        # Should still allow access for closed shadow roots if we have object_id
        # (in practice, having the object_id means we have access)
        connection_handler.execute_command.side_effect = [
            {"result": {"nodeId": 123}},
            {"result": {"nodeId": 456}},
            {"result": {"object": {"objectId": "element-789"}}}
        ]
        
        element = await shadow_root.find_element_in_shadow("button")
        assert element is not None


class TestShadowRootIntegration:
    """Integration tests for Shadow DOM features."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_shadow_dom_access(self):
        """Test complete shadow DOM access workflow."""
        connection_handler = AsyncMock(spec=ConnectionHandler)
        
        # Create host element
        host_element = WebElement(
            object_id="host-123",
            connection_handler=connection_handler
        )
        
        # Mock shadow root access
        connection_handler.execute_command.side_effect = [
            # describe_node for getting shadow root
            {
                "result": {
                    "root": {
                        "shadowRoots": [{
                            "nodeId": 456,
                            "shadowRootType": "open"
                        }]
                    }
                }
            },
            # resolve_node for shadow root
            {"result": {"object": {"objectId": "shadow-root-789"}}},
            # request_node for element finding
            {"result": {"nodeId": 456}},
            # query_selector for finding button
            {"result": {"nodeId": 789}},
            # resolve_node for button element
            {"result": {"object": {"objectId": "button-101112"}}}
        ]
        
        # Access shadow root
        shadow_root = await host_element.get_shadow_root()
        assert shadow_root.mode == "open"
        
        # Find element within shadow root
        button = await shadow_root.find_element_in_shadow("button.submit")
        assert isinstance(button, WebElement)
        
        # Verify all expected commands were called
        assert connection_handler.execute_command.call_count == 5

    @pytest.mark.asyncio
    async def test_error_handling_chain(self):
        """Test proper error handling throughout the chain."""
        connection_handler = AsyncMock(spec=ConnectionHandler)
        
        # Simulate command failure
        connection_handler.execute_command.side_effect = Exception("CDP error")
        
        element = WebElement(
            object_id="element-123",
            connection_handler=connection_handler
        )
        
        with pytest.raises(ShadowRootAccessDenied, match="Failed to access shadow root"):
            await element.get_shadow_root() 