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


class ScrollPosition(str, Enum):
    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'


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
        var select = this && this.parentElement ? this.parentElement.closest('select') : null;
        if (!select) { return false; }
        for (var i = 0; i < select.options.length; i++) {
            select.options[i].selected = false;
        }
        this.selected = true;
        select.value = this.value;
        select.dispatchEvent(new Event('input', { bubbles: true }));
        select.dispatchEvent(new Event('change', { bubbles: true }));
        return true;
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

    GET_TEXT_BY_XPATH = """
        (() => {
            const node = document.evaluate(
                "{escaped_value}",
                document,
                null,
                XPathResult.FIRST_ORDERED_NODE_TYPE,
                null
            ).singleNodeValue;
            return node ? (node.textContent || "") : "";
        })()
    """

    GET_TEXT_BY_CSS = """
        (() => {
            const el = document.querySelector("{selector}");
            return el ? (el.textContent || "") : "";
        })()
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

    SCROLL_BY = """
new Promise((resolve) => {{
    const behavior = '{behavior}';
    if (behavior === 'auto') {{
        window.scrollBy({{
            {axis}: {distance},
            behavior: 'auto'
        }});
        resolve();
    }} else {{
        const onScrollEnd = () => {{
            window.removeEventListener('scrollend', onScrollEnd);
            resolve();
        }};
        window.addEventListener('scrollend', onScrollEnd);
        window.scrollBy({{
            {axis}: {distance},
            behavior: 'smooth'
        }});
        setTimeout(() => {{
            window.removeEventListener('scrollend', onScrollEnd);
            resolve();
        }}, 2000);
    }}
}});
"""

    SCROLL_TO_TOP = """
new Promise((resolve) => {{
    const behavior = '{behavior}';
    if (behavior === 'auto') {{
        window.scrollTo({{
            top: 0,
            behavior: 'auto'
        }});
        resolve();
    }} else {{
        const onScrollEnd = () => {{
            window.removeEventListener('scrollend', onScrollEnd);
            resolve();
        }};
        window.addEventListener('scrollend', onScrollEnd);
        window.scrollTo({{
            top: 0,
            behavior: 'smooth'
        }});
        setTimeout(() => {{
            window.removeEventListener('scrollend', onScrollEnd);
            resolve();
        }}, 2000);
    }}
}});
"""

    SCROLL_TO_BOTTOM = """
new Promise((resolve) => {{
    const behavior = '{behavior}';
    if (behavior === 'auto') {{
        window.scrollTo({{
            top: document.body.scrollHeight,
            behavior: 'auto'
        }});
        resolve();
    }} else {{
        const onScrollEnd = () => {{
            window.removeEventListener('scrollend', onScrollEnd);
            resolve();
        }};
        window.addEventListener('scrollend', onScrollEnd);
        window.scrollTo({{
            top: document.body.scrollHeight,
            behavior: 'smooth'
        }});
        setTimeout(() => {{
            window.removeEventListener('scrollend', onScrollEnd);
            resolve();
        }}, 2000);
    }}
}});
"""

    INSERT_TEXT = """
    function() {
        const el = this;
        const text = arguments[0];

        // Standard input/textarea
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
            const start = el.selectionStart || el.value.length;
            const end = el.selectionEnd || el.value.length;
            const before = el.value.substring(0, start);
            const after = el.value.substring(end);
            el.value = before + text + after;
            el.selectionStart = el.selectionEnd = start + text.length;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            return true;
        }

        // ContentEditable elements
        if (el.isContentEditable) {
            el.focus();
            const selection = window.getSelection();
            const range = selection.getRangeAt(0);
            range.deleteContents();
            const textNode = document.createTextNode(text);
            range.insertNode(textNode);
            range.setStartAfter(textNode);
            range.setEndAfter(textNode);
            selection.removeAllRanges();
            selection.addRange(range);
            el.dispatchEvent(new Event('input', { bubbles: true }));
            return true;
        }

        return false;
    }
    """

    IS_EDITABLE = """
    function() {
        const el = this;

        // Check standard input elements
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
            return !el.disabled && !el.readOnly;
        }

        // Check contenteditable (including inherited)
        let current = el;
        while (current) {
            if (current.isContentEditable) {
                return true;
            }
            current = current.parentElement;
        }

        return false;
    }
    """

    IS_OPTION_TAG = """
    function() {
        return !!(this && this.tagName && this.tagName.toLowerCase() === 'option');
    }
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

    DIGIT0 = ('0', 48)
    DIGIT1 = ('1', 49)
    DIGIT2 = ('2', 50)
    DIGIT3 = ('3', 51)
    DIGIT4 = ('4', 52)
    DIGIT5 = ('5', 53)
    DIGIT6 = ('6', 54)
    DIGIT7 = ('7', 55)
    DIGIT8 = ('8', 56)
    DIGIT9 = ('9', 57)

    A = ('A', 65)
    B = ('B', 66)
    C = ('C', 67)
    D = ('D', 68)
    E = ('E', 69)
    F = ('F', 70)
    G = ('G', 71)
    H = ('H', 72)
    I = ('I', 73)  # noqa: E741
    J = ('J', 74)
    K = ('K', 75)
    L = ('L', 76)
    M = ('M', 77)
    N = ('N', 78)
    O = ('O', 79)  # noqa: E741
    P = ('P', 80)
    Q = ('Q', 81)
    R = ('R', 82)
    S = ('S', 83)
    T = ('T', 84)
    U = ('U', 85)
    V = ('V', 86)
    W = ('W', 87)
    X = ('X', 88)
    Y = ('Y', 89)
    Z = ('Z', 90)

    META = ('Meta', 91)
    METARIGHT = ('MetaRight', 92)
    CONTEXTMENU = ('ContextMenu', 93)

    NUMPAD0 = ('Numpad0', 96)
    NUMPAD1 = ('Numpad1', 97)
    NUMPAD2 = ('Numpad2', 98)
    NUMPAD3 = ('Numpad3', 99)
    NUMPAD4 = ('Numpad4', 100)
    NUMPAD5 = ('Numpad5', 101)
    NUMPAD6 = ('Numpad6', 102)
    NUMPAD7 = ('Numpad7', 103)
    NUMPAD8 = ('Numpad8', 104)
    NUMPAD9 = ('Numpad9', 105)
    NUMPADMULTIPLY = ('NumpadMultiply', 106)
    NUMPADADD = ('NumpadAdd', 107)
    NUMPADSUBTRACT = ('NumpadSubtract', 109)
    NUMPADDECIMAL = ('NumpadDecimal', 110)
    NUMPADDIVIDE = ('NumpadDivide', 111)

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

    NUMLOCK = ('NumLock', 144)
    SCROLLLOCK = ('ScrollLock', 145)

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
