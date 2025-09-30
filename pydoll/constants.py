from enum import Enum, auto


class By(str, Enum):
    CSS_SELECTOR = 'css'
    XPATH = 'xpath'
    CLASS_NAME = 'class_name'
    ID = 'id'
    TAG_NAME = 'tag_name'
    NAME = 'name'


class PageLoadState(str, Enum):
    COMPLETE = 'complete'
    INTERACTIVE = 'interactive'


class Scripts:
    ELEMENT_VISIBLE = """
    function() {
        const rect = this.getBoundingClientRect();
        return (
            rect.width > 0 && rect.height > 0
            && getComputedStyle(this).visibility !== 'hidden'
            && getComputedStyle(this).display !== 'none'
        )
    }
    """

    ELEMENT_ON_TOP = """
    function() {
        const rect = this.getBoundingClientRect();
        const x = rect.x + rect.width / 2;
        const y = rect.y + rect.height / 2;
        const elementFromPoint = document.elementFromPoint(x, y);
        if (!elementFromPoint) {
            return false;
        }
        return elementFromPoint === this || this.contains(elementFromPoint);
    }
    """

    ELEMENT_INTERACTIVE = """
    function() {
        const style = window.getComputedStyle(this);
        const rect = this.getBoundingClientRect();
        if (
            rect.width <= 0 ||
            rect.height <= 0 ||
            style.visibility === 'hidden' ||
            style.display === 'none' ||
            style.pointerEvents === 'none'
        ) {
            return false;
        }
        const x = rect.x + rect.width / 2;
        const y = rect.y + rect.height / 2;
        const elementFromPoint = document.elementFromPoint(x, y);
        if (!elementFromPoint || (elementFromPoint !== this && !this.contains(elementFromPoint))) {
            return false;
        }
        if (this.disabled) {
            return false;
        }
        return true;
    }
    """

    CLICK = """
    function(){
        clicked = false;
        this.addEventListener('click', function(){
            clicked = true;
        });
        this.click();
        return clicked;
    }
    """

    CLICK_OPTION_TAG = """
    function() {
    this.selected = true;
    var select = this.parentElement.closest('select');
    var event = new Event('change', { bubbles: true });
    select.dispatchEvent(event);
    }
    """

    BOUNDS = """
    function() {
        return JSON.stringify(this.getBoundingClientRect());
    }
    """

    FIND_RELATIVE_XPATH_ELEMENT = """
        function() {
            return document.evaluate(
                "{escaped_value}", this, null,
                XPathResult.FIRST_ORDERED_NODE_TYPE, null
            ).singleNodeValue;
        }
    """

    FIND_XPATH_ELEMENT = """
        var element = document.evaluate(
            "{escaped_value}", document, null,
            XPathResult.FIRST_ORDERED_NODE_TYPE, null
        ).singleNodeValue;
        element;
    """

    FIND_RELATIVE_XPATH_ELEMENTS = """
        function() {
            var elements = document.evaluate(
                "{escaped_value}", this, null,
                XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null
            );
            var results = [];
            for (var i = 0; i < elements.snapshotLength; i++) {
                results.push(elements.snapshotItem(i));
            }
            return results;
        }
    """

    FIND_XPATH_ELEMENTS = """
        var elements = document.evaluate(
            "{escaped_value}", document, null,
            XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null
        );
        var results = [];
        for (var i = 0; i < elements.snapshotLength; i++) {
            results.push(elements.snapshotItem(i));
        }
        results;
    """

    QUERY_SELECTOR = 'document.querySelector("{selector}");'

    RELATIVE_QUERY_SELECTOR = """
        function() {
            return this.querySelector("{selector}");
        }
    """

    QUERY_SELECTOR_ALL = 'document.querySelectorAll("{selector}");'

    RELATIVE_QUERY_SELECTOR_ALL = """
        function() {
            return this.querySelectorAll("{selector}");
        }
    """

    GET_PARENT_NODE = """
        function() {
            return this.parentElement;
        }
    """

    GET_CHILDREN_NODE = """
        function() {{
            function getChildrenUntilDepth(element, maxDepth, tagFilter = [], currentDepth = 1)
            {{
                if (currentDepth > maxDepth) return [];

                const children = Array.from(element.children);
                let filtered = tagFilter.length === 0
                    ? children
                : children.filter(child => tagFilter.includes(child.tagName.toLowerCase()));

                let allDescendants = [...filtered];

                for (let child of children)
                {{
                    allDescendants.push(
                    ...getChildrenUntilDepth(child, maxDepth, tagFilter, currentDepth + 1)
                    );
                }}

                return allDescendants;
            }}

            return getChildrenUntilDepth(this, {max_depth}, {tag_filter});
        }}
    """

    GET_SIBLINGS_NODE = """
        function() {{
            function getSiblingsUntilDepth(element, tagFilter = [])
            {{
                const parent = element.parentElement;
                const siblings = Array.from(parent.children);
                let filtered = tagFilter.length === 0
                    ? siblings.filter(child => child !== element)
                : siblings.filter(child =>
                    tagFilter.includes(child.tagName.toLowerCase()) && child !== element);

                let allDescendants = [...filtered];

                return allDescendants;
            }}

            return getSiblingsUntilDepth(this, {tag_filter});
        }}
    """

    MAKE_REQUEST = """
(async function() {{
    async function makeRequest(url, options) {{
        try {{
            const response = await fetch(url, options, {{
                credentials: 'include',
            }});
            const headers = {{}};
            response.headers.forEach((value, key) => {{
                headers[key] = value;
            }});

            // Extract cookies from set-cookie header
            const cookies = document.cookie;
            let text = await response.text();
            const possiblePrefixes = [")]}}'\\n", ")]}}'\\n", ")]}}\\n"];
            for (let prefix of possiblePrefixes) {{
                if (text.startsWith(prefix)) {{
                    text = text.substring(prefix.length);
                    break;
                }}
            }}
            let content, jsonData;
            const contentType = response.headers.get('content-type') || '';

            if (contentType.includes('application/json')) {{
                try {{
                    jsonData = JSON.parse(text);
                    text = JSON.stringify(jsonData);
                }} catch (e) {{
                    jsonData = null;
                    // Keep original text if parsing fails
                }}
                content = new TextEncoder().encode(text).buffer;
            }} else {{
                // For non-JSON, keep original text handling
                content = new TextEncoder().encode(text).buffer;
                jsonData = null;
            }}

            return {{
                status: response.status,
                ok: response.ok,
                url: response.url,
                headers: headers,
                cookies: cookies,
                content: Array.from(new Uint8Array(content)),
                text: text,
                json: jsonData
            }};
        }} catch (error) {{
            return {{
                error: error.toString(),
                status: 0
            }};
        }}
    }}

    const url = {url};
    const options = {options};
    return await makeRequest(url, options);
}})();
"""


