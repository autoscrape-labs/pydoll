"""Convert HTML to Markdown optimized for LLM consumption.

Uses a two-pass approach: first builds a lightweight DOM tree from the HTML,
then scores each node using text-density and link-density heuristics
(inspired by Readability, Boilerpipe, and jusText), prunes boilerplate,
and serializes the remaining content to Markdown.

Uses only the Python standard library (html.parser). No external dependencies.
"""

from __future__ import annotations

import re
from html import escape as _html_escape
from html.parser import HTMLParser

_STRIP_TAGS = frozenset({
    'script', 'style', 'svg', 'noscript', 'iframe',
    'object', 'embed', 'applet', 'template', 'math', 'canvas',
})

_BOILERPLATE_TAGS = frozenset({'nav', 'footer', 'header', 'aside'})

_VOID_TAGS = frozenset({
    'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
    'link', 'meta', 'param', 'source', 'track', 'wbr',
})

_HEADING_LEVELS = {'h1': 1, 'h2': 2, 'h3': 3, 'h4': 4, 'h5': 5, 'h6': 6}

_INLINE_WRAPPERS = {
    'strong': '**', 'b': '**',
    'em': '*', 'i': '*',
    'del': '~~', 's': '~~',
}

_SEMANTIC_CONTENT_TAGS = frozenset({'main', 'article'})
_SUPPRESS_INLINE_TAGS = frozenset({'cite'})

_BLOCK_LEVEL_TAGS = frozenset({
    'div', 'section', 'article', 'main', 'aside', 'figure', 'figcaption',
    'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'pre', 'blockquote', 'table', 'dl', 'details', 'address',
})

_NEGATIVE_PATTERN = re.compile(
    r'comment|combx|disqus|footer|gdpr|header|legends|menu|related|remark|'
    r'rss|shoutbox|sidebar|skyscraper|social|sponsor|ad-break|agegate|'
    r'pagination|pager|popup|promo|shopping|tags|tool|widget|share|cookie|'
    r'consent|newsletter|signup|subscribe|masthead|outbrain|taboola|breadcrumb|'
    r'modal|overlay|dropdown|toolbar|banner|announcement',
    re.IGNORECASE,
)

_POSITIVE_PATTERN = re.compile(
    r'article|body|content|entry|hentry|main|page|post|text|blog|story|'
    r'prose|copy|md-content|md-typeset',
    re.IGNORECASE,
)

_MIN_TEXT_LENGTH = 25
_LINK_DENSITY_THRESHOLD = 0.5
_TEXT_DENSITY_THRESHOLD = 5
_MIN_CONTENT_SCORE = 0.3

_NEWLINE_COLLAPSE_RE = re.compile(r'\n{3,}')
_WHITESPACE_RE = re.compile(r'[ \t]+')
_EMPTY_BOLD_RE = re.compile(r'\*\*\*\*')
_EMPTY_STRIKE_RE = re.compile(r'~~~~')
_EMPTY_HEADINGS_RE = re.compile(r'^#{1,6}\s*$', re.MULTILINE)
_ORPHAN_BACKTICKS_RE = re.compile(r'^`{2}(?!`)\s*$', re.MULTILINE)
_EMPTY_LINKS_RE = re.compile(r'\[(?:!\[\]\([^)]*\))?\]\(\s*#?\s*\)')
_EMPTY_LIST_ITEMS_RE = re.compile(r'^[-*]\s*$', re.MULTILINE)
_NUMBERED_EMPTY_ITEMS_RE = re.compile(r'^\d+\.\s*$', re.MULTILINE)
_LOADING_LINE_RE = re.compile(r'^Loading\b[^.]*$', re.MULTILINE)
_HEADING_RE = re.compile(r'^(#{1,6}) ', re.MULTILINE)
_INLINE_LINK_RE = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
_DISPLAY_RE = re.compile(r'display\s*:\s*(\w+)')

_MIN_IMAGE_SRC_LENGTH = 5
_MIN_BOILERPLATE_NON_LINK_TEXT = 200
_MAX_LINK_HREF_LENGTH = 150

_BOILERPLATE_ARIA_ROLES = frozenset({
    'navigation', 'search', 'banner', 'complementary',
    'contentinfo', 'button', 'dialog', 'tooltip',
})

_UI_LABEL_PATTERN = re.compile(
    r'^(share|share link|click to copy|copy link|show more|show less|'
    r'positive feedback|negative feedback|feedback|cancel|confirm|'
    r'close|dismiss|sign in|log in|loading|my ad centre|'
    r'are you sure\??|visible only to you|still in progress\??|'
    r'choose a reason.*|the reason will be displayed.*|'
    r'dive deeper.*|ai can make mistakes.*|'
    r'apply labels.*|none yet|you\'re receiving notifications.*|'
    r'pro\s?tip!?.*)$',
    re.IGNORECASE,
)

_CONTENT_ARIA_ROLES = frozenset({'main', 'article'})
_UI_ELEMENT_TAGS = frozenset({
    'button', 'label', 'select', 'textarea', 'input', 'form',
})
_TABLE_CELL_TAGS = frozenset({'td', 'th'})
_WHITESPACE_CHARS = frozenset({' ', '\n'})
_FORMATTING_MARKERS = frozenset({'*', '`', '[', '!'})
_LINK_HEAVY_TAGS = frozenset({'div', 'section', 'span'})
_LINK_HEAVY_THRESHOLD = 0.7
_MAX_UI_LABEL_LENGTH = 120

