"""Tests for all protocol methods enums."""

from pydoll.protocol.browser.methods import BrowserMethod
from pydoll.protocol.dom.methods import DomMethod
from pydoll.protocol.fetch.methods import FetchMethod
from pydoll.protocol.input.methods import InputMethod
from pydoll.protocol.network.methods import NetworkMethod
from pydoll.protocol.page.methods import PageMethod
from pydoll.protocol.runtime.methods import RuntimeMethod
from pydoll.protocol.storage.methods import StorageMethod
from pydoll.protocol.target.methods import TargetMethod


def test_browser_methods():
    """Test key BrowserMethod enum values."""
    assert BrowserMethod.CLOSE == 'Browser.close'
    assert BrowserMethod.GET_VERSION == 'Browser.getVersion'
    assert BrowserMethod.RESET_PERMISSIONS == 'Browser.resetPermissions'
    assert BrowserMethod.GRANT_PERMISSIONS == 'Browser.grantPermissions'
    assert BrowserMethod.SET_PERMISSION == 'Browser.setPermission'


def test_dom_methods():
    """Test key DomMethod enum values."""
    assert DomMethod.DESCRIBE_NODE == 'DOM.describeNode'
    assert DomMethod.DISABLE == 'DOM.disable'
    assert DomMethod.ENABLE == 'DOM.enable'
    assert DomMethod.FOCUS == 'DOM.focus'
    assert DomMethod.GET_ATTRIBUTES == 'DOM.getAttributes'
    assert DomMethod.GET_BOX_MODEL == 'DOM.getBoxModel'
    assert DomMethod.GET_DOCUMENT == 'DOM.getDocument'
    assert DomMethod.GET_NODE_FOR_LOCATION == 'DOM.getNodeForLocation'
    assert DomMethod.GET_OUTER_HTML == 'DOM.getOuterHTML'
    assert DomMethod.HIDE_HIGHLIGHT == 'DOM.hideHighlight'
    assert DomMethod.HIGHLIGHT_NODE == 'DOM.highlightNode'
    assert DomMethod.HIGHLIGHT_RECT == 'DOM.highlightRect'
    assert DomMethod.MOVE_TO == 'DOM.moveTo'
    assert DomMethod.QUERY_SELECTOR == 'DOM.querySelector'
    assert DomMethod.QUERY_SELECTOR_ALL == 'DOM.querySelectorAll'
    assert DomMethod.REMOVE_ATTRIBUTE == 'DOM.removeAttribute'
    assert DomMethod.REMOVE_NODE == 'DOM.removeNode'
    assert DomMethod.REQUEST_CHILD_NODES == 'DOM.requestChildNodes'
    assert DomMethod.REQUEST_NODE == 'DOM.requestNode'
    assert DomMethod.RESOLVE_NODE == 'DOM.resolveNode'
    assert DomMethod.SCROLL_INTO_VIEW_IF_NEEDED == 'DOM.scrollIntoViewIfNeeded'
    assert DomMethod.SET_ATTRIBUTES_AS_TEXT == 'DOM.setAttributesAsText'
    assert DomMethod.SET_ATTRIBUTE_VALUE == 'DOM.setAttributeValue'
    assert DomMethod.SET_FILE_INPUT_FILES == 'DOM.setFileInputFiles'
    assert DomMethod.SET_NODE_NAME == 'DOM.setNodeName'
    assert DomMethod.SET_NODE_VALUE == 'DOM.setNodeValue'
    assert DomMethod.SET_OUTER_HTML == 'DOM.setOuterHTML'


def test_fetch_methods():
    """Test key FetchMethod enum values."""
    assert FetchMethod.DISABLE == 'Fetch.disable'
    assert FetchMethod.ENABLE == 'Fetch.enable'
    assert FetchMethod.FAIL_REQUEST == 'Fetch.failRequest'
    assert FetchMethod.FULFILL_REQUEST == 'Fetch.fulfillRequest'
    assert FetchMethod.CONTINUE_REQUEST == 'Fetch.continueRequest'
    assert FetchMethod.CONTINUE_WITH_AUTH == 'Fetch.continueWithAuth'
    assert FetchMethod.GET_RESPONSE_BODY == 'Fetch.getResponseBody'


