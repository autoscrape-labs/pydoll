"""Utility functions for saving page bundles (HTML + assets as .zip)."""

from __future__ import annotations

import base64 as _b64
import posixpath
import re
from urllib.parse import urljoin, urlparse

from pydoll.protocol.network.types import ResourceType
from pydoll.protocol.page.types import FrameResource, FrameResourceTree

_BUNDLEABLE_RESOURCE_TYPES: frozenset[ResourceType] = frozenset({
    ResourceType.DOCUMENT,
    ResourceType.STYLESHEET,
    ResourceType.SCRIPT,
    ResourceType.IMAGE,
    ResourceType.FONT,
    ResourceType.MEDIA,
})

_MIME_TO_EXT: dict[str, str] = {
    'text/css': '.css',
    'text/javascript': '.js',
    'application/javascript': '.js',
    'application/x-javascript': '.js',
    'text/html': '.html',
    'text/plain': '.txt',
    'image/png': '.png',
    'image/jpeg': '.jpg',
    'image/gif': '.gif',
    'image/svg+xml': '.svg',
    'image/webp': '.webp',
    'image/x-icon': '.ico',
    'image/vnd.microsoft.icon': '.ico',
    'font/woff': '.woff',
    'font/woff2': '.woff2',
    'application/font-woff': '.woff',
    'application/font-woff2': '.woff2',
    'font/ttf': '.ttf',
    'font/otf': '.otf',
    'application/x-font-ttf': '.ttf',
    'application/x-font-otf': '.otf',
    'video/mp4': '.mp4',
    'video/webm': '.webm',
    'audio/mpeg': '.mp3',
    'audio/ogg': '.ogg',
    'application/json': '.json',
    'application/xml': '.xml',
    'text/xml': '.xml',
}

_CSS_URL_RE = re.compile(r'url\(\s*(["\']?)(.*?)\1\s*\)', re.IGNORECASE)


def filter_fetchable_resources(
    all_resources: list[tuple[str, FrameResource]],
    page_url: str,
) -> list[tuple[str, FrameResource]]:
    """Filter resources to only those that should be bundled."""
    fetchable: list[tuple[str, FrameResource]] = []
    for fid, res in all_resources:
        if res.get('failed') or res.get('canceled'):
            continue
        url = res['url']
        if url == page_url or url.startswith('data:'):
            continue
        if res['type'] not in _BUNDLEABLE_RESOURCE_TYPES:
            continue
        fetchable.append((fid, res))
    return fetchable


def collect_frame_resources(
    frame_tree: FrameResourceTree,
) -> list[tuple[str, FrameResource]]:
    """Recursively collect all resources from a frame tree."""
    frame_id = frame_tree['frame']['id']
    result: list[tuple[str, FrameResource]] = [
        (frame_id, res) for res in frame_tree.get('resources', [])
    ]
    for child in frame_tree.get('childFrames', []):
        result.extend(collect_frame_resources(child))
    return result


def build_asset_filename(url: str, mime_type: str, index: int) -> str:
    """Build a unique filename from a URL, MIME type, and index."""
    parsed = urlparse(url)
    basename = posixpath.basename(parsed.path) if parsed.path else ''
    if not basename or basename == '/':
        basename = 'resource'
    if '.' not in basename:
        ext = _MIME_TO_EXT.get(mime_type.split(';')[0].strip(), '')
        basename = f'{basename}{ext}'
    return f'{index:04d}_{basename}'


def rewrite_css_urls(
    css_text: str,
    css_url: str,
    asset_map: dict[str, tuple[str, bytes, str, ResourceType]],
) -> str:
    """Rewrite url() references in CSS to point to local asset paths."""

    def _replace(match: re.Match[str]) -> str:
        raw_url = match.group(2)
        if raw_url.startswith('data:'):
            return match.group(0)
        absolute = urljoin(css_url, raw_url)
        entry = asset_map.get(absolute)
        if entry is None:
            return match.group(0)
        filename = entry[0]
        return f'url("{filename}")'

    return _CSS_URL_RE.sub(_replace, css_text)


def inline_css_urls(
    css_text: str,
    css_url: str,
    asset_map: dict[str, tuple[str, bytes, str, ResourceType]],
) -> str:
    """Replace url() references in CSS with data URIs."""

    def _replace(match: re.Match[str]) -> str:
        raw_url = match.group(2)
        if raw_url.startswith('data:'):
            return match.group(0)
        absolute = urljoin(css_url, raw_url)
        entry = asset_map.get(absolute)
        if entry is None:
            return match.group(0)
        _fname, data, mime, _rtype = entry
        b64 = _b64.b64encode(data).decode('ascii')
        return f'url("data:{mime};base64,{b64}")'

    return _CSS_URL_RE.sub(_replace, css_text)


def replace_stylesheet_with_inline(html: str, url: str, css_text: str) -> str:
    """Replace a <link> stylesheet tag with an inline <style> block."""
    escaped = re.escape(url)
    pattern = re.compile(
        rf'<link\b[^>]*href=["\']?{escaped}["\']?[^>]*/?>',
        re.IGNORECASE,
    )
    replacement = f'<style>{css_text}</style>'
    return pattern.sub(lambda _: replacement, html, count=1)


def replace_script_with_inline(html: str, url: str, js_text: str) -> str:
    """Replace a <script src=...> tag with an inline <script> block."""
    escaped = re.escape(url)
    pattern = re.compile(
        rf'<script\b[^>]*src=["\']?{escaped}["\']?[^>]*>\s*</script>',
        re.IGNORECASE,
    )
    safe_js = js_text.replace('</script>', '<\\/script>')
    replacement = f'<script>{safe_js}</script>'
    return pattern.sub(lambda _: replacement, html, count=1)


def rewrite_html_urls(
    html: str,
    asset_map: dict[str, tuple[str, bytes, str, ResourceType]],
) -> str:
    """Rewrite asset URLs in HTML to point to local assets/ directory."""
    for url, (filename, data, mime, rtype) in asset_map.items():
        if rtype == ResourceType.STYLESHEET:
            css_text = data.decode('utf-8', errors='replace')
            rewritten_css = rewrite_css_urls(css_text, url, asset_map)
            asset_map[url] = (filename, rewritten_css.encode('utf-8'), mime, rtype)
        html = html.replace(url, f'assets/{filename}')
    return html


def inline_all_assets(
    html: str,
    asset_map: dict[str, tuple[str, bytes, str, ResourceType]],
) -> str:
    """Embed all assets inline into the HTML."""
    for url, (_, data, mime, rtype) in asset_map.items():
        if rtype == ResourceType.STYLESHEET:
            css_text = data.decode('utf-8', errors='replace')
            css_text = inline_css_urls(css_text, url, asset_map)
            html = replace_stylesheet_with_inline(html, url, css_text)
        elif rtype == ResourceType.SCRIPT:
            js_text = data.decode('utf-8', errors='replace')
            html = replace_script_with_inline(html, url, js_text)
        else:
            b64 = _b64.b64encode(data).decode('ascii')
            data_uri = f'data:{mime};base64,{b64}'
            html = html.replace(url, data_uri)
    return html
