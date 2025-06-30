"""Tests for protocol types and responses."""

from typing import get_type_hints


def test_runtime_types():
    """Test Runtime types imports and basic structure."""
    from pydoll.protocol.runtime.types import (
        PropertyPreview, CallArgument, RemoteObject
    )
    
    # Test that types can be imported
    assert PropertyPreview is not None
    assert CallArgument is not None
    assert RemoteObject is not None
    
    # Test type hints availability
    preview_hints = get_type_hints(PropertyPreview)
    arg_hints = get_type_hints(CallArgument)
    obj_hints = get_type_hints(RemoteObject)
    
    # Should have type annotations
    assert len(preview_hints) > 0
    assert len(arg_hints) > 0
    assert len(obj_hints) > 0


def test_page_types():
    """Test Page types imports and basic structure."""
    from pydoll.protocol.page.types import (
        Frame, FrameTree, Viewport
    )
    
    # Test that types can be imported
    assert Frame is not None
    assert FrameTree is not None
    assert Viewport is not None


def test_network_types():
    """Test Network types imports and basic structure."""
    from pydoll.protocol.network.types import (
        ResourceType, Cookie, Request, Response
    )
    
    # Test that types can be imported
    assert ResourceType is not None
    assert Cookie is not None
    assert Request is not None
    assert Response is not None


def test_dom_types():
    """Test DOM types imports and basic structure."""
    from pydoll.protocol.dom.types import (
        Node, Rect
    )
    
    # Test that types can be imported
    assert Node is not None
    assert Rect is not None


def test_target_types():
    """Test Target types imports and basic structure."""
    from pydoll.protocol.target.types import (
        TargetInfo, RemoteLocation
    )
    
    # Test that types can be imported
    assert TargetInfo is not None
    assert RemoteLocation is not None
    
    # Test type structure
    target_hints = get_type_hints(TargetInfo)
    location_hints = get_type_hints(RemoteLocation)
    
    assert len(target_hints) > 0
    assert len(location_hints) > 0


def test_runtime_responses():
    """Test Runtime response types."""
    from pydoll.protocol.runtime.responses import (
        EvaluateResponse, CallFunctionOnResponse, GetPropertiesResponse,
        CompileScriptResponse, AwaitPromiseResponse
    )
    
    # Test that response types can be imported
    assert EvaluateResponse is not None
    assert CallFunctionOnResponse is not None
    assert GetPropertiesResponse is not None
    assert CompileScriptResponse is not None
    assert AwaitPromiseResponse is not None
    
    # Test type structure
    eval_hints = get_type_hints(EvaluateResponse)
    call_hints = get_type_hints(CallFunctionOnResponse)
    
    assert len(eval_hints) > 0
    assert len(call_hints) > 0


def test_page_responses():
    """Test Page response types."""
    from pydoll.protocol.page.responses import (
        NavigateResponse, CaptureScreenshotResponse, PrintToPDFResponse,
        GetFrameTreeResponse, CreateIsolatedWorldResponse
    )
    
    # Test that response types can be imported
    assert NavigateResponse is not None
    assert CaptureScreenshotResponse is not None
    assert PrintToPDFResponse is not None
    assert GetFrameTreeResponse is not None
    assert CreateIsolatedWorldResponse is not None


def test_network_responses():
    """Test Network response types."""
    from pydoll.protocol.network.responses import (
        GetCookiesResponse, GetResponseBodyResponse,
        SetCookieResponse, GetCertificateResponse
    )
    
    # Test that response types can be imported
    assert GetCookiesResponse is not None
    assert GetResponseBodyResponse is not None
    assert SetCookieResponse is not None
    assert GetCertificateResponse is not None


def test_dom_responses():
    """Test DOM response types."""
    from pydoll.protocol.dom.responses import (
        GetDocumentResponse, QuerySelectorResponse, QuerySelectorAllResponse,
        DescribeNodeResponse, GetBoxModelResponse
    )
    
    # Test that response types can be imported
    assert GetDocumentResponse is not None
    assert QuerySelectorResponse is not None
    assert QuerySelectorAllResponse is not None
    assert DescribeNodeResponse is not None
    assert GetBoxModelResponse is not None


def test_target_responses():
    """Test Target response types."""
    from pydoll.protocol.target.responses import (
        CreateTargetResponse, GetTargetsResponse, AttachToTargetResponse,
        CreateBrowserContextResponse, GetBrowserContextsResponse
    )
    
    # Test that response types can be imported
    assert CreateTargetResponse is not None
    assert GetTargetsResponse is not None
    assert AttachToTargetResponse is not None
    assert CreateBrowserContextResponse is not None
    assert GetBrowserContextsResponse is not None


def test_storage_types_and_responses():
    """Test Storage types and responses."""
    from pydoll.protocol.storage.types import (
        StorageBucket, TrustToken, UsageForType
    )
    from pydoll.protocol.storage.responses import (
        GetCookiesResponse, GetUsageAndQuotaResponse, ClearTrustTokensResponse
    )
    
    # Test types
    assert StorageBucket is not None
    assert TrustToken is not None
    assert UsageForType is not None
    
    # Test responses
    assert GetCookiesResponse is not None
    assert GetUsageAndQuotaResponse is not None
    assert ClearTrustTokensResponse is not None


def test_fetch_types_and_responses():
    """Test Fetch types and responses."""
    from pydoll.protocol.fetch.responses import (
        GetResponseBodyResponse
    )
    
    # Test responses
    assert GetResponseBodyResponse is not None


def test_input_types():
    """Test Input types imports."""
    from pydoll.protocol.input.types import (
        TouchPoint
    )
    
    # Test that types can be imported
    assert TouchPoint is not None


def test_types_are_structured():
    """Test that types follow proper structure patterns."""
    from pydoll.protocol.runtime.types import RemoteObject
    from pydoll.protocol.page.types import Frame
    from pydoll.protocol.network.types import Cookie
    
    # Test that we can get type hints (indicating proper TypedDict structure)
    obj_hints = get_type_hints(RemoteObject)
    frame_hints = get_type_hints(Frame)
    cookie_hints = get_type_hints(Cookie)
    
    # Should have meaningful fields
    assert len(obj_hints) > 0, "RemoteObject should have type annotations"
    assert len(frame_hints) > 0, "Frame should have type annotations"
    assert len(cookie_hints) > 0, "Cookie should have type annotations"


def test_responses_have_proper_structure():
    """Test that responses have proper structure."""
    from pydoll.protocol.runtime.responses import EvaluateResponse
    from pydoll.protocol.page.responses import NavigateResponse
    
    # Test that responses have type hints
    eval_hints = get_type_hints(EvaluateResponse)
    nav_hints = get_type_hints(NavigateResponse)
    
    # Should have meaningful structure
    assert len(eval_hints) > 0, "EvaluateResponse should have type annotations"
    assert len(nav_hints) > 0, "NavigateResponse should have type annotations" 