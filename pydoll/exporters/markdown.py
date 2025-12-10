from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Dict, List, Optional, Set


class HTMLtoMarkdown(HTMLParser):
    """
    HTML to Markdown converter using Python's built-in HTMLParser.

    This class parses HTML content and converts it to Markdown format,
    handling common HTML elements like headings, paragraphs, links,
    images, lists, tables, code blocks, and text formatting.

    The converter is designed to produce clean, readable Markdown output
    suitable for documentation, content extraction, or archival purposes.
    It automatically handles nested elements, maintains proper spacing,
    and can optionally skip navigation elements and images.

    Attributes:
        SKIP_TAGS: HTML tags that are always skipped during conversion
            (script, style, noscript, svg).
        OPTIONAL_SKIP_TAGS: HTML tags that can be optionally skipped
            (nav, aside, header, footer).
        BLOCK_TAGS: HTML tags that represent block-level elements
            and require proper spacing.

    Example:
        Convert HTML to Markdown::

            converter = HTMLtoMarkdown(skip_nav=True)
            markdown = converter.convert('<h1>Title</h1><p>Content</p>')
            # Output: '# Title\n\nContent'

        Skip images in conversion::

            converter = HTMLtoMarkdown(skip_images=True)
            markdown = converter.convert('<p>Text</p><img src="test.png"/>')
            # Output: 'Text'
    """

    SKIP_TAGS: Set[str] = {'script', 'style', 'noscript', 'svg'}

    OPTIONAL_SKIP_TAGS: Set[str] = {'nav', 'aside', 'header', 'footer'}

    BLOCK_TAGS: Set[str] = {
        'p',
        'div',
        'h1',
        'h2',
        'h3',
        'h4',
        'h5',
        'h6',
        'ul',
        'ol',
        'li',
        'blockquote',
        'pre',
        'table',
        'tr',
        'article',
        'section',
    }

    BOLD_TAGS: Set[str] = {'strong', 'b'}
    ITALIC_TAGS: Set[str] = {'em', 'i'}
    TABLE_CELL_TAGS: Set[str] = {'td', 'th'}
    CODE_TAGS: Set[str] = {'code', 'pre'}
    LIST_TAGS: Set[str] = {'ul', 'ol', 'li'}
    LIST_END_TAGS: Set[str] = {'ul', 'ol'}
    TABLE_STRUCTURE_TAGS: Set[str] = {'table', 'tr'}
    SPECIAL_INLINE_TAGS: Set[str] = {'a', 'img', 'blockquote'}
    HEADING_TAG_LENGTH: int = 2

    def __init__(
        self, skip_nav: bool = True, skip_images: bool = False, code_fence: str = '```', **kwargs
    ):
        """
        Initialize the HTML to Markdown converter.

        Args:
            skip_nav: If True, skips navigation-related elements including
                nav, aside, header, and footer tags. This is useful for
                extracting main content without site navigation clutter.
                Defaults to True.
            skip_images: If True, skips all img tags during conversion.
                Useful when only text content is needed. Defaults to False.
            code_fence: The string to use for fenced code blocks.
                Defaults to triple backticks (```).
            **kwargs: Additional keyword arguments (reserved for future use).

        Example:
            Create a converter that includes navigation::

                converter = HTMLtoMarkdown(skip_nav=False)

            Create a converter with custom code fences::

                converter = HTMLtoMarkdown(code_fence='~~~')
        """
        super().__init__()
        self.skip_nav = skip_nav
        self.skip_images = skip_images
        self.code_fence = code_fence

        self.markdown: List[str] = []
        self.skip_depth: int = 0
        self.current_tag_stack: List[str] = []

        self.in_pre: bool = False
        self.in_code: bool = False
        self.list_stack: List[str] = []
        self.list_counters: List[int] = []

        self.bold_depth: int = 0
        self.italic_depth: int = 0

        self.link_buffer: Optional[Dict] = None
        self.table_buffer: Optional[Dict] = None

    def convert(self, html: str) -> str:
        """
        Convert HTML string to Markdown format.

        This is the main entry point for conversion. It parses the provided
        HTML content and returns a clean Markdown string with normalized
        whitespace (no more than two consecutive newlines).

        Args:
            html: The HTML string to convert. Can be a complete HTML document
                or a fragment.

        Returns:
            The converted Markdown string, stripped of leading and trailing
            whitespace with normalized line breaks.

        Example:
            Convert a simple HTML fragment::

                converter = HTMLtoMarkdown()
                result = converter.convert('<p>Hello <strong>world</strong></p>')
                # Returns: 'Hello **world**'

            Convert HTML with multiple elements::

                html = '''
                <h1>Title</h1>
                <p>First paragraph.</p>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
                '''
                result = converter.convert(html)
        """
        self.feed(html)
        result = ''.join(self.markdown)

        result = re.sub(r'\n{3,}', '\n\n', result)
        return result.strip()

    def _is_heading_tag(self, tag: str) -> bool:
        """Check if a tag is a valid heading tag (h1-h6)."""
        return tag.startswith('h') and len(tag) == self.HEADING_TAG_LENGTH and tag[1].isdigit()

    def _handle_heading_start(self, tag: str) -> None:
        """Handle opening heading tags (h1-h6)."""
        level = int(tag[1])
        self._add_block_separator()
        self.markdown.append('#' * level + ' ')

    def _handle_formatting_start(self, tag: str) -> None:
        """Handle opening formatting tags (bold, italic)."""
        if tag in self.BOLD_TAGS:
            self.markdown.append('**')
            self.bold_depth += 1
        elif tag in self.ITALIC_TAGS:
            self.markdown.append('*')
            self.italic_depth += 1

    def _handle_code_start(self, tag: str) -> None:
        """Handle opening code/pre tags."""
        if tag == 'code' and not self.in_pre:
            self.markdown.append('`')
            self.in_code = True
        elif tag == 'pre':
            self._add_block_separator()
            self.markdown.append(f'{self.code_fence}\n')
            self.in_pre = True

    def _handle_simple_block_start(self, tag: str) -> None:
        """Handle simple block tags (p, br)."""
        if tag == 'p':
            self._add_block_separator()
        else:  # br
            self.markdown.append('\n')

    def _handle_special_start(self, tag: str, attrs_dict: Dict[str, str]) -> None:
        """Handle special inline tags (a, img, blockquote)."""
        if tag == 'a':
            href = attrs_dict.get('href', '')
            self.link_buffer = {'href': href, 'text': []}
        elif tag == 'img':
            if not self.skip_images:
                src = attrs_dict.get('src', '')
                alt = attrs_dict.get('alt', '')
                self._add_block_separator()
                self.markdown.append(f'![{alt}]({src})')
        else:  # blockquote
            self._add_block_separator()
            self.markdown.append('> ')

    def _handle_list_start(self, tag: str) -> None:
        """Handle opening list tags (ul, ol, li)."""
        if tag == 'ul':
            self._add_block_separator()
            self.list_stack.append('ul')
        elif tag == 'ol':
            self._add_block_separator()
            self.list_stack.append('ol')
            self.list_counters.append(1)
        elif tag == 'li':
            indent = '  ' * (len(self.list_stack) - 1)
            if self.list_stack and self.list_stack[-1] == 'ul':
                self.markdown.append(f'\n{indent}- ')
            elif self.list_stack and self.list_stack[-1] == 'ol':
                counter = self.list_counters[-1]
                self.markdown.append(f'\n{indent}{counter}. ')
                self.list_counters[-1] += 1

    def _handle_table_start(self, tag: str) -> None:
        """Handle opening table tags."""
        if tag == 'table':
            self.table_buffer = {'rows': [], 'current_row': []}
        elif tag == 'tr' and self.table_buffer:
            self.table_buffer['current_row'] = []
        elif tag in self.TABLE_CELL_TAGS and self.table_buffer:
            self.table_buffer['in_cell'] = True
            self.table_buffer['cell_content'] = []

    def handle_starttag(self, tag: str, attrs: List[tuple]):
        """
        Process an HTML opening tag and convert to Markdown.

        This method is called by the HTMLParser base class when an opening
        tag is encountered. It handles conversion of various HTML elements
        to their Markdown equivalents.

        Supported tags:
            - Headings (h1-h6): Converted to # syntax
            - Paragraphs (p): Add block separation
            - Line breaks (br): Add newline
            - Bold (strong, b): Wrapped in **
            - Italic (em, i): Wrapped in *
            - Code (code): Wrapped in backticks
            - Preformatted (pre): Fenced code blocks
            - Links (a): [text](href) format
            - Images (img): ![alt](src) format
            - Lists (ul, ol, li): - or numbered format
            - Blockquotes: > prefix
            - Tables (table, tr, td, th): Pipe-delimited format

        Args:
            tag: The HTML tag name (lowercase).
            attrs: List of (name, value) tuples for tag attributes.

        Note:
            Tags in SKIP_TAGS are always ignored. Tags in OPTIONAL_SKIP_TAGS
            are ignored based on the skip_nav setting.
        """
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return

        if self.skip_nav and tag in self.OPTIONAL_SKIP_TAGS:
            self.skip_depth += 1
            return

        if self.skip_depth > 0:
            return

        self.current_tag_stack.append(tag)
        attrs_dict = dict(attrs)

        if self._is_heading_tag(tag):
            self._handle_heading_start(tag)
        elif tag in {'p', 'br'}:
            self._handle_simple_block_start(tag)
        elif tag in self.BOLD_TAGS or tag in self.ITALIC_TAGS:
            self._handle_formatting_start(tag)
        elif tag in self.CODE_TAGS:
            self._handle_code_start(tag)
        elif tag in self.SPECIAL_INLINE_TAGS:
            self._handle_special_start(tag, attrs_dict)
        elif tag in self.LIST_TAGS:
            self._handle_list_start(tag)
        elif tag in self.TABLE_STRUCTURE_TAGS or tag in self.TABLE_CELL_TAGS:
            self._handle_table_start(tag)

    def _handle_formatting_end(self, tag: str) -> None:
        """Handle closing formatting tags (bold, italic)."""
        if tag in self.BOLD_TAGS:
            if self.bold_depth > 0:
                self.markdown.append('**')
                self.bold_depth -= 1
        elif tag in self.ITALIC_TAGS:
            if self.italic_depth > 0:
                self.markdown.append('*')
                self.italic_depth -= 1

    def _handle_code_end(self, tag: str) -> None:
        """Handle closing code/pre tags."""
        if tag == 'code' and not self.in_pre:
            self.markdown.append('`')
            self.in_code = False
        elif tag == 'pre':
            self.markdown.append(f'{self.code_fence}\n')
            self.in_pre = False

    def _handle_link_end(self) -> None:
        """Handle closing anchor tag."""
        if self.link_buffer:
            text = ''.join(self.link_buffer['text']).strip()
            href = self.link_buffer['href']
            self.markdown.append(f'[{text}]({href})')
            self.link_buffer = None

    def _handle_list_end(self, tag: str) -> None:
        """Handle closing list tags (ul, ol)."""
        if tag == 'ul':
            if self.list_stack and self.list_stack[-1] == 'ul':
                self.list_stack.pop()
            if not self.list_stack:
                self.markdown.append('\n')
        elif tag == 'ol':
            if self.list_stack and self.list_stack[-1] == 'ol':
                self.list_stack.pop()
                if self.list_counters:
                    self.list_counters.pop()
            if not self.list_stack:
                self.markdown.append('\n')

    def _handle_table_end(self, tag: str) -> None:
        """Handle closing table tags."""
        if tag == 'table' and self.table_buffer:
            self._render_table()
            self.table_buffer = None
        elif tag == 'tr' and self.table_buffer:
            if self.table_buffer.get('current_row'):
                self.table_buffer['rows'].append(self.table_buffer['current_row'])
        elif tag in self.TABLE_CELL_TAGS and self.table_buffer:
            if 'cell_content' in self.table_buffer:
                content = ''.join(self.table_buffer['cell_content']).strip()
                self.table_buffer['current_row'].append(content)
                self.table_buffer['in_cell'] = False

    def handle_endtag(self, tag: str) -> None:
        """
        Process an HTML closing tag and finalize Markdown conversion.

        This method is called by the HTMLParser base class when a closing
        tag is encountered. It handles closing syntax for Markdown elements
        that require it (like bold, italic, links, lists, and tables).

        Args:
            tag: The HTML tag name (lowercase).

        Note:
            Maintains proper nesting for formatting elements and handles
            cleanup of buffers used for complex elements like links and tables.
        """
        if tag in self.SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
            return

        if self.skip_nav and tag in self.OPTIONAL_SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
            return

        if self.skip_depth > 0:
            return

        if self.current_tag_stack and self.current_tag_stack[-1] == tag:
            self.current_tag_stack.pop()

        if self._is_heading_tag(tag):
            self.markdown.append('\n')
        elif tag in self.BOLD_TAGS or tag in self.ITALIC_TAGS:
            self._handle_formatting_end(tag)
        elif tag in self.CODE_TAGS:
            self._handle_code_end(tag)
        elif tag == 'a':
            self._handle_link_end()
        elif tag in self.LIST_END_TAGS:
            self._handle_list_end(tag)
        elif tag in self.TABLE_STRUCTURE_TAGS or tag in self.TABLE_CELL_TAGS:
            self._handle_table_end(tag)

    def handle_data(self, data: str) -> None:
        """
        Process text content within HTML elements.

        This method is called by the HTMLParser base class when text data
        is encountered between tags. It handles proper formatting of text
        content based on the current parsing context.

        Args:
            data: The text content to process.

        Note:
            - Text inside skipped tags is ignored
            - Text inside links is buffered for link construction
            - Text inside table cells is buffered for table rendering
            - Text inside pre blocks preserves whitespace
            - Regular text has whitespace normalized
        """
        if self.skip_depth > 0:
            return

        if self.link_buffer is not None:
            self.link_buffer['text'].append(data)
            return

        if self.table_buffer and self.table_buffer.get('in_cell'):
            self.table_buffer['cell_content'].append(data)
            return

        if self.in_pre:
            self.markdown.append(data)
        else:
            cleaned = re.sub(r'\s+', ' ', data)
            if cleaned:
                self.markdown.append(cleaned)

    def _add_block_separator(self) -> None:
        """
        Add appropriate spacing between block-level elements.

        Ensures proper visual separation in the output Markdown by adding
        newlines when transitioning between block elements. Prevents
        excessive blank lines by checking current output state.
        """
        if self.markdown and not self.markdown[-1].endswith('\n\n'):
            if self.markdown[-1].endswith('\n'):
                self.markdown.append('\n')
            else:
                self.markdown.append('\n\n')

    def _render_table(self) -> None:
        """
        Render buffered table data as Markdown table syntax.

        Converts the accumulated table rows and cells from the table_buffer
        into GitHub Flavored Markdown table syntax with header separator row.
        Handles uneven column counts by padding shorter rows.

        The first row is treated as the header row. Output format::

            | Header 1 | Header 2 |
            |----------|----------|
            | Cell 1   | Cell 2   |

        Note:
            Called automatically when a closing </table> tag is encountered.
            Does nothing if table_buffer is empty or has no rows.
        """

        if not self.table_buffer or not self.table_buffer['rows']:
            return

        rows = self.table_buffer['rows']

        self._add_block_separator()

        max_cols = max(len(row) for row in rows)

        header = rows[0]
        self.markdown.append('| ' + ' | '.join(header) + ' |\n')
        self.markdown.append('|' + '|'.join(['---'] * max_cols) + '|\n')

        for row in rows[1:]:
            padded_row = row + [''] * (max_cols - len(row))
            self.markdown.append('| ' + ' | '.join(padded_row) + ' |\n')

        self.markdown.append('\n')
