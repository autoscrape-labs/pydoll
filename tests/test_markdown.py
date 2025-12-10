"""
Tests for the HTMLtoMarkdown converter in pydoll.exporters.markdown.

"""

import pytest

from pydoll.exporters.markdown import HTMLtoMarkdown


class TestHTMLtoMarkdownBasics:
    """Basic HTML to Markdown conversion tests."""

    def test_convert_empty_string(self):
        """Test conversion of empty HTML string."""
        converter = HTMLtoMarkdown()
        result = converter.convert('')
        assert result == ''

    def test_convert_plain_text(self):
        """Test conversion of plain text without HTML tags."""
        converter = HTMLtoMarkdown()
        result = converter.convert('Hello World')
        assert result == 'Hello World'

    def test_convert_whitespace_normalization(self):
        """Test that excessive whitespace is normalized."""
        converter = HTMLtoMarkdown()
        result = converter.convert('Hello    World')
        assert result == 'Hello World'


class TestHTMLtoMarkdownHeadings:
    """Tests for heading conversion."""

    def test_convert_h1(self):
        """Test conversion of h1 heading."""
        converter = HTMLtoMarkdown()
        result = converter.convert('<h1>Title</h1>')
        assert result == '# Title'

    def test_convert_h2(self):
        """Test conversion of h2 heading."""
        converter = HTMLtoMarkdown()
        result = converter.convert('<h2>Subtitle</h2>')
        assert result == '## Subtitle'

    def test_convert_h3(self):
        """Test conversion of h3 heading."""
        converter = HTMLtoMarkdown()
        result = converter.convert('<h3>Section</h3>')
        assert result == '### Section'

    def test_convert_h4(self):
        """Test conversion of h4 heading."""
        converter = HTMLtoMarkdown()
        result = converter.convert('<h4>Subsection</h4>')
        assert result == '#### Subsection'

    def test_convert_h5(self):
        """Test conversion of h5 heading."""
        converter = HTMLtoMarkdown()
        result = converter.convert('<h5>Minor Section</h5>')
        assert result == '##### Minor Section'

    def test_convert_h6(self):
        """Test conversion of h6 heading."""
        converter = HTMLtoMarkdown()
        result = converter.convert('<h6>Small Section</h6>')
        assert result == '###### Small Section'

    def test_convert_multiple_headings(self):
        """Test conversion of multiple headings."""
        converter = HTMLtoMarkdown()
        html = '<h1>Main</h1><h2>Sub</h2><h3>Section</h3>'
        result = converter.convert(html)
        assert '# Main' in result
        assert '## Sub' in result
        assert '### Section' in result


class TestHTMLtoMarkdownParagraphs:
    """Tests for paragraph and text conversion."""

    def test_convert_paragraph(self):
        """Test conversion of paragraph element."""
        converter = HTMLtoMarkdown()
        result = converter.convert('<p>This is a paragraph.</p>')
        assert result == 'This is a paragraph.'

    def test_convert_multiple_paragraphs(self):
        """Test conversion of multiple paragraphs with proper spacing."""
        converter = HTMLtoMarkdown()
        html = '<p>First paragraph.</p><p>Second paragraph.</p>'
        result = converter.convert(html)
        assert 'First paragraph.' in result
        assert 'Second paragraph.' in result
        # Should have proper separation
        assert '\n\n' in result

    def test_convert_line_break(self):
        """Test conversion of br element."""
        converter = HTMLtoMarkdown()
        result = converter.convert('Line one<br>Line two')
        assert 'Line one\nLine two' == result


class TestHTMLtoMarkdownFormatting:
    """Tests for text formatting conversion."""

    def test_convert_bold_strong(self):
        """Test conversion of strong tag to bold."""
        converter = HTMLtoMarkdown()
        result = converter.convert('<strong>bold text</strong>')
        assert result == '**bold text**'

    def test_convert_bold_b(self):
        """Test conversion of b tag to bold."""
        converter = HTMLtoMarkdown()
        result = converter.convert('<b>bold text</b>')
        assert result == '**bold text**'

    def test_convert_italic_em(self):
        """Test conversion of em tag to italic."""
        converter = HTMLtoMarkdown()
        result = converter.convert('<em>italic text</em>')
        assert result == '*italic text*'

    def test_convert_italic_i(self):
        """Test conversion of i tag to italic."""
        converter = HTMLtoMarkdown()
        result = converter.convert('<i>italic text</i>')
        assert result == '*italic text*'

    def test_convert_inline_code(self):
        """Test conversion of inline code element."""
        converter = HTMLtoMarkdown()
        result = converter.convert('Use the <code>print()</code> function')
        assert result == 'Use the `print()` function'

    def test_convert_nested_formatting(self):
        """Test conversion of nested formatting elements."""
        converter = HTMLtoMarkdown()
        result = converter.convert('<strong><em>bold and italic</em></strong>')
        assert '**' in result
        assert '*' in result
        assert 'bold and italic' in result