class Key(tuple[str, int], Enum):
    BACKSPACE = ('Backspace', 8)
    TAB = ('Tab', 9)
    ENTER = ('Enter', 13)
    SHIFT = ('Shift', 16)
    CONTROL = ('Control', 17)
    ALT = ('Alt', 18)
    PAUSE = ('Pause', 19)
    CAPSLOCK = ('CapsLock', 20)
    ESCAPE = ('Escape', 27)
    SPACE = ('Space', 32)
    PAGEUP = ('PageUp', 33)
    PAGEDOWN = ('PageDown', 34)
    END = ('End', 35)
    HOME = ('Home', 36)
    ARROWLEFT = ('ArrowLeft', 37)
    ARROWUP = ('ArrowUp', 38)
    ARROWRIGHT = ('ArrowRight', 39)
    ARROWDOWN = ('ArrowDown', 40)
    PRINTSCREEN = ('PrintScreen', 44)
    INSERT = ('Insert', 45)
    DELETE = ('Delete', 46)
    META = ('Meta', 91)
    METARIGHT = ('MetaRight', 92)
    CONTEXTMENU = ('ContextMenu', 93)
    NUMLOCK = ('NumLock', 144)
    SCROLLLOCK = ('ScrollLock', 145)

    F1 = ('F1', 112)
    F2 = ('F2', 113)
    F3 = ('F3', 114)
    F4 = ('F4', 115)
    F5 = ('F5', 116)
    F6 = ('F6', 117)
    F7 = ('F7', 118)
    F8 = ('F8', 119)
    F9 = ('F9', 120)
    F10 = ('F10', 121)
    F11 = ('F11', 122)
    F12 = ('F12', 123)

    SEMICOLON = ('Semicolon', 186)
    EQUALSIGN = ('EqualSign', 187)
    COMMA = ('Comma', 188)
    MINUS = ('Minus', 189)
    PERIOD = ('Period', 190)
    SLASH = ('Slash', 191)
    GRAVEACCENT = ('GraveAccent', 192)
    BRACKETLEFT = ('BracketLeft', 219)
    BACKSLASH = ('Backslash', 220)
    BRACKETRIGHT = ('BracketRight', 221)
    QUOTE = ('Quote', 222)


class BrowserType(Enum):
    CHROME = auto()
    EDGE = auto()
