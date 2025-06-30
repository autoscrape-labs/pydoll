"""Tests for protocol params classes."""

from typing import get_type_hints
from pydoll.protocol.base import CommandParams


def test_runtime_params():
    """Test Runtime params imports and basic structure."""
    from pydoll.protocol.runtime.params import (
        EvaluateParams, CallFunctionOnParams, GetPropertiesParams,
        AddBindingParams, RemoveBindingParams
    )
    
    # Test that params can be instantiated
    eval_params = EvaluateParams(expression="console.log('test')")
    call_params = CallFunctionOnParams(functionDeclaration="function() { return 42; }")
    get_props = GetPropertiesParams(objectId="test-id")
    add_binding = AddBindingParams(name="testBinding")
    remove_binding = RemoveBindingParams(name="testBinding")
    
    # Test required fields are present
    assert eval_params['expression'] == "console.log('test')"
    assert call_params['functionDeclaration'] == "function() { return 42; }"
    assert get_props['objectId'] == "test-id"
    assert add_binding['name'] == "testBinding"
    assert remove_binding['name'] == "testBinding"


def test_page_params():
    """Test Page params imports and basic structure."""
    from pydoll.protocol.page.params import (
        NavigateParams, ReloadParams, CaptureScreenshotParams,
        SetDocumentContentParams, PrintToPDFParams
    )
    
    # Test basic instantiation
    nav_params = NavigateParams(url="https://example.com")
    reload_params = ReloadParams()
    screenshot_params = CaptureScreenshotParams()
    set_content = SetDocumentContentParams(frameId="frame1", html="<html></html>")
    pdf_params = PrintToPDFParams()
    
    # Test that instances are dict-like
    assert isinstance(nav_params, dict)
    assert isinstance(reload_params, dict)
    assert isinstance(screenshot_params, dict)
    assert isinstance(set_content, dict)
    assert isinstance(pdf_params, dict)


def test_network_params():
    """Test Network params imports and basic structure."""
    from pydoll.protocol.network.params import (
        GetCookiesParams, SetCookiesParams, DeleteCookiesParams,
        SetUserAgentOverrideParams
    )
    
    # Test basic instantiation
    get_cookies = GetCookiesParams()
    set_cookies = SetCookiesParams(cookies=[])
    delete_cookies = DeleteCookiesParams(name="testCookie")
    set_user_agent = SetUserAgentOverrideParams(userAgent="Custom Agent")
    
    # Test that instances are dict-like
    assert isinstance(get_cookies, dict)
    assert isinstance(set_cookies, dict)
    assert isinstance(delete_cookies, dict)
    assert isinstance(set_user_agent, dict)


def test_dom_params():
    """Test DOM params imports and basic structure."""
    from pydoll.protocol.dom.params import (
        GetDocumentParams, QuerySelectorParams, QuerySelectorAllParams,
        SetAttributeValueParams, RemoveNodeParams
    )
    
    # Test basic instantiation
    get_doc = GetDocumentParams()
    query_selector = QuerySelectorParams(nodeId=1, selector="div")
    query_all = QuerySelectorAllParams(nodeId=1, selector="div")
    set_attr = SetAttributeValueParams(nodeId=1, name="class", value="test")
    remove_node = RemoveNodeParams(nodeId=1)
    
    # Test that instances are dict-like
    assert isinstance(get_doc, dict)
    assert isinstance(query_selector, dict)
    assert isinstance(query_all, dict)
    assert isinstance(set_attr, dict)
    assert isinstance(remove_node, dict)


def test_input_params():
    """Test Input params imports and basic structure."""
    from pydoll.protocol.input.params import (
        DispatchKeyEventParams, DispatchMouseEventParams,
        InsertTextParams
    )
    
    # Test basic instantiation (using proper enum values)
    insert_text = InsertTextParams(text="Hello World")
    
    # Test that instances are dict-like
    assert isinstance(insert_text, dict)


def test_fetch_params():
    """Test Fetch params imports and basic structure."""
    from pydoll.protocol.fetch.params import (
        FailRequestParams, FulfillRequestParams,
        ContinueRequestParams, GetResponseBodyParams
    )
    
    # Test basic instantiation
    continue_req = ContinueRequestParams(requestId="req1")
    get_body = GetResponseBodyParams(requestId="req1")
    
    # Test that instances are dict-like
    assert isinstance(continue_req, dict)
    assert isinstance(get_body, dict)


def test_storage_params():
    """Test Storage params imports and basic structure."""
    from pydoll.protocol.storage.params import (
        ClearCookiesParams, GetCookiesParams, SetCookiesParams,
        ClearDataForOriginParams, GetUsageAndQuotaParams
    )
    
    # Test instantiation
    clear_cookies = ClearCookiesParams()
    get_cookies = GetCookiesParams()
    set_cookies = SetCookiesParams(cookies=[])
    clear_data = ClearDataForOriginParams(origin="https://example.com", storageTypes="all")
    get_usage = GetUsageAndQuotaParams(origin="https://example.com")
    
    # Test required fields
    assert set_cookies['cookies'] == []
    assert clear_data['origin'] == "https://example.com"
    assert clear_data['storageTypes'] == "all"
    assert get_usage['origin'] == "https://example.com"


def test_target_params():
    """Test Target params imports and basic structure."""
    from pydoll.protocol.target.params import (
        ActivateTargetParams, AttachToTargetParams, CloseTargetParams,
        CreateTargetParams, GetTargetsParams, SetDiscoverTargetsParams
    )
    
    # Test instantiation
    activate = ActivateTargetParams(targetId="target1")
    attach = AttachToTargetParams(targetId="target1")
    close = CloseTargetParams(targetId="target1")
    create = CreateTargetParams(url="https://example.com")
    get_targets = GetTargetsParams()
    discover = SetDiscoverTargetsParams(discover=True)
    
    # Test required fields
    assert activate['targetId'] == "target1"
    assert attach['targetId'] == "target1"
    assert close['targetId'] == "target1"
    assert create['url'] == "https://example.com"
    assert discover['discover'] is True


def test_params_are_typeddict():
    """Test that all params classes are properly typed."""
    from pydoll.protocol.runtime.params import EvaluateParams
    from pydoll.protocol.page.params import NavigateParams
    
    # Test that we can get type hints (indicating proper TypedDict structure)
    eval_hints = get_type_hints(EvaluateParams)
    nav_hints = get_type_hints(NavigateParams)
    
    # Should have at least some fields
    assert len(eval_hints) > 0, "EvaluateParams should have type hints"
    assert len(nav_hints) > 0, "NavigateParams should have type hints"
    
    # Test specific required fields
    assert 'expression' in eval_hints, "EvaluateParams should have 'expression' field"
    assert 'url' in nav_hints, "NavigateParams should have 'url' field"


def test_params_instantiation():
    """Test that params can be instantiated properly."""
    from pydoll.protocol.runtime.params import EvaluateParams
    from pydoll.protocol.page.params import NavigateParams
    
    # Test basic instantiation
    eval_params = EvaluateParams(expression="console.log('test')")
    nav_params = NavigateParams(url="https://example.com")
    
    # Should be dict-like
    assert isinstance(eval_params, dict)
    assert isinstance(nav_params, dict)
    
    # Test that we can create them with required fields
    assert len(eval_params) > 0
    assert len(nav_params) > 0


def test_command_params_base():
    """Test the base CommandParams class."""
    # Test instantiation
    base_params = CommandParams()
    assert isinstance(base_params, dict) 