_NOISE_IMAGE_PATTERNS = frozenset({
    'avatars.', '/social/', '/kpui/', 'gstatic.com',
    'googleusercontent.com', '/favicon',
})

_SCORE_CONTAINER_TAGS = frozenset({'div', 'section', 'td'})
_SCORE_MIN_THRESHOLD = 1.0
_CONTEXT_PRUNE_MIN_CHILDREN = 3
_MAX_ANCESTOR_DEPTH = 5
_MAX_HEADING_LEVEL = 6
_MIN_HEADINGS_FOR_NORMALIZATION = 2
_MIN_LINK_REPETITIONS = 2


class _Node:
    """Lightweight DOM node."""

    __slots__ = ('tag', 'attrs', 'children', 'text', 'tail', 'parent')

    def __init__(self, tag: str, attrs: dict[str, str]) -> None:
        self.tag = tag
        self.attrs = attrs
        self.children: list[_Node] = []
        self.text: str = ''
        self.tail: str = ''
        self.parent: _Node | None = None

    def text_content(self) -> str:
        """Get all text content recursively."""
        parts = [self.text]
        for child in self.children:
            parts.append(child.text_content())
            parts.append(child.tail)
        return ''.join(parts)

    def link_text_length(self) -> int:
        """Get total text length inside <a> tags."""
        if self.tag == 'a':
            return len(self.text_content())
        return sum(child.link_text_length() for child in self.children)

    def count_tags(self) -> int:
        """Count all descendant tags."""
        return sum(1 + child.count_tags() for child in self.children)

    def iter_tag(self, tag: str) -> list[_Node]:
        """Find all descendants with given tag."""
        result: list[_Node] = []
        for child in self.children:
            if child.tag == tag:
                result.append(child)
            result.extend(child.iter_tag(tag))
        return result

    def iter_all(self) -> list[_Node]:
        """Iterate all descendants."""
        result: list[_Node] = []
        for child in self.children:
            result.append(child)
            result.extend(child.iter_all())
        return result