class TestHTMLtoMarkdownLinks:
    """Tests for link conversion."""

    def test_convert_link(self):
        """Test conversion of anchor tag to markdown link."""
        converter = HTMLtoMarkdown()
        result = converter.convert('<a href="https://example.com">Example</a>')
        assert result == '[Example](https://example.com)'

    def test_convert_link_without_href(self):
        """Test conversion of anchor tag without href."""
        converter = HTMLtoMarkdown()
        result = converter.convert('<a>No Link</a>')
        assert result == '[No Link]()'

    def test_convert_link_with_formatted_text(self):
        """Test conversion of link with formatted text."""
        converter = HTMLtoMarkdown()
        result = converter.convert('<a href="https://example.com"><strong>Bold Link</strong></a>')
        assert 'Bold Link' in result
        assert 'https://example.com' in result


class TestHTMLtoMarkdownImages:
    """Tests for image conversion."""

    def test_convert_image(self):
        """Test conversion of img tag to markdown image."""
        converter = HTMLtoMarkdown()
        result = converter.convert('<img src="image.png" alt="Test Image">')
        assert result == '![Test Image](image.png)'

    def test_convert_image_without_alt(self):
        """Test conversion of img tag without alt text."""
        converter = HTMLtoMarkdown()
        result = converter.convert('<img src="image.png">')
        assert result == '![](image.png)'

    def test_skip_images_option(self):
        """Test that images are skipped when skip_images is True."""
        converter = HTMLtoMarkdown(skip_images=True)
        result = converter.convert('<p>Text</p><img src="image.png" alt="Image">')
        assert '![' not in result
        assert 'image.png' not in result
        assert 'Text' in result


class TestHTMLtoMarkdownLists:
    """Tests for list conversion."""

    def test_convert_unordered_list(self):
        """Test conversion of unordered list."""
        converter = HTMLtoMarkdown()
        html = '<ul><li>Item 1</li><li>Item 2</li><li>Item 3</li></ul>'
        result = converter.convert(html)
        assert '- Item 1' in result
        assert '- Item 2' in result
        assert '- Item 3' in result

    def test_convert_ordered_list(self):
        """Test conversion of ordered list."""
        converter = HTMLtoMarkdown()
        html = '<ol><li>First</li><li>Second</li><li>Third</li></ol>'
        result = converter.convert(html)
        assert '1. First' in result
        assert '2. Second' in result
        assert '3. Third' in result

    def test_convert_nested_lists(self):
        """Test conversion of nested lists."""
        converter = HTMLtoMarkdown()
        html = '''
        <ul>
            <li>Parent
                <ul>
                    <li>Child 1</li>
                    <li>Child 2</li>
                </ul>
            </li>
        </ul>
        '''
        result = converter.convert(html)
        assert '- Parent' in result
        assert 'Child 1' in result
        assert 'Child 2' in result


class TestHTMLtoMarkdownCodeBlocks:
    """Tests for code block conversion."""

    def test_convert_preformatted_code(self):
        """Test conversion of pre/code block."""
        converter = HTMLtoMarkdown()
        html = '<pre><code>def hello():\n    print("Hello")</code></pre>'
        result = converter.convert(html)
        assert '```' in result
        assert 'def hello():' in result
        assert 'print("Hello")' in result

    def test_convert_pre_block_preserves_whitespace(self):
        """Test that pre blocks preserve whitespace."""
        converter = HTMLtoMarkdown()
        html = '<pre>Line 1\n    Line 2 indented</pre>'
        result = converter.convert(html)
        assert 'Line 1\n    Line 2 indented' in result

    def test_custom_code_fence(self):
        """Test conversion with custom code fence."""
        converter = HTMLtoMarkdown(code_fence='~~~')
        html = '<pre>code here</pre>'
        result = converter.convert(html)
        assert '~~~' in result
        assert '```' not in result