def test_input_methods():
    """Test key InputMethod enum values."""
    assert InputMethod.DISPATCH_KEY_EVENT == 'Input.dispatchKeyEvent'
    assert InputMethod.DISPATCH_MOUSE_EVENT == 'Input.dispatchMouseEvent'
    assert InputMethod.DISPATCH_TOUCH_EVENT == 'Input.dispatchTouchEvent'
    assert InputMethod.INSERT_TEXT == 'Input.insertText'
    assert InputMethod.SET_IGNORE_INPUT_EVENTS == 'Input.setIgnoreInputEvents'


def test_network_methods():
    """Test key NetworkMethod enum values."""
    assert NetworkMethod.DISABLE == 'Network.disable'
    assert NetworkMethod.ENABLE == 'Network.enable'
    assert NetworkMethod.GET_COOKIES == 'Network.getCookies'
    assert NetworkMethod.SET_COOKIES == 'Network.setCookies'
    assert NetworkMethod.DELETE_COOKIES == 'Network.deleteCookies'
    assert NetworkMethod.CLEAR_BROWSER_CACHE == 'Network.clearBrowserCache'
    assert NetworkMethod.CLEAR_BROWSER_COOKIES == 'Network.clearBrowserCookies'
    assert NetworkMethod.SET_USER_AGENT_OVERRIDE == 'Network.setUserAgentOverride'


def test_page_methods():
    """Test key PageMethod enum values."""
    assert PageMethod.ENABLE == 'Page.enable'
    assert PageMethod.DISABLE == 'Page.disable'
    assert PageMethod.NAVIGATE == 'Page.navigate'
    assert PageMethod.RELOAD == 'Page.reload'
    assert PageMethod.GET_FRAME_TREE == 'Page.getFrameTree'
    assert PageMethod.CAPTURE_SCREENSHOT == 'Page.captureScreenshot'
    assert PageMethod.PRINT_TO_PDF == 'Page.printToPDF'


def test_runtime_methods():
    """Test key RuntimeMethod enum values."""
    assert RuntimeMethod.ADD_BINDING == 'Runtime.addBinding'
    assert RuntimeMethod.AWAIT_PROMISE == 'Runtime.awaitPromise'
    assert RuntimeMethod.CALL_FUNCTION_ON == 'Runtime.callFunctionOn'
    assert RuntimeMethod.COMPILE_SCRIPT == 'Runtime.compileScript'
    assert RuntimeMethod.DISABLE == 'Runtime.disable'
    assert RuntimeMethod.DISCARD_CONSOLE_ENTRIES == 'Runtime.discardConsoleEntries'
    assert RuntimeMethod.ENABLE == 'Runtime.enable'
    assert RuntimeMethod.EVALUATE == 'Runtime.evaluate'
    assert RuntimeMethod.GET_PROPERTIES == 'Runtime.getProperties'
    assert RuntimeMethod.GLOBAL_LEXICAL_SCOPE_NAMES == 'Runtime.globalLexicalScopeNames'
    assert RuntimeMethod.QUERY_OBJECTS == 'Runtime.queryObjects'
    assert RuntimeMethod.RELEASE_OBJECT == 'Runtime.releaseObject'
    assert RuntimeMethod.RELEASE_OBJECT_GROUP == 'Runtime.releaseObjectGroup'
    assert RuntimeMethod.REMOVE_BINDING == 'Runtime.removeBinding'
    assert RuntimeMethod.RUN_IF_WAITING_FOR_DEBUGGER == 'Runtime.runIfWaitingForDebugger'
    assert RuntimeMethod.RUN_SCRIPT == 'Runtime.runScript'
    assert RuntimeMethod.SET_ASYNC_CALL_STACK_DEPTH == 'Runtime.setAsyncCallStackDepth'
    assert RuntimeMethod.GET_EXCEPTION_DETAILS == 'Runtime.getExceptionDetails'
    assert RuntimeMethod.GET_HEAP_USAGE == 'Runtime.getHeapUsage'
    assert RuntimeMethod.GET_ISOLATE_ID == 'Runtime.getIsolateId'
    assert RuntimeMethod.SET_CUSTOM_OBJECT_FORMATTER_ENABLED == 'Runtime.setCustomObjectFormatterEnabled'
    assert RuntimeMethod.SET_MAX_CALL_STACK_SIZE_TO_CAPTURE == 'Runtime.setMaxCallStackSizeToCapture'
    assert RuntimeMethod.TERMINATE_EXECUTION == 'Runtime.terminateExecution'


