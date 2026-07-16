from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.bidi.browser.types import ClientWindow, UserContext

if TYPE_CHECKING:
    from pydoll.protocol.bidi.script.types import SharedReference

BrowsingContext = str
"""Unique identifier for a navigable (browsing context)."""

Navigation = str
"""Unique identifier for an ongoing navigation."""


class ReadinessState(str, Enum):
    """Stage of document loading at which a navigation command returns."""

    NONE = 'none'
    INTERACTIVE = 'interactive'
    COMPLETE = 'complete'


class CreateType(str, Enum):
    """Type of navigable to create."""

    TAB = 'tab'
    WINDOW = 'window'


class UserPromptType(str, Enum):
    """Possible user prompt types."""

    ALERT = 'alert'
    BEFORE_UNLOAD = 'beforeunload'
    CONFIRM = 'confirm'
    PROMPT = 'prompt'


class Info(TypedDict):
    """Properties of a navigable."""

    children: list['Info'] | None
    clientWindow: ClientWindow
    context: BrowsingContext
    originalOpener: BrowsingContext | None
    url: str
    userContext: UserContext
    parent: NotRequired[BrowsingContext | None]


InfoList = list[Info]


class NavigationInfo(TypedDict):
    """Details of an ongoing navigation."""

    context: BrowsingContext
    navigation: Navigation | None
    timestamp: int
    url: str
    userContext: NotRequired[UserContext]


class AccessibilityLocatorValue(TypedDict, total=False):
    """Value for accessibility locator."""

    name: str
    role: str


class AccessibilityLocator(TypedDict):
    """Locator using accessibility attributes."""

    type: str  # "accessibility"
    value: AccessibilityLocatorValue


class CssLocator(TypedDict):
    """Locator using CSS selector."""

    type: str  # "css"
    value: str


class ContextLocatorValue(TypedDict):
    """Value for context locator."""

    context: BrowsingContext


class ContextLocator(TypedDict):
    """Locator using a child browsing context."""

    type: str  # "context"
    value: ContextLocatorValue


class InnerTextLocator(TypedDict):
    """Locator using inner text matching."""

    type: str  # "innerText"
    value: str
    ignoreCase: NotRequired[bool]
    matchType: NotRequired[str]  # "full" / "partial"
    maxDepth: NotRequired[int]


class XPathLocator(TypedDict):
    """Locator using XPath expression."""

    type: str  # "xpath"
    value: str


Locator = (
    AccessibilityLocator
    | CssLocator
    | ContextLocator
    | InnerTextLocator
    | XPathLocator
)


class ImageFormat(TypedDict):
    """Image format specification for screenshots."""

    type: str
    quality: NotRequired[float]  # 0.0..1.0


class BoxClipRectangle(TypedDict):
    """Clip rectangle defined by coordinates and dimensions."""

    type: str  # "box"
    x: float
    y: float
    width: float
    height: float


class ElementClipRectangle(TypedDict):
    """Clip rectangle defined by a DOM element reference."""

    type: str  # "element"
    element: SharedReference


ClipRectangle = BoxClipRectangle | ElementClipRectangle


class Viewport(TypedDict):
    """Viewport dimensions."""

    width: int
    height: int


class PrintMarginParameters(TypedDict, total=False):
    """Margin parameters for PDF printing (in cm)."""

    bottom: float  # .default 1.0
    left: float  # .default 1.0
    right: float  # .default 1.0
    top: float  # .default 1.0


class PrintPageParameters(TypedDict, total=False):
    """Page size parameters for PDF printing (in cm)."""

    height: float  # .default 27.94
    width: float  # .default 21.59