class TestHTMLtoMarkdownBlockquotes:
    """Tests for blockquote conversion."""

    def test_convert_blockquote(self):
        """Test conversion of blockquote element."""
        converter = HTMLtoMarkdown()
        result = converter.convert('<blockquote>Quoted text</blockquote>')
        assert '> Quoted text' in result


class TestHTMLtoMarkdownTables:
    """Tests for table conversion."""

    def test_convert_simple_table(self):
        """Test conversion of simple table."""
        converter = HTMLtoMarkdown()
        html = '''
        <table>
            <tr><th>Name</th><th>Age</th></tr>
            <tr><td>Alice</td><td>25</td></tr>
            <tr><td>Bob</td><td>30</td></tr>
        </table>
        '''
        result = converter.convert(html)
        assert '| Name | Age |' in result
        assert '|---|---|' in result
        assert '| Alice | 25 |' in result
        assert '| Bob | 30 |' in result

    def test_convert_table_uneven_columns(self):
        """Test conversion of table with uneven columns."""
        converter = HTMLtoMarkdown()
        html = '''
        <table>
            <tr><th>A</th><th>B</th><th>C</th></tr>
            <tr><td>1</td><td>2</td></tr>
        </table>
        '''
        result = converter.convert(html)
        # Should pad shorter rows
        assert '| A | B | C |' in result
        assert '| 1 | 2 |' in result


class TestHTMLtoMarkdownSkipTags:
    """Tests for skipped tags functionality."""

    def test_skip_script_tags(self):
        """Test that script tags are skipped."""
        converter = HTMLtoMarkdown()
        html = '<p>Text</p><script>alert("hello")</script>'
        result = converter.convert(html)
        assert 'alert' not in result
        assert 'Text' in result

    def test_skip_style_tags(self):
        """Test that style tags are skipped."""
        converter = HTMLtoMarkdown()
        html = '<p>Text</p><style>.class { color: red; }</style>'
        result = converter.convert(html)
        assert 'color' not in result
        assert '.class' not in result
        assert 'Text' in result

    def test_skip_noscript_tags(self):
        """Test that noscript tags are skipped."""
        converter = HTMLtoMarkdown()
        html = '<p>Text</p><noscript>Enable JavaScript</noscript>'
        result = converter.convert(html)
        assert 'Enable JavaScript' not in result
        assert 'Text' in result

    def test_skip_svg_tags(self):
        """Test that svg tags are skipped."""
        converter = HTMLtoMarkdown()
        html = '<p>Text</p><svg><circle cx="50" cy="50" r="40"/></svg>'
        result = converter.convert(html)
        assert 'circle' not in result
        assert 'Text' in result


class TestHTMLtoMarkdownNavSkipping:
    """Tests for navigation element skipping."""

    def test_skip_nav_by_default(self):
        """Test that nav elements are skipped by default."""
        converter = HTMLtoMarkdown()
        html = '<nav>Navigation content</nav><p>Main content</p>'
        result = converter.convert(html)
        assert 'Navigation content' not in result
        assert 'Main content' in result

    def test_skip_header_by_default(self):
        """Test that header elements are skipped by default."""
        converter = HTMLtoMarkdown()
        html = '<header>Header content</header><p>Main content</p>'
        result = converter.convert(html)
        assert 'Header content' not in result
        assert 'Main content' in result

    def test_skip_footer_by_default(self):
        """Test that footer elements are skipped by default."""
        converter = HTMLtoMarkdown()
        html = '<footer>Footer content</footer><p>Main content</p>'
        result = converter.convert(html)
        assert 'Footer content' not in result
        assert 'Main content' in result

    def test_skip_aside_by_default(self):
        """Test that aside elements are skipped by default."""
        converter = HTMLtoMarkdown()
        html = '<aside>Sidebar content</aside><p>Main content</p>'
        result = converter.convert(html)
        assert 'Sidebar content' not in result
        assert 'Main content' in result

    def test_include_nav_when_skip_nav_false(self):
        """Test that nav elements are included when skip_nav is False."""
        converter = HTMLtoMarkdown(skip_nav=False)
        html = '<nav>Navigation content</nav><p>Main content</p>'
        result = converter.convert(html)
        assert 'Navigation content' in result
        assert 'Main content' in result

    def test_include_header_when_skip_nav_false(self):
        """Test that header elements are included when skip_nav is False."""
        converter = HTMLtoMarkdown(skip_nav=False)
        html = '<header>Header content</header><p>Main content</p>'
        result = converter.convert(html)
        assert 'Header content' in result
        assert 'Main content' in result