class _TreeBuilder(HTMLParser):
    """Build a lightweight DOM tree from HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.root = _Node('root', {})
        self._current = self.root
        self._strip_depth = 0
        self._text_target: _Node | None = None

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if self._should_skip_tag(tag):
            return
        attr_dict = {k: (v or '') for k, v in attrs}
        node = _Node(tag, attr_dict)
        node.parent = self._current
        self._current.children.append(node)
        if tag in _VOID_TAGS:
            self._text_target = node
            return
        self._current = node
        self._text_target = None

    def handle_endtag(self, tag: str) -> None:
        if tag in _STRIP_TAGS:
            self._strip_depth = max(0, self._strip_depth - 1)
            return
        if self._strip_depth > 0:
            if tag not in _VOID_TAGS:
                self._strip_depth = max(0, self._strip_depth - 1)
            return
        if tag in _VOID_TAGS:
            return
        self._close_tag(tag)

    def handle_data(self, data: str) -> None:
        if self._strip_depth > 0:
            return
        if self._text_target is not None:
            self._text_target.tail += data
        else:
            self._current.text += data

    def handle_comment(self, _data: str) -> None:
        pass

    def _should_skip_tag(self, tag: str) -> bool:
        if tag in _STRIP_TAGS:
            self._strip_depth += 1
            return True
        if self._strip_depth > 0:
            if tag not in _VOID_TAGS:
                self._strip_depth += 1
            return True
        return False

    def _close_tag(self, tag: str) -> None:
        """Walk up the tree to find and close a matching open tag."""
        node = self._current
        while node.parent is not None:
            if node.tag == tag:
                self._current = node.parent
                self._text_target = node
                return
            node = node.parent

    @classmethod
    def parse(cls, html: str) -> _Node:
        """Parse HTML string into a DOM tree."""
        builder = cls()
        builder.feed(html)
        return builder.root


class _BoilerplatePruner:
    """Score nodes and prune boilerplate from the DOM tree."""

    def prune(self, root: _Node) -> None:
        """Remove boilerplate nodes from the tree."""
        root.children = [
            c for c in root.children if not self._should_strip(c)
        ]
        for child in root.children:
            self.prune(child)

    _STRUCTURAL_PARENTS = frozenset({
        'ul', 'ol', 'table', 'thead', 'tbody', 'tfoot', 'tr',
        'dl', 'details', 'figure',
    })

    def context_sensitive_prune(self, root: _Node) -> None:
        """jusText-inspired: remove short isolated blocks between bad blocks.

        Skips structural containers (lists, tables) where children
        are structural elements, not standalone content blocks.
        """
        if (
            len(root.children) < _CONTEXT_PRUNE_MIN_CHILDREN
            or root.tag in self._STRUCTURAL_PARENTS
        ):
            for child in root.children:
                self.context_sensitive_prune(child)
            return
        scores = [self._score_node(c) for c in root.children]
        has_good_anchor = any(s >= _MIN_CONTENT_SCORE for s in scores)
        if not has_good_anchor:
            for child in root.children:
                self.context_sensitive_prune(child)
            return
        to_remove: set[int] = set()
        for i, (child, score) in enumerate(zip(root.children, scores)):
            text = child.text_content().strip()
            if len(text) >= _MIN_TEXT_LENGTH or score >= _MIN_CONTENT_SCORE:
                continue
            prev_score = scores[i - 1] if i > 0 else 0.0
            next_score = (
                scores[i + 1] if i < len(scores) - 1 else 0.0
            )
            if (
                prev_score < _MIN_CONTENT_SCORE
                and next_score < _MIN_CONTENT_SCORE
            ):
                to_remove.add(i)
        if to_remove:
            root.children = [
                c for i, c in enumerate(root.children)
                if i not in to_remove
            ]
        for child in root.children:
            self.context_sensitive_prune(child)

    def _should_strip(self, node: _Node) -> bool:
        """Check if a node should be removed entirely."""
        return (
            self._is_low_content_boilerplate(node)
            or self._is_hidden(node)
            or self._has_boilerplate_role(node)
            or self._has_negative_pattern(node)
            or node.tag in _UI_ELEMENT_TAGS
            or self._is_link_heavy(node)
            or self._is_ui_label(node)
        )

    # ── Individual strip checks ──

    @staticmethod
    def _is_low_content_boilerplate(node: _Node) -> bool:
        if node.tag not in _BOILERPLATE_TAGS:
            return False
        if (
            node.parent is not None
            and node.parent.tag in _SEMANTIC_CONTENT_TAGS
        ):
            return False
        text = node.text_content().strip()
        non_link_text = len(text) - node.link_text_length()
        return non_link_text < _MIN_BOILERPLATE_NON_LINK_TEXT

    @staticmethod
    def _is_hidden(node: _Node) -> bool:
        if node.attrs.get('aria-hidden') == 'true':
            return True
        if 'hidden' in node.attrs:
            return True
        style = node.attrs.get('style', '').replace(' ', '')
        return 'display:none' in style or 'visibility:hidden' in style

    @staticmethod
    def _has_boilerplate_role(node: _Node) -> bool:
        return node.attrs.get('role', '') in _BOILERPLATE_ARIA_ROLES

    def _has_negative_pattern(self, node: _Node) -> bool:
        class_id = self._get_class_id(node)
        if not class_id or not _NEGATIVE_PATTERN.search(class_id):
            return False
        if _POSITIVE_PATTERN.search(class_id):
            return False
        if self._score_node(node) >= _MIN_CONTENT_SCORE:
            return False
        return not self._has_content_rich_ancestor(node)

    def _has_content_rich_ancestor(self, node: _Node) -> bool:
        """Check if any ancestor is content-rich (high score).

        Prevents false-positive stripping of nodes inside real content
        areas where class names like 'comment-view-model' match the
        negative pattern but are actually content containers.
        """
        current = node.parent
        depth = 0
        while current is not None and depth < _MAX_ANCESTOR_DEPTH:
            if self._score_node(current) >= _MIN_CONTENT_SCORE:
                return True
            current = current.parent
            depth += 1
        return False

    def _is_link_heavy(self, node: _Node) -> bool:
        if node.tag not in _LINK_HEAVY_TAGS:
            return False
        text = node.text_content().strip()
        if len(text) <= _MIN_TEXT_LENGTH:
            return False
        if self._link_density(node) <= _LINK_HEAVY_THRESHOLD:
            return False
        return not self._has_content_rich_ancestor(node)

    @staticmethod
    def _is_ui_label(node: _Node) -> bool:
        text = node.text_content().strip()
        return bool(
            text
            and len(text) < _MAX_UI_LABEL_LENGTH
            and _UI_LABEL_PATTERN.match(text)
        )

    def _score_node(self, node: _Node) -> float:
        """Score a block-level node for content quality."""
        text = node.text_content().strip()
        if len(text) < _MIN_TEXT_LENGTH:
            return 0.0
        ld = self._link_density(node)
        if ld > _LINK_DENSITY_THRESHOLD:
            return 0.0
        score = self._density_score(node)
        score += self._length_bonus(text)
        score += self._punctuation_bonus(text)
        score *= 1.0 - ld
        score += self._class_id_bonus(node)
        score += self._aria_role_bonus(node)
        return max(score, 0.0)

    def _density_score(self, node: _Node) -> float:
        td = self._text_density(node)
        if td > _TEXT_DENSITY_THRESHOLD * 2:
            return 1.0
        if td > _TEXT_DENSITY_THRESHOLD:
            return 0.5
        return 0.0

    @staticmethod
    def _length_bonus(text: str) -> float:
        return min(len(text) / 500, 1.0)

    @staticmethod
    def _punctuation_bonus(text: str) -> float:
        punct_count = text.count(',') + text.count('.') + text.count(';')
        return min(punct_count * 0.1, 0.5)

    def _class_id_bonus(self, node: _Node) -> float:
        class_id = self._get_class_id(node)
        if not class_id:
            return 0.0
        score = 0.0
        if _POSITIVE_PATTERN.search(class_id):
            score += 0.5
        if _NEGATIVE_PATTERN.search(class_id):
            score -= 0.5
        return score

    @staticmethod
    def _aria_role_bonus(node: _Node) -> float:
        role = node.attrs.get('role', '')
        if role in _BOILERPLATE_ARIA_ROLES:
            return -1.0
        if role in _CONTENT_ARIA_ROLES:
            return 0.5
        return 0.0

    @staticmethod
    def _text_density(node: _Node) -> float:
        """Text characters per tag descendant (CETD-inspired)."""
        text_len = len(node.text_content().strip())
        return text_len / max(node.count_tags(), 1)

    @staticmethod
    def _link_density(node: _Node) -> float:
        """Fraction of text inside <a> tags (Readability-inspired)."""
        total = len(node.text_content().strip())
        if total == 0:
            return 1.0
        return node.link_text_length() / total

    @staticmethod
    def _get_class_id(node: _Node) -> str:
        return (
            f'{node.attrs.get("class", "")} {node.attrs.get("id", "")}'
        ).strip()


class _ContentFinder:
    """Find the main content element in the DOM tree."""

    @staticmethod
    def find(root: _Node) -> _Node:
        """Prioritizes <main>, <article>, or [role="main"] elements.

        Falls back to score-based container detection (Readability-style).
        """
        for tag in ('main', 'article'):
            candidates = root.iter_tag(tag)
            if candidates:
                return max(
                    candidates, key=lambda n: len(n.text_content())
                )
        for child in root.iter_all():
            if child.attrs.get('role') == 'main':
                return child
        return _ContentFinder._find_by_score(root)

    @staticmethod
    def _find_by_score(root: _Node) -> _Node:
        """Score-bubbling fallback for pages without semantic HTML5 tags."""
        scorer = _BoilerplatePruner()
        root_text_len = len(root.text_content().strip())
        if root_text_len == 0:
            return root
        best_node = root
        best_score = -1.0
        for node in root.iter_all():
            if node.tag not in _SCORE_CONTAINER_TAGS:
                continue
            node_text_len = len(node.text_content().strip())
            if node_text_len < root_text_len * 0.25:
                continue
            score = scorer._score_node(node)
            if score > best_score:
                best_score = score
                best_node = node
        if best_score >= _SCORE_MIN_THRESHOLD:
            return best_node
        return root


class _CSSDisplayResolver:
    """Adjust node classification based on CSS display property."""

    @staticmethod
    def resolve(root: _Node) -> None:
        """Mark nodes with display overrides (block/inline)."""
        for node in root.iter_all():
            style = node.attrs.get('style', '')
            if not style:
                continue
            match = _DISPLAY_RE.search(style)
            if not match:
                continue
            display = match.group(1).lower()
            if display == 'block' and node.tag not in _BLOCK_LEVEL_TAGS:
                node.attrs['_display'] = 'block'
            elif display == 'inline' and node.tag in _BLOCK_LEVEL_TAGS:
                node.attrs['_display'] = 'inline'


class _MarkdownSerializer:
    """Serialize a DOM subtree to Markdown."""

    def __init__(self) -> None:
        self._parts: list[str] = []
        self._list_stack: list[tuple[str, int]] = []
        self._blockquote_depth = 0
        self._tag_handlers = {
            'p': self._handle_paragraph,
            'a': self._handle_link,
            'img': self._handle_image,
            'code': self._handle_inline_code,
            'pre': self._handle_code_block,
            'ul': self._handle_list,
            'ol': self._handle_list,
            'blockquote': self._handle_blockquote,
            'table': self._handle_table,
            'hr': self._handle_hr,
            'br': self._handle_br,
            'dl': self._handle_definition_list,
            'details': self._handle_details,
            **{tag: self._handle_heading for tag in _HEADING_LEVELS},
            **{tag: self._handle_inline_wrapper for tag in _INLINE_WRAPPERS},
        }
        self._inline_renderers = {
            'code': self._render_code_fragment,
            'a': self._render_link_fragment,
            'br': self._render_br_fragment,
            'hr': self._render_hr_fragment,
            'img': self._render_image_fragment,
            **{
                tag: self._render_wrapper_fragment
                for tag in _INLINE_WRAPPERS
            },
        }

    def serialize(self, node: _Node) -> str:
        """Convert a DOM subtree to Markdown."""
        self._parts = []
        self._list_stack = []
        self._blockquote_depth = 0
        self._process_node(node)
        return ''.join(self._parts)

    def _process_node(self, node: _Node) -> None:
        """Dispatch node to the appropriate handler."""
        handler = self._tag_handlers.get(node.tag)
        if handler is not None:
            handler(node)
        else:
            self._handle_generic_block(node)

    def _handle_heading(self, node: _Node) -> None:
        level = _HEADING_LEVELS[node.tag]
        inner = self._get_inline_text(node).strip()
        if inner:
            self._parts.append(f'\n\n{"#" * level} {inner}\n\n')

    def _handle_paragraph(self, node: _Node) -> None:
        inner = self._get_inline_text(node).strip()
        if not inner:
            return
        if self._blockquote_depth > 0:
            prefix = '> ' * self._blockquote_depth
            inner = '\n'.join(prefix + line for line in inner.split('\n'))
        self._parts.append(f'\n\n{inner}\n\n')

    def _handle_link(self, node: _Node) -> None:
        href = node.attrs.get('href', '')
        text = self._get_inline_text(node).strip()
        if text and href:
            href = self._truncate_href(href)
            link_md = f'[{text}]({href})'
            self._ensure_space_before(self._parts, link_md)
            self._parts.append(link_md)
        elif text:
            self._ensure_space_before(self._parts, text)
            self._parts.append(text)

    def _handle_image(self, node: _Node) -> None:
        rendered = self._render_image_fragment(node)
        if rendered:
            self._ensure_space_before(self._parts, rendered)
            self._parts.append(rendered)

    def _handle_inline_wrapper(self, node: _Node) -> None:
        wrapper = _INLINE_WRAPPERS[node.tag]
        inner = self._get_inline_text(node).strip()
        if inner:
            formatted = f'{wrapper}{inner}{wrapper}'
            self._ensure_space_before(self._parts, formatted)
            self._parts.append(formatted)

    def _handle_inline_code(self, node: _Node) -> None:
        if self._is_inside_pre(node):
            return
        inner = node.text_content().strip()
        if inner:
            formatted = f'`{inner}`'
            self._ensure_space_before(self._parts, formatted)
            self._parts.append(formatted)

    def _handle_code_block(self, node: _Node) -> None:
        code_node = next(
            (c for c in node.children if c.tag == 'code'), None
        )
        if code_node:
            lang = self._extract_code_language(code_node)
            code_text = code_node.text_content()
        else:
            lang = ''
            code_text = node.text_content()
        if code_text.strip():
            self._parts.append(f'\n\n```{lang}\n{code_text}\n```\n\n')

    def _handle_list(self, node: _Node) -> None:
        self._list_stack.append((node.tag, 0))
        self._parts.append('\n')
        for child in node.children:
            if child.tag == 'li':
                self._handle_list_item(child, node.tag)
        self._parts.append('\n')
        self._list_stack.pop()

    def _handle_list_item(self, node: _Node, list_type: str) -> None:
        bq_prefix = '> ' * self._blockquote_depth
        indent = '  ' * max(0, len(self._list_stack) - 1)
        if list_type == 'ol':
            tag, counter = self._list_stack[-1]
            counter += 1
            self._list_stack[-1] = (tag, counter)
            self._parts.append(f'{bq_prefix}{indent}{counter}. ')
        else:
            self._parts.append(f'{bq_prefix}{indent}- ')
        self._handle_li_content(node)
        self._parts.append('\n')

    def _handle_li_content(self, node: _Node) -> None:
        """Serialize list item content (may contain nested block elements)."""
        inline_text = self._get_inline_text(node).strip()
        if inline_text:
            self._parts.append(inline_text)
        for child in node.children:
            if child.tag in _BLOCK_LEVEL_TAGS:
                self._process_node(child)

    def _handle_blockquote(self, node: _Node) -> None:
        self._blockquote_depth += 1
        for child in node.children:
            self._process_node(child)
        self._blockquote_depth -= 1

    def _handle_table(self, node: _Node) -> None:
        rows = self._collect_table_rows(node)
        if not rows:
            return
        target_cols = self._find_target_column_count(rows)
        pre_text, table_rows = self._split_table_rows(rows, target_cols)
        for text in pre_text:
            self._parts.append(f'\n\n{text}\n\n')
        self._render_pipe_table(table_rows)

    def _handle_hr(self, _node: _Node) -> None:
        self._parts.append('\n\n---\n\n')

    def _handle_br(self, _node: _Node) -> None:
        self._parts.append('\n')

    def _handle_definition_list(self, node: _Node) -> None:
        for child in node.children:
            if child.tag == 'dt':
                inner = self._get_inline_text(child).strip()
                if inner:
                    self._parts.append(f'\n\n**{inner}**\n')
            elif child.tag == 'dd':
                inner = self._get_inline_text(child).strip()
                if inner:
                    self._parts.append(f': {inner}\n')

    def _handle_details(self, node: _Node) -> None:
        summary = next(
            (c for c in node.children if c.tag == 'summary'), None
        )
        if summary:
            inner = self._get_inline_text(summary).strip()
            if inner:
                self._parts.append(f'\n\n**{inner}**\n\n')
        for child in node.children:
            if child.tag != 'summary':
                self._process_node(child)

    def _handle_generic_block(self, node: _Node) -> None:
        text = node.text.strip()
        if text:
            self._parts.append(text)
        for child in node.children:
            self._prepend_block_spacing(child)
            self._process_node(child)
            self._append_block_tail(child)

    def _prepend_block_spacing(self, child: _Node) -> None:
        if self._is_block_display(child):
            self._parts.append('\n')
        else:
            self._ensure_space_before_parts(self._parts)

    def _append_block_tail(self, child: _Node) -> None:
        tail_text = child.tail.strip()
        if tail_text:
            self._ensure_space_before(self._parts, tail_text)
            self._parts.append(tail_text)
        elif self._is_block_display(child):
            self._parts.append('\n')

    # ── Inline rendering ──

    def _get_inline_text(self, node: _Node) -> str:
        """Get text content, rendering inline elements."""
        parts: list[str] = []
        text = _WHITESPACE_RE.sub(' ', node.text.replace('\n', ' '))
        parts.append(text)
        for child in node.children:
            if self._is_block_display(child):
                continue
            fragment = self._render_inline_child(child)
            if fragment:
                self._ensure_space_before(parts, fragment)
                parts.append(fragment)
            self._append_inline_tail(parts, child.tail)
        return ''.join(parts)

    def _append_inline_tail(self, parts: list[str], raw_tail: str) -> None:
        """Append tail text of an inline element, preserving spacing."""
        tail = _WHITESPACE_RE.sub(' ', raw_tail.replace('\n', ' '))
        if tail.strip():
            self._ensure_space_before(parts, tail)
            parts.append(tail)
        elif (
            tail
            and parts
            and parts[-1]
            and not parts[-1].endswith((' ', '\n'))
        ):
            parts.append(' ')

    def _render_inline_child(self, child: _Node) -> str:
        """Render a single inline child node to Markdown text."""
        if child.tag in _SUPPRESS_INLINE_TAGS:
            return ''
        renderer = self._inline_renderers.get(child.tag)
        if renderer is not None:
            return renderer(child)
        return self._get_inline_text(child).strip()

    def _render_wrapper_fragment(self, node: _Node) -> str:
        wrapper = _INLINE_WRAPPERS[node.tag]
        inner = self._get_inline_text(node).strip()
        return f'{wrapper}{inner}{wrapper}' if inner else ''

    @staticmethod
    def _render_code_fragment(node: _Node) -> str:
        inner = node.text_content().strip()
        return f'`{inner}`' if inner else ''

    def _render_link_fragment(self, node: _Node) -> str:
        href = node.attrs.get('href', '')
        link_text = self._get_inline_text(node).strip()
        if link_text and href:
            href = self._truncate_href(href)
            return f'[{link_text}]({href})'
        return link_text or ''

    @staticmethod
    def _render_br_fragment(_node: _Node) -> str:
        return '\n'

    @staticmethod
    def _render_hr_fragment(_node: _Node) -> str:
        return '\n\n---\n\n'

    def _render_image_fragment(self, node: _Node) -> str:
        """Render an image, filtering noise images."""
        src = node.attrs.get('src', '')
        if self._is_noise_image(src):
            return ''
        alt = node.attrs.get('alt', '')
        return f'![{alt}]({src})'

    # ── Table helpers ──

    def _collect_table_rows(self, node: _Node) -> list[list[str]]:
        rows: list[list[str]] = []
        for child in node.iter_all():
            if child.tag == 'tr':
                cells = self._extract_row_cells(child)
                if cells:
                    rows.append(cells)
        return rows

    def _extract_row_cells(self, row_node: _Node) -> list[str]:
        cells: list[str] = []
        for cell in row_node.children:
            if cell.tag in _TABLE_CELL_TAGS:
                cell_text = self._get_inline_text(cell).strip()
                cell_text = cell_text.replace('|', '\\|').replace('\n', ' ')
                colspan = self._get_colspan(cell)
                cells.append(cell_text)
                for _ in range(colspan - 1):
                    cells.append('')
        return cells

    @staticmethod
    def _get_colspan(cell: _Node) -> int:
        """Read colspan attribute, defaulting to 1."""
        try:
            return max(1, int(cell.attrs.get('colspan', '1')))
        except ValueError:
            return 1

    @staticmethod
    def _find_target_column_count(rows: list[list[str]]) -> int:
        col_counts = [len(row) for row in rows]
        return max(set(col_counts), key=col_counts.count)

    @staticmethod
    def _split_table_rows(
        rows: list[list[str]],
        target_cols: int,
    ) -> tuple[list[str], list[list[str]]]:
        table_rows: list[list[str]] = []
        pre_text: list[str] = []
        for row in rows:
            if len(row) == 1 and target_cols > 1:
                if row[0]:
                    pre_text.append(row[0])
            else:
                while len(row) < target_cols:
                    row.append('')
                table_rows.append(row[:target_cols])
        table_rows = [
            row for row in table_rows if any(cell.strip() for cell in row)
        ]
        return pre_text, table_rows

    def _render_pipe_table(self, table_rows: list[list[str]]) -> None:
        if not table_rows:
            return
        self._parts.append('\n\n')
        self._parts.append('| ' + ' | '.join(table_rows[0]) + ' |\n')
        self._parts.append(
            '| ' + ' | '.join('---' for _ in table_rows[0]) + ' |\n'
        )
        for row in table_rows[1:]:
            self._parts.append('| ' + ' | '.join(row) + ' |\n')
        self._parts.append('\n')

    @staticmethod
    def _ensure_space_before(
        parts: list[str], next_text: str
    ) -> None:
        """Insert a space between parts to prevent word concatenation."""
        if not parts or not parts[-1] or not next_text:
            return
        last_char = parts[-1][-1]
        first_char = next_text[0]
        if last_char in _WHITESPACE_CHARS or first_char in _WHITESPACE_CHARS:
            return
        if (
            last_char.isalnum()
            or first_char.isalnum()
            or first_char in _FORMATTING_MARKERS
        ):
            parts.append(' ')

    @staticmethod
    def _ensure_space_before_parts(parts: list[str]) -> None:
        """Add a space if the last text ends with a word character."""
        if parts and parts[-1] and parts[-1][-1].isalnum():
            parts.append(' ')

    @staticmethod
    def _is_block_display(node: _Node) -> bool:
        """Check if a node should be treated as block-level."""
        display = node.attrs.get('_display', '')
        if display == 'inline':
            return False
        if display == 'block':
            return True
        return node.tag in _BLOCK_LEVEL_TAGS

    @staticmethod
    def _is_inside_pre(node: _Node) -> bool:
        current = node.parent
        while current is not None:
            if current.tag == 'pre':
                return True
            current = current.parent
        return False

    @staticmethod
    def _extract_code_language(code_node: _Node) -> str:
        code_class = code_node.attrs.get('class', '')
        for cls in code_class.split():
            if cls.startswith('language-'):
                return cls[9:]
        return ''

    @staticmethod
    def _is_noise_image(src: str) -> bool:
        return (
            not src
            or src.startswith('data:')
            or len(src) < _MIN_IMAGE_SRC_LENGTH
            or src.endswith('.svg')
            or any(pattern in src for pattern in _NOISE_IMAGE_PATTERNS)
        )

    @staticmethod
    def _truncate_href(href: str) -> str:
        if len(href) > _MAX_LINK_HREF_LENGTH:
            return href.split('?')[0]
        return href


class _PostProcessor:
    """Clean up raw Markdown output."""

    _CLEANUP_PATTERNS = [
        _EMPTY_BOLD_RE,
        _EMPTY_STRIKE_RE,
        _EMPTY_HEADINGS_RE,
        _ORPHAN_BACKTICKS_RE,
        _EMPTY_LINKS_RE,
        _EMPTY_LIST_ITEMS_RE,
        _NUMBERED_EMPTY_ITEMS_RE,
        _LOADING_LINE_RE,
    ]

    @classmethod
    def process(cls, text: str) -> str:
        """Apply cleanup patterns and normalize whitespace."""
        text = text.replace('\xa0', ' ')
        for pattern in cls._CLEANUP_PATTERNS:
            text = pattern.sub('', text)
        text = cls._normalize_headings(text)
        text = _NEWLINE_COLLAPSE_RE.sub('\n\n', text)
        text = cls._convert_to_reference_links(text)
        return text.strip()

    @classmethod
    def _normalize_headings(cls, text: str) -> str:
        """Shift headings so the minimum level becomes H1.

        Only applies when there are 2+ headings (avoids changing fragments).
        Skips headings inside code fences.
        """
        parts = re.split(r'(```[\s\S]*?```)', text)
        min_level = 7
        heading_count = 0
        for i in range(0, len(parts), 2):
            for m in _HEADING_RE.finditer(parts[i]):
                heading_count += 1
                min_level = min(min_level, len(m.group(1)))
        if (
            min_level <= 1
            or min_level > _MAX_HEADING_LEVEL
            or heading_count < _MIN_HEADINGS_FOR_NORMALIZATION
        ):
            return text
        shift = min_level - 1

        def _shift_heading(m: re.Match[str]) -> str:
            new_level = max(1, len(m.group(1)) - shift)
            return '#' * new_level + ' '

        result: list[str] = []
        for i, part in enumerate(parts):
            if i % 2 == 0:
                result.append(_HEADING_RE.sub(_shift_heading, part))
            else:
                result.append(part)
        return ''.join(result)

    @classmethod
    def _convert_to_reference_links(cls, text: str) -> str:
        """Convert repeated inline links to reference-style for token savings.

        Only converts URLs that appear 2+ times. Skips code fences.
        """
        parts = re.split(r'(```[\s\S]*?```)', text)
        url_counts: dict[str, int] = {}
        for i in range(0, len(parts), 2):
            for m in _INLINE_LINK_RE.finditer(parts[i]):
                url = m.group(2)
                url_counts[url] = url_counts.get(url, 0) + 1
        repeated = {
            url for url, count in url_counts.items()
            if count >= _MIN_LINK_REPETITIONS
        }
        if not repeated:
            return text
        ref_map: dict[str, int] = {}
        counter = 0

        def _replace_link(m: re.Match[str]) -> str:
            nonlocal counter
            link_text, url = m.group(1), m.group(2)
            if url not in repeated:
                return m.group(0)
            if url not in ref_map:
                counter += 1
                ref_map[url] = counter
            return f'[{link_text}][{ref_map[url]}]'

        result_parts: list[str] = []
        for i, part in enumerate(parts):
            if i % 2 == 0:
                result_parts.append(
                    _INLINE_LINK_RE.sub(_replace_link, part)
                )
            else:
                result_parts.append(part)
        result = ''.join(result_parts)
        if ref_map:
            sorted_refs = sorted(ref_map.items(), key=lambda x: x[1])
            refs = '\n'.join(
                f'[{rid}]: {url}' for url, rid in sorted_refs
            )
            result = f'{result}\n\n{refs}'
        return result


def clean_html(html: str) -> str:
    """Clean HTML by removing noise while preserving structure and attributes.

    Strips scripts, styles, SVGs, hidden elements, UI elements, and
    non-content tags (head, link, meta). Does NOT apply content-finding
    or aggressive boilerplate pruning — when used on scoped containers
    (e.g. a single list item), the content finder would discard content.

    Args:
        html: Raw HTML string (full page or scoped fragment).

    Returns:
        Clean HTML string with noise removed.
    """
    tree = _TreeBuilder.parse(html)
    _BoilerplatePruner().prune(tree)
    _strip_non_content_tags(tree)
    _strip_empty_nodes(tree)
    _collapse_wrappers(tree)
    return _serialize_to_html(tree, minimal=True).strip()


_NON_CONTENT_TAGS = frozenset({
    'head', 'link', 'meta',
})


def _strip_non_content_tags(root: _Node) -> None:
    """Remove tags that carry no extractable content (head, link, meta)."""
    root.children = [
        c for c in root.children if c.tag not in _NON_CONTENT_TAGS
    ]
    for child in root.children:
        _strip_non_content_tags(child)


def _strip_empty_nodes(root: _Node) -> None:
    """Remove nodes that have no text content (empty wrappers).

    Runs bottom-up so that deeply nested empty structures collapse
    fully in a single pass. Preserves nodes that have meaningful
    text, tail, or semantic attributes (href, src, aria-label, alt).
    """
    for child in root.children:
        _strip_empty_nodes(child)
    root.children = [
        c for c in root.children if _has_content(c)
    ]


_WRAPPER_TAGS = frozenset({'div', 'span', 'section'})


def _collapse_wrappers(root: _Node) -> None:
    """Collapse wrapper nodes that add no semantic value.

    A wrapper is a div/span/section with no text, no semantic attributes,
    and exactly one child. It is replaced by its child, reducing nesting.
    Runs bottom-up and repeats until stable.
    """
    changed = True
    while changed:
        changed = _collapse_pass(root)


def _collapse_pass(root: _Node) -> bool:
    """Single pass of wrapper collapsing. Returns True if any were collapsed."""
    changed = False
    for child in root.children:
        if _collapse_pass(child):
            changed = True
    new_children: list[_Node] = []
    for child in root.children:
        if _is_collapsible_wrapper(child):
            grandchild = child.children[0]
            if child.tail and child.tail.strip():
                grandchild.tail = (grandchild.tail or '') + child.tail
            grandchild.parent = root
            new_children.append(grandchild)
            changed = True
        else:
            new_children.append(child)
    root.children = new_children
    return changed


def _is_collapsible_wrapper(node: _Node) -> bool:
    """Check if a node is a meaningless wrapper that can be collapsed."""
    if node.tag not in _WRAPPER_TAGS:
        return False
    if len(node.children) != 1:
        return False
    if node.text and node.text.strip():
        return False
    return not (node.attrs.keys() & _KEEP_ATTRS)


def _has_content(node: _Node) -> bool:
    """Check if a node contributes any extractable content."""
    if node.text and node.text.strip():
        return True
    if node.tail and node.tail.strip():
        return True
    if node.children:
        return True
    return bool(node.attrs.keys() & _KEEP_ATTRS)


def _serialize_to_html(node: _Node, minimal: bool = False) -> str:
    """Serialize a DOM subtree back to HTML.

    Args:
        node: Root node of the subtree.
        minimal: If True, strip non-semantic attributes (class, data-*, etc.).
    """
    parts: list[str] = []
    _render_html_node(node, parts, minimal=minimal)
    return ''.join(parts)


def _render_html_node(
    node: _Node,
    parts: list[str],
    minimal: bool = False,
) -> None:
    """Recursively render a node and its children to HTML.

    Text and tail content are escaped to prevent HTML injection
    (the parser delivers decoded entities, so re-serialization
    must re-encode ``<``, ``>``, ``&``).
    """
    is_root = node.tag == 'root'
    if not is_root:
        attrs = _format_html_attrs(node.attrs, minimal=minimal)
        parts.append(f'<{node.tag}{attrs}>')
    if node.text:
        parts.append(_html_escape(node.text))
    for child in node.children:
        _render_html_node(child, parts, minimal=minimal)
        if child.tail:
            parts.append(_html_escape(child.tail))
    if not is_root and node.tag not in _VOID_TAGS:
        parts.append(f'</{node.tag}>')


_KEEP_ATTRS = frozenset({
    'href', 'src', 'alt', 'title', 'aria-label', 'aria-describedby',
    'type', 'name', 'value', 'placeholder', 'datetime', 'lang',
    'colspan', 'rowspan', 'scope',
})


def _format_html_attrs(
    attrs: dict[str, str],
    minimal: bool = False,
) -> str:
    """Format node attributes as an HTML attribute string.

    Attribute values are escaped to prevent injection via quotes.
    Internal ``_``-prefixed attrs (e.g. ``_display``) are always filtered.

    When ``minimal=True`` (used by ``clean_html``), only semantically
    relevant attributes are kept (href, src, alt, aria-label, etc.),
    stripping class names, data-* tracking attributes, and other noise
    that wastes LLM tokens.

    Args:
        attrs: Raw attribute dict from the node.
        minimal: If True, keep only ``_KEEP_ATTRS``.

    Returns:
        Formatted attribute string (with leading space) or empty string.
    """
    if minimal:
        filtered = {
            k: v for k, v in attrs.items()
            if k in _KEEP_ATTRS
        }
    else:
        filtered = {
            k: v for k, v in attrs.items()
            if not k.startswith('_')
        }
    if not filtered:
        return ''
    pairs = ' '.join(
        f'{k}="{_html_escape(v, quote=True)}"' if v else k
        for k, v in filtered.items()
    )
    return f' {pairs}'


def html_to_markdown(html: str) -> str:
    """Convert HTML string to Markdown.

    Two-pass approach:
    1. Parse HTML into a lightweight DOM tree.
    2. Score nodes using text/link density heuristics,
       prune boilerplate, and serialize to Markdown.

    Args:
        html: Raw HTML string.

    Returns:
        Clean Markdown string.
    """
    content_root = _prepare_content(html)
    _CSSDisplayResolver.resolve(content_root)
    markdown = _MarkdownSerializer().serialize(content_root)
    return _PostProcessor.process(markdown)


def _prepare_content(html: str) -> _Node:
    """Shared pipeline: parse, prune boilerplate, find content root.

    Used by both ``html_to_markdown()`` and ``clean_html()``.
    """
    tree = _TreeBuilder.parse(html)
    pruner = _BoilerplatePruner()
    pruner.prune(tree)
    content_root = _ContentFinder.find(tree)
    pruner.context_sensitive_prune(content_root)
    return content_root