def test_storage_methods():
    """Test key StorageMethod enum values."""
    assert StorageMethod.CLEAR_COOKIES == 'Storage.clearCookies'
    assert StorageMethod.GET_COOKIES == 'Storage.getCookies'
    assert StorageMethod.SET_COOKIES == 'Storage.setCookies'
    assert StorageMethod.CLEAR_DATA_FOR_ORIGIN == 'Storage.clearDataForOrigin'
    assert StorageMethod.GET_USAGE_AND_QUOTA == 'Storage.getUsageAndQuota'


def test_target_methods():
    """Test key TargetMethod enum values."""
    assert TargetMethod.ACTIVATE_TARGET == 'Target.activateTarget'
    assert TargetMethod.ATTACH_TO_TARGET == 'Target.attachToTarget'
    assert TargetMethod.CLOSE_TARGET == 'Target.closeTarget'
    assert TargetMethod.CREATE_TARGET == 'Target.createTarget'
    assert TargetMethod.GET_TARGETS == 'Target.getTargets'
    assert TargetMethod.SET_DISCOVER_TARGETS == 'Target.setDiscoverTargets'


def test_method_enums_integrity():
    """Test that all method enums are properly structured."""
    from enum import Enum
    
    method_classes = [
        BrowserMethod, DomMethod, FetchMethod, InputMethod, NetworkMethod,
        PageMethod, RuntimeMethod, StorageMethod, TargetMethod
    ]
    
    # Map class names to their correct domain prefixes
    domain_mapping = {
        'BrowserMethod': 'Browser',
        'DomMethod': 'DOM',
        'FetchMethod': 'Fetch',
        'InputMethod': 'Input',
        'NetworkMethod': 'Network',
        'PageMethod': 'Page',
        'RuntimeMethod': 'Runtime',
        'StorageMethod': 'Storage',
        'TargetMethod': 'Target'
    }
    
    for method_class in method_classes:
        # Test that enum has at least one value
        assert len(list(method_class)) > 0, f"{method_class.__name__} should have at least one method"
        
        # Test that class is an Enum
        assert issubclass(method_class, Enum), f"{method_class.__name__} should inherit from Enum"
        
        # Check that all values are strings and follow naming convention
        for method in method_class:
            assert isinstance(method.value, str), f"{method_class.__name__}.{method.name} should be a string"
            
            # Check that all values start with the correct domain prefix
            domain_name = domain_mapping[method_class.__name__]
            assert method.value.startswith(f'{domain_name}.'), \
                f"{method_class.__name__}.{method.name} should start with '{domain_name}.'"
            
            # Method values should contain exactly one dot (domain.method)
            dot_count = method.value.count('.')
            assert dot_count == 1, f"{method_class.__name__}.{method.name} should contain exactly one dot"


def test_all_method_enums_unique():
    """Test that all method values are unique across all enums."""
    all_methods = []
    method_classes = [
        BrowserMethod, DomMethod, FetchMethod, InputMethod, NetworkMethod,
        PageMethod, RuntimeMethod, StorageMethod, TargetMethod
    ]
    
    for method_class in method_classes:
        for method in method_class:
            all_methods.append(method.value)
    
    # Check for duplicates
    unique_methods = set(all_methods)
    assert len(unique_methods) == len(all_methods), \
        f"Found {len(all_methods) - len(unique_methods)} duplicate method values"


def test_method_enums_string_behavior():
    """Test that all method enums behave like strings."""
    method_classes = [
        BrowserMethod, DomMethod, FetchMethod, InputMethod, NetworkMethod,
        PageMethod, RuntimeMethod, StorageMethod, TargetMethod
    ]
    
    for method_class in method_classes:
        # Check that instances are strings
        for method in method_class:
            assert isinstance(method, str), f"{method_class.__name__} instances should be strings"
            # Test string operations work
            assert len(method) > 0, f"{method_class.__name__} values should have length > 0"
            assert '.' in method, f"{method_class.__name__} values should contain a dot" 