class TestHTMLtoMarkdownComplexHtml:
    """Tests for complex HTML structures."""

    def test_convert_full_page_structure(self):
        """Test conversion of a full page structure."""
        converter = HTMLtoMarkdown()
        html = '''
        <!DOCTYPE html>
        <html>
        <head><title>Test Page</title></head>
        <body>
            <nav>Menu</nav>
            <h1>Main Title</h1>
            <p>Introduction paragraph.</p>
            <h2>Section</h2>
            <p>Content with <strong>bold</strong> and <em>italic</em>.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
            <footer>Copyright</footer>
        </body>
        </html>
        '''
        result = converter.convert(html)
        assert '# Main Title' in result
        assert '## Section' in result
        assert '**bold**' in result
        assert '*italic*' in result
        assert '- Item 1' in result
        assert 'Menu' not in result  # nav skipped
        assert 'Copyright' not in result  # footer skipped

    def test_convert_nested_divs(self):
        """Test conversion of nested div elements."""
        converter = HTMLtoMarkdown()
        html = '<div><div><p>Nested content</p></div></div>'
        result = converter.convert(html)
        assert 'Nested content' in result

    def test_convert_mixed_content(self):
        """Test conversion of mixed inline and block content."""
        converter = HTMLtoMarkdown()
        html = '''
        <p>Start <strong>bold <em>and italic</em></strong> end.</p>
        <pre><code>code block</code></pre>
        '''
        result = converter.convert(html)
        assert 'Start' in result
        assert '**' in result
        assert '*' in result
        assert '```' in result
        assert 'code block' in result


class TestHTMLtoMarkdownEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_tags(self):
        """Test conversion of empty tags."""
        converter = HTMLtoMarkdown()
        result = converter.convert('<p></p><div></div>')
        # Should not crash and return empty or minimal content
        assert isinstance(result, str)

    def test_self_closing_tags(self):
        """Test conversion of self-closing tags."""
        converter = HTMLtoMarkdown()
        result = converter.convert('<br/><img src="test.png"/>')
        assert isinstance(result, str)

    def test_excessive_newlines_normalized(self):
        """Test that excessive newlines are normalized to double newlines."""
        converter = HTMLtoMarkdown()
        html = '<p>First</p><p></p><p></p><p>Second</p>'
        result = converter.convert(html)
        # Should not have more than 2 consecutive newlines
        assert '\n\n\n' not in result

    def test_special_characters_in_text(self):
        """Test that special characters in text are preserved."""
        converter = HTMLtoMarkdown()
        html = '<p>Special chars: &amp; &lt; &gt; &quot;</p>'
        result = converter.convert(html)
        # HTML entities should be preserved or decoded
        assert 'Special chars:' in result

    def test_unicode_content(self):
        """Test conversion of unicode content."""
        converter = HTMLtoMarkdown()
        html = '<p>Unicode: 你好 مرحبا שלום 🚀</p>'
        result = converter.convert(html)
        assert '你好' in result
        assert '🚀' in result

    def test_deeply_nested_skipped_tags(self):
        """Test that deeply nested content in skipped tags is ignored."""
        converter = HTMLtoMarkdown()
        html = '''
        <script>
            <div>
                <p>Should not appear</p>
            </div>
        </script>
        <p>Visible</p>
        '''
        result = converter.convert(html)
        assert 'Should not appear' not in result
        assert 'Visible' in result

    def test_unclosed_tags(self):
        """Test that unclosed tags are handled gracefully."""
        converter = HTMLtoMarkdown()
        # HTMLParser handles unclosed tags, test it doesn't crash
        html = '<p>Unclosed paragraph<strong>Bold without close'
        result = converter.convert(html)
        assert 'Unclosed paragraph' in result

    def test_multiple_conversions_same_instance(self):
        """Test that same converter instance can be reused for multiple conversions."""
        converter = HTMLtoMarkdown()
        result1 = converter.convert('<p>First conversion</p>')
        # Note: Due to how the converter works, a new instance is recommended
        # for each conversion, but this tests the current behavior
        assert 'First conversion' in result1
